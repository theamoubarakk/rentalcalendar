import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import sqlite3

# ---- Load inventory from Excel ----
@st.cache_data
def load_inventory_from_excel(file_path="cleaned_rentals.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(f"Error: The inventory file '{file_path}' was not found.")
        return pd.DataFrame()
    col_map = {
        'Mascot Name': 'Mascot_Name',
        'Kg': 'Weight_kg',
        'cm': 'Height_cm',
        'pcs': 'Quantity',
        'Rent Price': 'Rent_Price',
        'Sale Price': 'Sale_Price',
        'Status (Available, Rented, Reserved, Under Repair)': 'Status'
    }
    df.rename(columns=col_map, inplace=True)
    df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    df.dropna(subset=['ID','Mascot_Name'], inplace=True)
    return df

# ---- Init / Upgrade SQLite DB ----
def init_db(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    # Create table if missing, including customer_phone
    c.execute("""
    CREATE TABLE IF NOT EXISTS rentals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mascot_id INTEGER,
        mascot_name TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# ---- Load rental log from SQLite ----
@st.cache_data
def load_rental_log(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM rentals", conn, parse_dates=['start_date','end_date'])
    conn.close()
    return df

# ---- App startup ----
st.set_page_config(layout="wide")
init_db()
inventory_df  = load_inventory_from_excel()
rental_log_df = load_rental_log()

# ---- Header & filters ----
st.title("📅 Baba Jina Mascot Rental Calendar")
left_col, right_col = st.columns([3,2], gap="large")

with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    fc1, fc2 = st.columns(2)
    with fc1:
        mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
    with fc2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    # filter rentals
    fl = rental_log_df.copy()
    if selected_mascot != "All":
        fl = fl[fl["mascot_name"] == selected_mascot]
    # only those that intersect this month
    start_month = datetime(month_filter.year, month_filter.month, 1)
    end_month   = datetime(month_filter.year, month_filter.month,
                          calendar.monthrange(month_filter.year, month_filter.month)[1])
    fl = fl[(fl["start_date"] <= end_month) & (fl["end_date"] >= start_month)]

    # build calendar
    dr = pd.date_range(start_month, end_month)
    cal = pd.DataFrame({"Date": dr})
    def status_for(d):
        row = fl[(fl["start_date"]<=d)&(fl["end_date"]>=d)]
        return ("❌ " + ", ".join(row["mascot_name"].unique())) if not row.empty else "✅ Available"
    cal["Status"] = cal["Date"].apply(status_for)

    # render header
    st.markdown("<hr style='margin:0.5rem 0'>", unsafe_allow_html=True)
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdr = st.columns(7)
    for i,day in enumerate(days):
        hdr[i].markdown(f"**{day}**", unsafe_allow_html=True)

    # render weeks
    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i,daynum in enumerate(week):
            if daynum:
                date = datetime(month_filter.year, month_filter.month, daynum)
                stcol = cols[i]
                stcol.markdown(f"""
                    <div style='background-color:{"#ffe6e6" if "❌" in cal.loc[cal.Date==date,"Status"].iloc[0] else "#e6ffea"};
                                 border-radius:8px;padding:8px;text-align:center;min-height:60px;'>
                        <strong>{daynum}</strong><br>
                        {cal.loc[cal.Date==date,"Status"].iloc[0].replace("✅ ","✅ ")}
                    </div>
                """, unsafe_allow_html=True)
            else:
                cols[i].markdown("&nbsp;")

    # ---- Download Report ----
    st.markdown("---")
    st.markdown("#### 📥 Download Report")
    report_df = fl[["id","mascot_name","customer_name","customer_phone","start_date","end_date"]].copy()
    report_df.rename(columns={
        "mascot_name":"Mascot",
        "customer_name":"Customer",
        "customer_phone":"Phone",
        "start_date":"Start",
        "end_date":"End"
    }, inplace=True)
    csv = report_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        data=csv,
        file_name=f"rentals_{month_filter:%Y_%m}.csv",
        mime="text/csv"
    )

with right_col:
    st.markdown("### 📌 New Rental Entry")
    with st.form("rental_form"):
        m_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        cust_name = st.text_input("Customer Name:")
        cust_phone= st.text_input("Customer Phone:")
        sd = st.date_input("Start Date", value=datetime.today())
        ed = st.date_input("End Date",   value=datetime.today())

        # display details
        row = inventory_df[inventory_df["Mascot_Name"]==m_choice].iloc[0]
        st.markdown("**Mascot Details**")
        st.write(f"- Size: {row['Size']}")
        st.write(f"- Weight: {row['Weight_kg']} kg")
        st.write(f"- Height: {row['Height_cm'] if pd.notna(row['Height_cm']) else 'N/A'} cm")
        st.write(f"- Quantity: {int(row['Quantity'])}")
        st.write(f"- Rent Price: ${int(row['Rent_Price'])}")
        st.write(f"- Sale Price: ${int(row['Sale_Price'])}")
        st.write(f"- Status: {row['Status']}")

        if st.form_submit_button("📩 Submit Rental"):
            if not cust_name or not cust_phone:
                st.warning("Please enter both customer name and phone.")
            else:
                conn = sqlite3.connect("rental_log.db")
                c = conn.cursor()
                c.execute("""
                    INSERT INTO rentals
                      (mascot_id, mascot_name, customer_name, customer_phone, start_date, end_date)
                    VALUES (?,?,?,?,?,?)
                """, (int(row["ID"]), m_choice, cust_name, cust_phone, sd, ed))
                conn.commit()
                conn.close()
                st.success("✅ Rental submitted!")
                st.experimental_rerun()

    st.markdown("---")
    st.markdown("### 🗑️ Delete Rental Booking")
    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        # build display map
        disp_map = {
            f"{r['customer_name']} ({r['customer_phone']}) — {r['mascot_name']} {r['start_date'].date()}→{r['end_date'].date()}"
            : int(r["id"])
            for _,r in rental_log_df.iterrows()
        }
        sel = st.selectbox("Select booking to delete:", list(disp_map.keys()))
        if st.button("❌ Delete Booking"):
            conn = sqlite3.connect("rental_log.db")
            c = conn.cursor()
            c.execute("DELETE FROM rentals WHERE id=?", (disp_map[sel],))
            conn.commit()
            conn.close()
            st.success("🗑️ Booking deleted.")
            st.experimental_rerun()
