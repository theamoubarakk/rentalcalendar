import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# --- Configuration and Data Loading ---
st.set_page_config(layout="wide")

@st.cache_data
def load_inventory():
    try:
        return pd.read_excel("cleaned_rentals.xlsx")
    except FileNotFoundError:
        st.error("Error: 'cleaned_rentals.xlsx' not found. Please add the inventory file.")
        return pd.DataFrame()

def load_rental_log():
    try:
        return pd.read_excel("rental_log.xlsx")
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Mascot_Name", "Start_Date", "End_Date"])

inventory_df = load_inventory()
rental_log_df = load_rental_log()

# --- Main App ---
st.title("📅 Baba Jina Mascot Rental Calendar")

# Exit early if inventory is not loaded to prevent errors
if inventory_df.empty:
    st.warning("Cannot display calendar because inventory is missing.")
    st.stop()

# Create the two main columns for the entire layout below the title.
left_col, right_col = st.columns([3, 2], gap="large")


# ==============================================================================
# LEFT COLUMN: Contains all calendar-related elements
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")

    # --- Filters (now inside the left column) ---
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
    with filter_col2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    # --- Data Preparation (based on filter selection) ---
    filtered_log = rental_log_df.copy()
    filtered_log["Start_Date"] = pd.to_datetime(filtered_log["Start_Date"], errors="coerce")
    filtered_log["End_Date"] = pd.to_datetime(filtered_log["End_Date"], errors="coerce")

    if selected_mascot != "All":
        filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]

    month_start = datetime(month_filter.year, month_filter.month, 1)
    last_day_of_month = calendar.monthrange(month_filter.year, month_filter.month)[1]
    month_end = datetime(month_filter.year, month_filter.month, last_day_of_month)
    date_range = pd.date_range(month_start, month_end)
    calendar_df = pd.DataFrame({"Date": date_range})

    def get_booking_status(date):
        booked = filtered_log[(filtered_log["Start_Date"] <= date) & (filtered_log["End_Date"] >= date)]
        if booked.empty:
            return "✅ Available"
        else:
            names = ", ".join(booked["Mascot_Name"].unique())
            return f"❌ {names}"

    calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)
    
    st.markdown("<hr style='margin-top: 0; margin-bottom: 1rem'>", unsafe_allow_html=True)

    # --- Calendar Grid Display ---
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, day_name in enumerate(days_of_week):
        header_cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{day_name}</div>", unsafe_allow_html=True)

    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            with cols[i]:
                if day_num == 0:
                    st.markdown("")  # Keep column structure
                else:
                    date_obj = datetime(month_filter.year, month_filter.month, day_num)
                    status = calendar_df.loc[calendar_df["Date"] == date_obj, "Status"].iloc[0]
                    is_booked = "❌" in status
                    bg_color = "#f9e5e5" if is_booked else "#e6ffea"
                    icon, text = status.split(" ", 1)

                    st.markdown(f"""
                        <div style='background-color:{bg_color}; border-radius:10px; padding:10px; text-align:center;
                                    box-shadow:0 1px 3px rgba(0,0,0,0.05); margin-bottom:8px; min-height:80px;'>
                            <strong>{day_num}</strong><br>
                            <div style='font-size: 0.9em;'>{icon} {text}</div>
                        </div>
                    """, unsafe_allow_html=True)

# ==============================================================================
# RIGHT COLUMN: Contains all form-related elements
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        start_date = st.date_input("Start Date", value=datetime.today())
        end_date = st.date_input("End Date", value=datetime.today())

        if not inventory_df[inventory_df["Mascot_Name"] == mascot_choice].empty:
            mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
            st.markdown("---")
            st.markdown("##### 📋 Mascot Details")
            st.write(f"**Size:** {mascot_row.get('Size', 'N/A')}")
            st.write(f"**Weight:** {mascot_row.get('Weight_kg', 'N/A')} kg")
            st.write(f"**Height:** {mascot_row.get('Height_cm', 'N/A')} cm")
            # You can add more details here if needed
        
        submitted = st.form_submit_button("📩 Submit Rental")

        if submitted:
            # Re-fetch the row to be sure
            mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
            new_entry = pd.DataFrame([{
                "ID": mascot_row["ID"],
                "Mascot_Name": mascot_row["Mascot_Name"],
                "Start_Date": pd.to_datetime(start_date),
                "End_Date": pd.to_datetime(end_date)
            }])
            updated_log = pd.concat([rental_log_df, new_entry], ignore_index=True)
            updated_log.to_excel("rental_log.xlsx", index=False)
            st.success("✅ Rental submitted and logged!")
            st.rerun()

    # The delete section can also go here
    # st.markdown("---")
    # st.markdown("### 🗑️ Delete Rental Booking")
    # ... (Your delete booking code)
