import streamlit as st
import pandas as pd
import sqlite3
import calendar
from datetime import datetime
from pandas.errors import EmptyDataError

# ---- Page config ----
st.set_page_config(layout="wide", page_title="Baba Jina Mascot Rental Calendar")

# ---- Inventory loader (Excel) ----
@st.cache_data
def load_inventory_from_excel(file_path="cleaned_rentals.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except (FileNotFoundError, EmptyDataError):
        st.error(f"Could not load inventory from '{file_path}'.")
        return pd.DataFrame()
    # rename your columns to codes
    df = df.rename(columns={
        "Mascot Name": "Mascot_Name",
        "Kg": "Weight_kg",
        "cm": "Height_cm",
        "pcs": "Quantity",
        "Rent Price": "Rent_Price",
        "Sale Price": "Sale_Price",
        "Status (Available, Rented, Reserved, Under Repair)": "Status"
    })
    df["Mascot_Name"] = df["Mascot_Name"].astype(str).str.strip()
    df = df.dropna(subset=["ID", "Mascot_Name"])
    return df

# ---- SQLite setup ----
DB_FILE = "rental_log.db"

def init_db(db_file=DB_FILE):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascot_id INTEGER,
            mascot_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@st.cache_data
def load_rental_log(db_file=DB_FILE):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM rentals", conn, parse_dates=["start_date","end_date"])
    conn.close()
    return df

# ---- Initialize DB & load data ----
init_db()
inventory_df  = load_inventory_from_excel()
rental_log_df = load_rental_log()

# stop if no inventory
if inventory_df.empty:
    st.stop()

# ---- Main layout ----
st.title("📅 Baba Jina Mascot Rental Calendar")
left_col, right_col = st.columns([3,2], gap="large")

# ------------------- LEFT: Calendar -------------------
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    # filters
    fc1, fc2 = st.columns(2)
    with fc1:
        mascots = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascots)
    with fc2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    # prepare filtered log
    fl = rental_log_df.copy()
    if selected_mascot != "All":
        fl = fl[fl["mascot_name"] == selected_mascot]

    # calendar date range
    y, m = month_filter.year, month_filter.month
    first_of_month = datetime(y,m,1)
    last_day = calendar.monthrange(y,m)[1]
    last_of_month = datetime(y,m,last_day)
    dates = pd.date_range(first_of_month, last_of_month)

    cal_df = pd.DataFrame({"Date": dates})
    def booking_status(d):
        bk = fl[(fl["start_date"] <= d) & (fl["end_date"] >= d)]
        return (f"❌ {', '.join(bk['mascot_name'].unique())}" if not bk.empty 
                else "✅ Available")
    cal_df["Status"] = cal_df["Date"].apply(booking_status)

    # render headings
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdr_cols = st.columns(7)
    for i,day in enumerate(days):
        hdr_cols[i].markdown(f"**{day}**", unsafe_allow_html=True)

    # render each week
    for week in calendar.monthcalendar(y,m):
        row_cols = st.columns(7)
        for i,day in enumerate(week):
            cell = row_cols[i]
            if day == 0:
                cell.markdown("&nbsp;")
            else:
                d = datetime(y,m,day)
                status = cal_df.loc[cal_df["Date"]==d, "Status"].iat[0]
                booked = status.startswith("❌")
                bg = "#ffe6e6" if booked else "#e6ffea"
                icon, *txt = status.split(" ",1)
                detail = txt[0] if txt else "Available"
                cell.markdown(
                    f"""
                    <div style="
                        background:{bg};
                        border-radius:8px;
                        padding:6px;
                        text-align:center;
                        box-shadow:0 1px 2px rgba(0,0,0,0.1);
                        min-height:70px;
                        ">
                      <strong>{day}</strong><br>
                      {icon} {detail}
                    </div>
                    """, unsafe_allow_html=True
                )

# ------------------- RIGHT: Manage Bookings -------------------
with right_col:
    # -- New Rental Entry --
    st.markdown("### 📌 New Rental Entry")
    with st.form("rental_form"):
        mascot_choice  = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        customer_name  = st.text_input("Customer Name:")
        customer_phone = st.text_input("Customer Phone:")
        start_date     = st.date_input("Start Date", value=datetime.today())
        end_date       = st.date_input("End Date",   value=datetime.today())

        # show details
        row = inventory_df[inventory_df["Mascot_Name"]==mascot_choice].iloc[0]
        def fmt(v,unit=""): return (f"{v}{unit}" if pd.notna(v) else "N/A")
        st.markdown("#### 📋 Mascot Details")
        st.write(f"• Size: {fmt(row.get('Size',''), '')}")
        st.write(f"• Weight: {fmt(row.get('Weight_kg',None), ' kg')}")
        st.write(f"• Height: {fmt(row.get('Height_cm',None), ' cm')}")
        st.write(f"• Qty: {fmt(row.get('Quantity',None), '')}")
        st.write(f"• Rent: {fmt(row.get('Rent_Price',None), '')}")
        st.write(f"• Sale: {fmt(row.get('Sale_Price',None), '')}")
        st.write(f"• Status: {row.get('Status','N/A')}")

        if st.form_submit_button("📩 Submit Rental"):
            if not customer_name or not customer_phone:
                st.warning("Please provide both customer name and phone.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO rentals
                      (mascot_id, mascot_name, customer_name, customer_phone, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,(
                    int(row["ID"]), row["Mascot_Name"],
                    customer_name, customer_phone,
                    start_date, end_date
                ))
                conn.commit()
                conn.close()
                st.success("✅ Rental saved!")
                st.experimental_rerun()

    st.markdown("---")

    # -- Delete Booking --
    st.markdown("### 🗑️ Delete Rental Booking")
    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        # build display → id map
        choices = {}
        for _,r in rental_log_df.iterrows():
            disp = (f"{r['customer_name']} | {r['customer_phone']} | "
                    f"{r['mascot_name']} ({r['start_date'].date()}→{r['end_date'].date()})")
            choices[disp] = r["id"]
        sel = st.selectbox("Pick a booking to delete:", choices.keys())
        if st.button("❌ Delete Booking"):
            bid = choices[sel]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM rentals WHERE id=?", (bid,))
            conn.commit()
            conn.close()
            st.success("🗑️ Deleted.")
            st.experimental_rerun()

    st.markdown("---")

    # -- Download Report --
    st.markdown("### 📥 Download Report (CSV)")
    # slice same filters
    df = rental_log_df.copy()
    if selected_mascot!="All":
        df = df[df["mascot_name"]==selected_mascot]
    df = df[(df["start_date"]<=last_of_month) & (df["end_date"]>=first_of_month)]
    if df.empty:
        st.info("No bookings found for this month.")
    else:
        report = df[[
            "id","mascot_name","customer_name","customer_phone","start_date","end_date"
        ]].rename(columns={
            "id":"BookingID","mascot_name":"Mascot",
            "customer_name":"Customer","customer_phone":"Phone",
            "start_date":"Start","end_date":"End"
        })
        csv = report.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            csv,
            file_name=f"rentals_{month_filter:%Y_%m}.csv",
            mime="text/csv"
        )
