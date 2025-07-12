import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import sqlite3

# --- Configuration and Core Functions ---
st.set_page_config(layout="wide")

@st.cache_data
def load_inventory_from_excel(file_path="cleaned_rentals.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(f"Error: The inventory file '{file_path}' was not found.")
        st.info("Please make sure the inventory file is in the same directory as the app script.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred while reading the Excel file: {e}")
        return pd.DataFrame()

    column_mapping = {
        'Mascot Name': 'Mascot_Name',
        'Kg': 'Weight_kg',
        'cm': 'Height_cm',
        'pcs': 'Quantity',
        'Rent Price': 'Rent_Price',
        'Sale Price': 'Sale_Price',
        'Status (Available, Rented, Reserved, Under Repair)': 'Status'
    }
    df.rename(columns=column_mapping, inplace=True)
    if 'Mascot_Name' in df.columns:
        df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    df.dropna(subset=['ID', 'Mascot_Name'], inplace=True)
    return df[df['Mascot_Name'] != '']

def init_db(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascot_id INTEGER,
            mascot_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            contact_phone TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def load_rental_log(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM rentals", conn)
    conn.close()
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date']   = pd.to_datetime(df['end_date'])
    return df

def check_availability(log_df, mascot_name, start_dt, end_dt):
    if log_df.empty:
        return 0
    bookings = log_df[log_df['mascot_name'] == mascot_name]
    conflicts = bookings[
        (bookings['start_date'] <= end_dt) &
        (bookings['end_date'] >= start_dt)
    ]
    return len(conflicts)

# --- Initialize ---
init_db()
inventory_df  = load_inventory_from_excel()
rental_log_df = load_rental_log()

st.title("📅 Baba Jina Mascot Rental Calendar")
if inventory_df.empty:
    st.stop()

# --- Columns ---
left_col, right_col = st.columns([3,2], gap="large")

# ==============================================================================
# LEFT COLUMN: Full Calendar, Delete & Download REMOVED
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    fc1, fc2 = st.columns(2)
    with fc1:
        mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
    with fc2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    filtered = rental_log_df.copy()
    if selected_mascot != "All":
        filtered = filtered[filtered["mascot_name"] == selected_mascot]

    start = datetime(month_filter.year, month_filter.month, 1)
    last = calendar.monthrange(month_filter.year, month_filter.month)[1]
    end   = datetime(month_filter.year, month_filter.month, last)
    dates = pd.date_range(start=start, end=end)
    cal_df = pd.DataFrame({"Date": dates})

    def booking_status(d):
        b = filtered[(filtered["start_date"] <= d) & (filtered["end_date"] >= d)]
        if b.empty:
            return ("✅ Available", "Available")
        names = ", ".join(b["mascot_name"].unique())
        return (f"❌ {names}", "\n".join(
            f"{r['mascot_name']}: {r['customer_name']} ({r['contact_phone']})"
            for _, r in b.iterrows()
        ))

    cal_df["Tuple"] = cal_df["Date"].apply(booking_status)

    st.markdown("<hr>", unsafe_allow_html=True)
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdr = st.columns(7)
    for i, d in enumerate(days):
        hdr[i].markdown(f"**{d}**", unsafe_allow_html=True)

    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day==0: continue
            d = datetime(month_filter.year, month_filter.month, day)
            text, tip = cal_df.loc[cal_df["Date"]==d, "Tuple"].iloc[0]
            color = "#e6ffea" if "✅" in text else "#f9e5e5"
            icon, *_ = text.split(" ",1)
            cols[i].markdown(f"""
                <div title="{tip}" style="
                    background:{color};
                    border-radius:8px;
                    padding:8px;
                    text-align:center;
                    min-height:70px;
                    margin-bottom:4px;">
                  <strong>{day}</strong><br>{icon}
                </div>""", unsafe_allow_html=True)

# ==============================================================================
# RIGHT COLUMN: Form, Errors, Details, Delete+Download
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    # Mascot selector
    choice = st.selectbox("Select a mascot:",
                         sorted(inventory_df["Mascot_Name"].unique()))

    # Booking form
    with st.form("rent_form"):
        c1, c2 = st.columns(2)
        with c1:
            cust = st.text_input("Customer Name:")
        with c2:
            phone = st.text_input("Contact Phone Number:")

        s1, s2 = st.columns(2)
        with s1:
            sd = st.date_input("Start Date", value=datetime.today())
        with s2:
            ed = st.date_input("End Date",   value=datetime.today())

        go = st.form_submit_button("📩 Submit Rental")

    # Show errors/success immediately below button
    if go:
        if not cust:
            st.warning("Please enter a customer name.")
        elif ed < sd:
            st.warning("End date cannot be before start date.")
        else:
            row = inventory_df.loc[inventory_df["Mascot_Name"]==choice].iloc[0]
            start_dt = datetime.combine(sd, datetime.min.time())
            end_dt   = datetime.combine(ed, datetime.min.time())
            tot = int(row["Quantity"])
            used = check_availability(rental_log_df, choice, start_dt, end_dt)
            if used >= tot:
                st.error(f"Booking Failed: All {tot} units of '{choice}' are booked.")
            else:
                conn = sqlite3.connect("rental_log.db")
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO rentals (mascot_id,mascot_name,customer_name,contact_phone,start_date,end_date) VALUES (?,?,?,?,?,?)",
                    (int(row["ID"]), choice, cust, phone, sd, ed)
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Rental submitted! ({used+1} of {tot} booked)")
                st.experimental_rerun()

    # Mascot details
    info = inventory_df.loc[inventory_df["Mascot_Name"]==choice].iloc[0]
    def fmt(v):
        if pd.isna(v): return "N/A"
        try: return f"${int(float(v))}"
        except: return str(v)

    s = info["Size"]      if pd.notna(info["Size"])      else "N/A"
    w = f"{info['Weight_kg']} kg" if pd.notna(info["Weight_kg"]) else "N/A"
    h = info["Height_cm"] if pd.notna(info["Height_cm"]) else "N/A"
    q = int(info["Quantity"]) if pd.notna(info["Quantity"]) else "N/A"
    rp= fmt(info["Rent_Price"])
    sp= fmt(info["Sale_Price"])
    stt= info["Status"]  if pd.notna(info["Status"])  else "N/A"

    st.markdown("### 📋 Mascot Details")
    d1, d2 = st.columns(2)
    with d1:
        st.write(f"*Size:* {s}")
        st.write(f"*Weight:* {w}")
        st.write(f"*Height:* {h}")
    with d2:
        st.write(f"*Quantity:* {q}")
        st.write(f"*Rent Price:* {rp}")
        st.write(f"*Sale Price:* {sp}")
    st.write(f"*Status:* {stt}")

    # Delete & download
    st.markdown("---")
    dc, dl = st.columns(2)
    with dc:
        st.markdown("### 🗑️ Delete Rental Booking")
        if rental_log_df.empty:
            st.info("No bookings to delete.")
        else:
            opts = {
                f"{r['customer_name']} – {r['mascot_name']} ({r['start_date'].date()} to {r['end_date'].date()})": r["id"]
                for _, r in rental_log_df.iterrows()
            }
            sel = st.selectbox("Select booking to delete:", opts.keys())
            if st.button("❌ Delete Booking"):
                conn = sqlite3.connect("rental_log.db")
                cur  = conn.cursor()
                cur.execute("DELETE FROM rentals WHERE id = ?", (opts[sel],))
                conn.commit()
                conn.close()
                st.success("🗑️ Booking deleted successfully.")
                st.experimental_rerun()
    with dl:
        st.markdown("### 📥 Download Rental Log")
        if not rental_log_df.empty:
            csv = rental_log_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Log as CSV",
                data=csv,
                file_name=f"rental_log_{datetime.today().date()}.csv",
                mime="text/csv"
            )
        else:
            st.info("No rental log data to download.")
