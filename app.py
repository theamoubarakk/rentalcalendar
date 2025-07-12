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
# LEFT COLUMN: Calendar, Delete, and Download Sections
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
    with filter_col2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))
    
    filtered_log = rental_log_df.copy()
    if not filtered_log.empty and selected_mascot != "All":
        filtered_log = filtered_log[filtered_log["mascot_name"] == selected_mascot]

    month_start = datetime(month_filter.year, month_filter.month, 1)
    last_day = calendar.monthrange(month_filter.year, month_filter.month)[1]
    month_end = datetime(month_filter.year, month_filter.month, last_day)
    date_range = pd.date_range(start=month_start, end=month_end)
    calendar_df = pd.DataFrame({"Date": date_range})

    # --- CORRECTED: This function now sanitizes the tooltip data ---
    def get_booking_status(date):
        booked = filtered_log[(filtered_log["start_date"] <= date) & (filtered_log["end_date"] >= date)]
        
        if booked.empty:
            return ("✅ Available", "This day is available for booking.")
        else:
            display_text = f"❌ {', '.join(booked['mascot_name'].unique())}"
            
            tooltip_parts = []
            for _, row in booked.iterrows():
                # Sanitize each piece of data by replacing double quotes
                mascot = str(row['mascot_name']).replace('"', '"')
                customer = str(row.get('customer_name', 'N/A')).replace('"', '"')
                phone = str(row.get('contact_phone', 'N/A')).replace('"', '"')
                
                tooltip_parts.append(f"{mascot}: {customer} ({phone})")
            
            # Use a proper newline join instead of a literal line break
            tooltip_text = "\n".join(tooltip_parts)
            
            return (display_text, tooltip_text)

    calendar_df["StatusTuple"] = calendar_df["Date"].apply(get_booking_status)
    st.markdown("<hr style='margin-top: 0; margin-bottom: 1rem'>", unsafe_allow_html=True)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, day_name in enumerate(days):
        header_cols[i].markdown(f"<div style='text-align:center;font-weight:bold;'>{day_name}</div>", unsafe_allow_html=True)
    
    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            if day_num != 0:
                date = datetime(month_filter.year, month_filter.month, day_num)
                status_text, tooltip_info = calendar_df.loc[calendar_df["Date"] == date, "StatusTuple"].iloc[0]
                
                bg_color = "#f9e5e5" if "❌" in status_text else "#e6ffea"
                icon, *text = status_text.split(" ", 1)
                
                cols[i].markdown(f"""
                    <div title="{tooltip_info}" style='background-color:{bg_color};border-radius:10px;padding:10px;text-align:center;
                                box-shadow:0 1px 3px rgba(0,0,0,0.05);margin-bottom:8px;min-height:80px;'>
                        <strong>{day_num}</strong><br><div style='font-size:0.9em;word-wrap:break-word;'>{icon} {text[0] if text else ''}</div>
                    </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    delete_col, download_col = st.columns(2)

    with delete_col:
        st.markdown("### 🗑️ Delete Rental Booking")
        if rental_log_df.empty:
            st.info("No bookings to delete.")
        else:
            display_to_id_map = {}
            for index, row in rental_log_df.iterrows():
                display_str = f"{row.get('customer_name', 'N/A')} - {row['mascot_name']} ({pd.to_datetime(row.get('start_date')).strftime('%Y-%m-%d')} to {pd.to_datetime(row.get('end_date')).strftime('%Y-%m-%d')})"
                display_to_id_map[display_str] = row['id']
            
            booking_to_delete_display = st.selectbox("Select booking to delete:", list(display_to_id_map.keys()), key="delete_selectbox")
            
            if st.button("❌ Delete Booking"):
                booking_id_to_delete = display_to_id_map[booking_to_delete_display]
                conn = sqlite3.connect("rental_log.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM rentals WHERE id = ?", (booking_id_to_delete,))
                conn.commit()
                conn.close()
                st.success("🗑️ Booking deleted successfully.")
                st.rerun()

    with download_col:
        st.markdown("### 📥 Download Rental Log")
        if not rental_log_df.empty:
            csv = rental_log_df.to_csv(index=False).encode('utf-8')
            st.download_button(
               label="Download Log as CSV",
               data=csv,
               file_name=f"rental_log_{datetime.now().strftime('%Y-%m-%d')}.csv",
               mime='text/csv',
            )
        else:
            st.info("No rental log data to download.")


# ==============================================================================
# RIGHT COLUMN: New Entry Form Only
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        customer_name = st.text_input("Customer Name:")
        contact_phone = st.text_input("Contact Phone Number:")
        start_date_input = st.date_input("Start Date", value=datetime.today())
        end_date_input = st.date_input("End Date", value=datetime.today())

        mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
        def format_price(value):
            if pd.isna(value): return 'N/A'
            try: return f"${int(float(value))}"
            except (ValueError, TypeError): return str(value)
        size_display = mascot_row.get('Size', 'N/A') if pd.notna(mascot_row.get('Size')) else 'N/A'
        weight_display = f"{mascot_row.get('Weight_kg')} kg" if pd.notna(mascot_row.get('Weight_kg')) else 'N/A'
        height_display = mascot_row.get('Height_cm', 'N/A') if pd.notna(mascot_row.get('Height_cm')) else 'N/A'
        quantity_display = int(mascot_row.get('Quantity', 0)) if pd.notna(mascot_row.get('Quantity')) else 'N/A'
        status_display = mascot_row.get('Status', 'N/A') if pd.notna(mascot_row.get('Status')) else 'N/A'
        st.markdown("### 📋 Mascot Details")
        st.write(f"*Size:* {size_display}")
        st.write(f"*Weight:* {weight_display}")
        st.write(f"*Height:* {height_display}")
        st.write(f"*Quantity:* {quantity_display}")
        st.write(f"*Rent Price:* {format_price(mascot_row.get('Rent_Price'))}")
        st.write(f"*Sale Price:* {format_price(mascot_row.get('Sale_Price'))}")
        st.write(f"*Status:* {status_display}")

        if st.form_submit_button("📩 Submit Rental"):
            if not customer_name:
                st.warning("Please enter a customer name.")
            elif end_date_input < start_date_input:
                st.warning("End date cannot be before start date.")
            else:
                start_date_dt = datetime.combine(start_date_input, datetime.min.time())
                end_date_dt = datetime.combine(end_date_input, datetime.min.time())
                total_quantity = int(mascot_row.get('Quantity', 0))
                booked_count = check_availability(rental_log_df, mascot_choice, start_date_dt, end_date_dt)

                if booked_count >= total_quantity:
                    st.error(f"⚠️ Booking Failed: All {total_quantity} units of '{mascot_choice}' are already booked for this period.")
                else:
                    conn = sqlite3.connect("rental_log.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO rentals (mascot_id, mascot_name, customer_name, contact_phone, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?)",
                        (int(mascot_row["ID"]), mascot_choice, customer_name, contact_phone, start_date_input, end_date_input)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Rental submitted! ({booked_count + 1} of {total_quantity} booked)")
                    st.rerun()
