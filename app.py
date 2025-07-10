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
    This is the most reliable method.
    """
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(f"Error: The inventory file '{file_path}' was not found.")
        st.info("Please make sure 'rentals.xlsx' is in the same directory as the app script.")
        return pd.DataFrame() # Return empty DataFrame to prevent further errors
    except Exception as e:
        st.error(f"An error occurred while reading the Excel file: {e}")
        return pd.DataFrame()

    # Define the mapping from Excel column names to the names used in the code
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

    # Clean up data: remove whitespace and drop invalid rows
    if 'Mascot_Name' in df.columns:
        df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    
    df.dropna(subset=['ID', 'Mascot_Name'], inplace=True)
    df = df[df['Mascot_Name'] != '']
    
    return df

def load_rental_log(file_path="rental_log.xlsx"):
    try:
        return pd.read_excel(file_path)
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Mascot_Name", "Start_Date", "End_Date"])

# --- Load Data ---
inventory_df = load_inventory_from_excel()
rental_log_df = load_rental_log()

# --- Main App ---
st.title("📅 Baba Jina Mascot Rental Calendar")

# Stop the app if inventory failed to load
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

    # Prepare data for calendar display
    filtered_log = rental_log_df.copy()
    if not filtered_log.empty:
        filtered_log["Start_Date"] = pd.to_datetime(filtered_log["Start_Date"], errors="coerce")
        filtered_log["End_Date"] = pd.to_datetime(filtered_log["End_Date"], errors="coerce")
        if selected_mascot != "All":
            filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]

    month_start = datetime(month_filter.year, month_filter.month, 1)
    last_day = calendar.monthrange(month_filter.year, month_filter.month)[1]
    month_end = datetime(month_filter.year, month_filter.month, last_day)
    date_range = pd.date_range(start=month_start, end=month_end)
    calendar_df = pd.DataFrame({"Date": date_range})

    def get_booking_status(date):
        if not filtered_log.empty:
            booked = filtered_log[(filtered_log["Start_Date"] <= date) & (filtered_log["End_Date"] >= date)]
            if not booked.empty:
                return f"❌ {', '.join(booked['Mascot_Name'].unique())}"
        return "✅ Available"

    calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)
    st.markdown("<hr style='margin-top: 0; margin-bottom: 1rem'>", unsafe_allow_html=True)

    # Display calendar grid
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

    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        start_date = st.date_input("Start Date", value=datetime.today())
        end_date = st.date_input("End Date", value=datetime.today())

        # Get the full row for the selected mascot
        mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]

        # Helper function to format prices robustly
        def format_price(value):
            if pd.isna(value): return 'N/A'
            try:
                # Attempt to convert to float then int to handle "125.0"
                return f"${int(float(value))}"
            except (ValueError, TypeError):
                # If it fails (e.g., text), return the original value as a string
                return str(value)

        st.markdown("### 📋 Mascot Details")
        st.write(f"**Size:** {mascot_row.get('Size', 'N/A')}")
        st.write(f"**Weight:** {mascot_row.get('Weight_kg', 'N/A')} kg")
        st.write(f"**Height:** {mascot_row.get('Height_cm', 'N/A')}")
        st.write(f"**Quantity:** {int(mascot_row.get('Quantity', 0))}")
        st.write(f"**Rent Price:** {format_price(mascot_row.get('Rent_Price'))}")
        st.write(f"**Sale Price:** {format_price(mascot_row.get('Sale_Price'))}")
        st.write(f"**Status:** {mascot_row.get('Status', 'N/A')}")

        if st.form_submit_button("📩 Submit Rental"):
            new_entry_data = {
                "ID": mascot_row["ID"],
                "Mascot_Name": mascot_row["Mascot_Name"],
                "Start_Date": pd.to_datetime(start_date),
                "End_Date": pd.to_datetime(end_date)
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
        # Create a display string for each booking for the selectbox
        rental_log_df['display'] = rental_log_df.apply(
            lambda row: f"{row['Mascot_Name']} ({row.get('Start_Date', pd.NaT).strftime('%Y-%m-%d')} to {row.get('End_Date', pd.NaT).strftime('%Y-%m-%d')})",
            axis=1
        )
        booking_to_delete = st.selectbox("Select booking to delete:", rental_log_df['display'].unique())
        
        if st.button("❌ Delete Booking"):
            # Find the index of the booking to delete
            index_to_delete = rental_log_df[rental_log_df['display'] == booking_to_delete].index
            
            # Drop the temporary display column before saving
            log_to_save = rental_log_df.drop(columns=['display'])
            
            if not index_to_delete.empty:
                log_to_save = log_to_save.drop(index_to_delete)
                log_to_save.to_excel("rental_log.xlsx", index=False)
                st.success("🗑️ Booking deleted successfully.")
                st.rerun()
