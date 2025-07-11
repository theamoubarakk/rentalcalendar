import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# --- Configuration and Core Functions ---
st.set_page_config(layout="wide")

@st.cache_data
def load_inventory_from_excel(file_path="cleaned_rentals.xlsx"):
    """
    Loads and cleans data directly from the specified Excel file.
    """
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

def load_rental_log(file_path="rental_log.xlsx"):
    """
    Loads the rental log. If it doesn't exist, creates an empty DataFrame.
    """
    try:
        df = pd.read_excel(file_path)
        df['Start_Date'] = pd.to_datetime(df['Start_Date'])
        df['End_Date'] = pd.to_datetime(df['End_Date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Mascot_Name", "Customer_Name", "Start_Date", "End_Date"])

# --- Load Data ---
inventory_df = load_inventory_from_excel()
rental_log_df = load_rental_log()

# --- Main App ---
st.title("📅 Baba Jina Mascot Rental Calendar")

if inventory_df.empty:
    st.stop()

# --- Layout Definition ---
left_col, right_col = st.columns([3, 2], gap="large")

# ==============================================================================
# LEFT COLUMN: Calendar View and Controls
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
    with filter_col2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    display_log = rental_log_df.copy()
    if selected_mascot != "All":
        display_log = display_log[display_log["Mascot_Name"] == selected_mascot]

    month_start = datetime(month_filter.year, month_filter.month, 1)
    last_day = calendar.monthrange(month_filter.year, month_filter.month)[1]
    month_end = datetime(month_filter.year, month_filter.month, last_day)
    date_range = pd.date_range(start=month_start, end=month_end)
    calendar_df = pd.DataFrame({"Date": date_range})

    def get_booking_status(date):
        if not display_log.empty:
            booked = display_log[(display_log["Start_Date"] <= date) & (display_log["End_Date"] >= date)]
            if not booked.empty:
                return f"❌ {', '.join(booked['Mascot_Name'].unique())}"
        return "✅ Available"

    calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)
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
                status = calendar_df.loc[calendar_df["Date"] == date, "Status"].iloc[0]
                bg_color = "#f9e5e5" if "❌" in status else "#e6ffea"
                icon, *text = status.split(" ", 1)
                cols[i].markdown(f"""
                    <div style='background-color:{bg_color};border-radius:10px;padding:10px;text-align:center;
                                box-shadow:0 1px 3px rgba(0,0,0,0.05);margin-bottom:8px;min-height:80px;'>
                        <strong>{day_num}</strong><br><div style='font-size:0.9em;word-wrap:break-word;'>{icon} {text[0] if text else ''}</div>
                    </div>""", unsafe_allow_html=True)

# ==============================================================================
# RIGHT COLUMN: New Entry and Deletion Forms
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    # --- ADJUSTMENT 1: Widgets for dynamic updates are OUTSIDE the form ---
    mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
    
    # --- ADJUSTMENT 2: Customer name is now before the dates ---
    customer_name = st.text_input("Customer Name:")
    
    start_date = st.date_input("Start Date", value=datetime.today())
    end_date = st.date_input("End Date", value=datetime.today())

    # --- DYNAMIC STATUS LOGIC ---
    mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
    general_status = mascot_row.get('Status', 'N/A')
    quantity = int(mascot_row.get('Quantity', 0))
    dynamic_status_display = general_status

    if general_status == 'Available':
        start_date_dt = datetime.combine(start_date, datetime.min.time())
        end_date_dt = datetime.combine(end_date, datetime.min.time())
        conflicting_bookings = rental_log_df[
            (rental_log_df['Mascot_Name'] == mascot_choice) &
            (rental_log_df['Start_Date'] <= end_date_dt) &
            (rental_log_df['End_Date'] >= start_date_dt)
        ]
        num_booked = len(conflicting_bookings)
        if num_booked >= quantity:
            dynamic_status_display = "Booked for selected dates"
        else:
            available_count = quantity - num_booked
            dynamic_status_display = f"Available ({available_count} of {quantity} left)"

    # --- FORM FOR SUBMISSION (now only contains the button and displays info) ---
    with st.form("rental_form_submit"):
        st.markdown("### 📋 Mascot Details")

        # --- ADJUSTMENT 3: Robust "N/A" formatting for all details ---
        size_display = mascot_row.get('Size') if pd.notna(mascot_row.get('Size')) else 'N/A'
        weight_display = f"{mascot_row.get('Weight_kg')} kg" if pd.notna(mascot_row.get('Weight_kg')) else 'N/A'
        height_display = mascot_row.get('Height_cm') if pd.notna(mascot_row.get('Height_cm')) else 'N/A'
        quantity_display = int(mascot_row.get('Quantity')) if pd.notna(mascot_row.get('Quantity')) else 'N/A'
        
        def format_price(value):
            if pd.isna(value): return 'N/A'
            try: return f"${int(float(value))}"
            except (ValueError, TypeError): return str(value)
        
        st.write(f"**Size:** {size_display}")
        st.write(f"**Weight:** {weight_display}")
        st.write(f"**Height:** {height_display}")
        st.write(f"**Quantity:** {quantity_display}")
        st.write(f"**Rent Price:** {format_price(mascot_row.get('Rent_Price'))}")
        st.write(f"**Sale Price:** {format_price(mascot_row.get('Sale_Price'))}")
        st.write(f"**Status:** {dynamic_status_display}")

        if st.form_submit_button("📩 Submit Rental"):
            if not customer_name:
                st.warning("Please enter a customer name.")
            elif "Booked" in str(dynamic_status_display):
                st.error("This mascot is fully booked for the selected dates. Please choose different dates.")
            else:
                new_entry_data = {
                    "ID": mascot_row["ID"], "Mascot_Name": mascot_choice,
                    "Customer_Name": customer_name,
                    "Start_Date": start_date_dt, "End_Date": end_date_dt
                }
                new_entry_df = pd.DataFrame([new_entry_data])
                updated_log_df = pd.concat([rental_log_df, new_entry_df], ignore_index=True)
                updated_log_df.to_excel("rental_log.xlsx", index=False)
                st.success("✅ Rental submitted and logged!")
                st.rerun()

    # --- Delete Booking Section ---
    st.markdown("---")
    st.markdown("### 🗑️ Delete Rental Booking")
    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        rental_log_df['display'] = rental_log_df.apply(
            lambda row: f"{row.get('Customer_Name', 'N/A')} - {row['Mascot_Name']} ({row.get('Start_Date', pd.NaT).strftime('%Y-%m-%d')} to {row.get('End_Date', pd.NaT).strftime('%Y-%m-%d')})",
            axis=1
        )
        booking_to_delete = st.selectbox("Select booking to delete:", sorted(rental_log_df['display'].unique()), key="delete_booking_select")
        
        if st.button("❌ Delete Booking"):
            index_to_delete = rental_log_df[rental_log_df['display'] == booking_to_delete].index
            log_to_save = rental_log_df.drop(columns=['display'])
            if not index_to_delete.empty:
                log_to_save = log_to_save.drop(index_to_delete)
                log_to_save.to_excel("rental_log.xlsx", index=False)
                st.success("🗑️ Booking deleted successfully.")
                st.rerun()
