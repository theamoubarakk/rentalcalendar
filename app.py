import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import sqlite3

# ─────────── remove white-space ───────────
st.markdown(
    """
    <style>
      /* remove the big top and bottom padding from every page block */
      .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
      }
      /* collapse the extra margin under headers, forms, etc */
      .css-1avcm0n, /* hr container */
      .css-18e3th9 { /* main gap container */
        margin-bottom: 0.25rem !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)
# ─────────────────────────────────────────────

# --- Streamlit page config ---
st.set_page_config(layout="wide")

# --- Header: logo on the left, title on the right ---
hdr_logo, hdr_title = st.columns([1, 9], gap="small")
with hdr_logo:
    st.image("logo.png", width=150)
with hdr_title:
    st.markdown("### 📅 Baba Jina Mascot Rental Calendar")

# --- Load data and initialize ---
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

    df.rename(columns={
        'Mascot Name': 'Mascot_Name',
        'Kg': 'Weight_kg',
        'cm': 'Height_cm',
        'pcs': 'Quantity',
        'Rent Price': 'Rent_Price',
        'Sale Price': 'Sale_Price',
        'Status (Available, Rented, Reserved, Under Repair)': 'Status'
    }, inplace=True)
    if 'Mascot_Name' in df.columns:
        df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    df.dropna(subset=['ID','Mascot_Name'], inplace=True)
    df = df[df['Mascot_Name'] != '']
    return df

def init_db(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascot_id INTEGER,
            mascot_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            contact_phone TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        )
        """
    )
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
        (bookings['end_date']   >= start_dt)
    ]
    return len(conflicts)

# --- Initialize ---
init_db()
inventory_df  = load_inventory_from_excel()
rental_log_df = load_rental_log()
if inventory_df.empty:
    st.stop()

# --- Main layout ---
left_col, right_col = st.columns([3, 2], gap="large")

# --- LEFT: Calendar ---
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    c1, c2 = st.columns(2)
    with c1:
        mlist = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mlist)
    with c2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    filtered = rental_log_df.copy()
    if selected_mascot != "All":
        filtered = filtered[filtered["mascot_name"] == selected_mascot]

    ms = datetime(month_filter.year, month_filter.month, 1)
    ld = calendar.monthrange(month_filter.year, month_filter.month)[1]
    me = datetime(month_filter.year, month_filter.month, ld)
    dr = pd.date_range(start=ms, end=me)
    cal_df = pd.DataFrame({"Date": dr})

    def get_status(d):
        b = filtered[(filtered['start_date'] <= d) & (filtered['end_date'] >= d)]
        if b.empty:
            return ("✅","This day is available for booking.")
        txt = f"❌ {', '.join(b['mascot_name'].unique())}"
        tips = [f"{r.mascot_name}: {r.customer_name} ({r.contact_phone})" for _,r in b.iterrows()]
        return (txt, "\n".join(tips))

    cal_df['St'] = cal_df['Date'].apply(get_status)
    st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdr = st.columns(7)
    for i,d in enumerate(days): hdr[i].markdown(f"**{d}**", unsafe_allow_html=True)

    for w in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i,day in enumerate(w):
            if day:
                d = datetime(month_filter.year, month_filter.month, day)
                txt, tip = cal_df.loc[cal_df['Date']==d,'St'].iloc[0]
                bg = '#f9e5e5' if txt.startswith('❌') else '#e6ffea'
                icon, *_ = txt.split(' ',1)
                cols[i].markdown(
                    f"<div title='{tip}' style='background:{bg};padding:8px;border-radius:8px;text-align:center;min-height:70px;'>"
                    f"<strong>{day}</strong><br>{icon}" +
                    "</div>", unsafe_allow_html=True)

# --- RIGHT: Form, feedback, details, delete/download ---
with right_col:
    st.markdown("### 📌 New Rental Entry")
    mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
    with st.form("frm"):
        cna, cph = st.columns(2)
        with cna: cn = st.text_input("Customer Name:")
        with cph: ph = st.text_input("Contact Phone Number:")
        cds, cde = st.columns(2)
        with cds: sd = st.date_input("Start Date", value=datetime.today())
        with cde: ed = st.date_input("End Date",   value=datetime.today())
        sub = st.form_submit_button("📩 Submit Rental")
    if sub:
        if not cn:
            st.warning("Please enter a customer name.")
        elif ed < sd:
            st.warning("End date cannot be before start date.")
        else:
            sdt = datetime.combine(sd, datetime.min.time())
            edt = datetime.combine(ed, datetime.min.time())
            row = inventory_df.query("Mascot_Name==@mascot_choice").iloc[0]
            total = int(row.Quantity)
            used  = check_availability(rental_log_df, mascot_choice, sdt, edt)
            if used >= total:
                st.error(f"⚠️ Booking Failed: All {total} units of '{mascot_choice}' are booked.")
            else:
                c = sqlite3.connect("rental_log.db").cursor()
                c.execute(
                    "INSERT INTO rentals (mascot_id,mascot_name,customer_name,contact_phone,start_date,end_date) VALUES (?,?,?,?,?,?)",
                    (int(row.ID), mascot_choice, cn, ph, sd, ed)
                ); c.connection.commit()
                st.success(f"✅ Rental submitted! ({used+1}/{total})")
                st.experimental_rerun()
    # details
    md = inventory_df.query("Mascot_Name==@mascot_choice").iloc[0]
    st.markdown("### 📋 Mascot Details")
    d1, d2 = st.columns(2)
    with d1:
        st.write(f"*Size:* {md.get('Size','N/A')}")
        st.write(f"*Weight:* {md.Weight_kg or 'N/A'} kg")
        st.write(f"*Height:* {md.Height_cm or 'N/A'}")
    with d2:
        st.write(f"*Quantity:* {int(md.Quantity)}")
        st.write(f"*Rent Price:* ${md.Rent_Price}")
        st.write(f"*Sale Price:* ${md.Sale_Price}")
    # delete/download
    st.markdown("---")
    dc, dl = st.columns(2)
    with dc:
        st.markdown("### 🗑️ Delete Rental Booking")
        if rental_log_df.empty:
            st.info("No bookings to delete.")
        else:
            m = {f"{r.customer_name} - {r.mascot_name} ({r.start_date.date()} to {r.end_date.date()})":r.id for _,r in rental_log_df.iterrows()}
            sel = st.selectbox("Select booking to delete:", list(m))
            if st.button("❌ Delete Booking"):
                c=sqlite3.connect("rental_log.db").cursor()
                c.execute("DELETE FROM rentals WHERE id=?",(m[sel],)); c.connection.commit()
                st.success("🗑️ Booking deleted.")
                st.experimental_rerun()
    with dl:
        st.markdown("### 📥 Download Rental Log")
        if not rental_log_df.empty:
            csv = rental_log_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Log as CSV", data=csv, file_name=f"rental_log_{datetime.today().date()}.csv")
            
