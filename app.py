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
        'Mascot Name': 'Mascot_Name', 'Kg': 'Weight_kg', 'cm': 'Height_cm',
        'pcs': 'Quantity', 'Rent Price': 'Rent_Price', 'Sale Price': 'Sale_Price',
        'Status (Available, Rented, Reserved, Under Repair)': 'Status'
    }
    df.rename(columns=column_mapping, inplace=True)
    if 'Mascot_Name' in df.columns:
        df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    df.dropna(subset=['ID', 'Mascot_Name'], inplace=True)
    df = df[df['Mascot_Name'] != '']
    return df

def init_db(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mascot_id INTEGER, mascot_name TEXT NOT NULL,
            customer_name TEXT NOT NULL, contact_phone TEXT, 
            start_date DATE NOT NULL, end_date DATE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def load_rental_log(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM rentals", conn)
    conn.close()
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    return df

def check_availability(log_df, mascot_name, start_date_req, end_date_req):
    if log_df.empty:
        return 0
    mascot_bookings = log_df[log_df['mascot_name'] == mascot_name].copy()
    conflicting_bookings = mascot_bookings[
        (mascot_bookings['start_date'] <= end_date_req) & 
        (mascot_bookings['end_date'] >= start_date_req)
    ]
    return len(conflicting_bookings)

# --- Initialize Database and Load Data ---
init_db()
inventory_df = load_inventory_from_excel()
rental_log_df = load_rental_log()

# --- Main App ---
st.title("📅 Baba Jina Mascot Rental Calendar")

if inventory_df.empty:
    st.stop()

# --- Layout Definition ---
left_col, right_col = st.columns([3, 2], gap="large")

# ==============================================================================
# LEFT COLUMN: Calendar, Delete, Download
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
    with filter_col2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    # apply filter
    filtered_log = rental_log_df.copy()
    if selected_mascot != "All" and not filtered_log.empty:
        filtered_log = filtered_log[filtered_log["mascot_name"] == selected_mascot]

    # build a date range for the month
    month_start = datetime(month_filter.year, month_filter.month, 1)
    last_day = calendar.monthrange(month_filter.year, month_filter.month)[1]
    month_end = datetime(month_filter.year, month_filter.month, last_day)
    date_range = pd.date_range(start=month_start, end=month_end)
    calendar_df = pd.DataFrame({"Date": date_range})

    # --- only changed here: properly escape quotes + join with "\n" ---
    def get_booking_status(date):
        booked = filtered_log[
            (filtered_log["start_date"] <= date) & 
            (filtered_log["end_date"] >= date)
        ]
        if booked.empty:
            return ("✅ Available", "This day is available for booking.")
        tooltip_parts = []
        for _, row in booked.iterrows():
            mascot = str(row["mascot_name"]).replace('"', '\\"')
            customer = str(row.get("customer_name", "N/A")).replace('"', '\\"')
            phone = str(row.get("contact_phone", "N/A")).replace('"', '\\"')
            tooltip_parts.append(f"{mascot}: {customer} ({phone})")
        tooltip_text = "\n".join(tooltip_parts)        # ← newline join
        display_text = f"❌ {', '.join(booked['mascot_name'].unique())}"
        return (display_text, tooltip_text)

    calendar_df["StatusTuple"] = calendar_df["Date"].apply(get_booking_status)

    # draw weekday headers
    st.markdown("<hr style='margin-top:0;margin-bottom:1rem'>", unsafe_allow_html=True)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, d in enumerate(days):
        header_cols[i].markdown(
            f"<div style='text-align:center;font-weight:bold;'>{d}</div>", 
            unsafe_allow_html=True
        )

    # render each week
    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            if day_num == 0:
                continue
            this_date = datetime(month_filter.year, month_filter.month, day_num)
            status_text, tooltip = calendar_df.loc[
                calendar_df["Date"] == this_date, "StatusTuple"
            ].iloc[0]
            bg_color = "#f9e5e5" if status_text.startswith("❌") else "#e6ffea"
            icon, *rest = status_text.split(" ", 1)
            cols[i].markdown(
                f"""
                <div title="{tooltip}"
                     style="
                       background-color:{bg_color};
                       border-radius:10px;
                       padding:10px;
                       text-align:center;
                       box-shadow:0 1px 3px rgba(0,0,0,0.05);
                       margin-bottom:8px;
                       min-height:80px;
                     ">
                  <strong>{day_num}</strong><br>
                  <div style="font-size:0.9em;word-wrap:break-word;">
                    {icon} {rest[0] if rest else ''}
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")

    # --- your DELETE logic unchanged ---
    delete_col, download_col = st.columns(2)
    with delete_col:
        st.markdown("### 🗑️ Delete Rental Booking")
        if rental_log_df.empty:
            st.info("No bookings to delete.")
        else:
            display_to_id_map = {
                f"{row.customer_name} - {row.mascot_name} ({row.start_date.date()} to {row.end_date.date()})": row.id
                for _, row in rental_log_df.iterrows()
            }
            sel = st.selectbox("Select booking to delete:", list(display_to_id_map.keys()))
            if st.button("❌ Delete Booking"):
                conn = sqlite3.connect("rental_log.db")
                cur = conn.cursor()
                cur.execute("DELETE FROM rentals WHERE id = ?", (display_to_id_map[sel],))
                conn.commit()
                conn.close()
                st.success("Booking deleted.")
                st.rerun()

    # --- your DOWNLOAD logic unchanged ---
    with download_col:
        st.markdown("### 📥 Download Rental Log")
        if not rental_log_df.empty:
            csv = rental_log_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Log as CSV",
                data=csv,
                file_name=f"rental_log_{datetime.now().date()}.csv",
                mime="text/csv",
            )
        else:
            st.info("No rental log data to download.")

# ==============================================================================
# RIGHT COLUMN: New Entry Form ONLY (unchanged)
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")
    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"]))
        customer_name = st.text_input("Customer Name:")
        contact_phone = st.text_input("Contact Phone Number:")
        start_date_input = st.date_input("Start Date", value=datetime.today())
        end_date_input = st.date_input("End Date", value=datetime.today())

        mascot_row = inventory_df.query("Mascot_Name == @mascot_choice").iloc[0]

        def format_price(v):
            if pd.isna(v): return "N/A"
            try: return f"${int(float(v))}"
            except: return str(v)

        st.write(f"**Size:** {mascot_row.get('Size','N/A')}")
        st.write(f"**Weight:** {mascot_row.get('Weight_kg','N/A')} kg")
        st.write(f"**Height:** {mascot_row.get('Height_cm','N/A')} cm")
        st.write(f"**Quantity:** {int(mascot_row.get('Quantity',0))}")
        st.write(f"**Rent Price:** {format_price(mascot_row.get('Rent_Price'))}")
        st.write(f"**Sale Price:** {format_price(mascot_row.get('Sale_Price'))}")
        st.write(f"**Status:** {mascot_row.get('Status','N/A')}")

        if st.form_submit_button("📩 Submit Rental"):
            # … keep your existing validation & INSERT logic here …
            pass
