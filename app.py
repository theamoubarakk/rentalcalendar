import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# ---- Load inventory from Excel ----
@st.cache_data
def load_inventory():
    return pd.read_excel("cleaned_rentals.xlsx")

# ---- Load rental log from Excel ----
def load_rental_log():
    try:
        return pd.read_excel("rental_log.xlsx")
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Mascot_Name", "Start_Date", "End_Date"])

# ---- Load Data ----
inventory_df = load_inventory()
rental_log_df = load_rental_log()

# ---- App Header ----
st.set_page_config(layout="wide")
st.title("📅 Baba Jina Mascot Rental Calendar")


# ---- Top Filters Row ----
# I've removed the st.container() that was wrapping these columns,
# as it added unnecessary vertical space.
st.markdown("### 🗓️ Monthly Calendar")
col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    selected_mascot = st.selectbox("Filter by Mascot:", ["All"] + sorted(inventory_df["Mascot_Name"].unique()))
with col2:
    month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))


# ---- Prepare rental log ----
filtered_log = rental_log_df.copy()
filtered_log["Start_Date"] = pd.to_datetime(filtered_log["Start_Date"], errors="coerce")
filtered_log["End_Date"] = pd.to_datetime(filtered_log["End_Date"], errors="coerce")

if selected_mascot != "All":
    filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]

# ---- Generate Calendar Grid ----
month_start = datetime(month_filter.year, month_filter.month, 1)
last_day = calendar.monthrange(month_filter.year, month_filter.month)[1]
month_end = datetime(month_filter.year, month_filter.month, last_day)
date_range = pd.date_range(month_start, month_end)

calendar_df = pd.DataFrame({"Date": date_range})

def get_booking_status(date):
    booked = filtered_log[(filtered_log["Start_Date"] <= date) & (filtered_log["End_Date"] >= date)]
    if booked.empty:
        return "✅ Available"
    else:
        # If there are multiple mascots booked, show them.
        names = ", ".join(booked["Mascot_Name"].unique())
        return f"❌ {names}"

calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)


# ---- CSS to reduce vertical whitespace ----
# This CSS is more precise. It targets the container that holds your two main columns
# (the calendar and the form) and moves the entire block up to reduce the gap.
st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-of-type(2):last-of-type) {
        margin-top: -100px !important;
    }
    </style>
""", unsafe_allow_html=True)


# ---- Layout: Calendar Grid + Rental Form ----
left, right = st.columns([3, 2], gap="small")

with right:
    # ---- New Rental Entry Form ----
    st.markdown("### 📌 New Rental Entry")

    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        start_date = st.date_input("Start Date", value=datetime.today())
        end_date = st.date_input("End Date", value=datetime.today())

        # Check if mascot exists before trying to access it
        if not inventory_df[inventory_df["Mascot_Name"] == mascot_choice].empty:
            mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]

            weight_display = "N/A" if pd.isna(mascot_row["Weight_kg"]) else f"{mascot_row['Weight_kg']} kg"
            height_display = "N/A" if pd.isna(mascot_row["Height_cm"]) else f"{mascot_row['Height_cm']} cm"

            st.markdown("### 📋 Mascot Details")
            st.write(f"Size: {mascot_row['Size']}")
            st.write(f"Weight: {weight_display}")
            st.write(f"Height: {height_display}")
            st.write(f"Quantity Available: {mascot_row['Quantity']}")
            st.write(f"Rent Price: ${mascot_row['Rent_Price']}")
            st.write(f"Sale Price: ${mascot_row['Sale_Price']}")
            st.write(f"Status: {mascot_row['Status']}")
        
        submitted = st.form_submit_button("📩 Submit Rental")

        if submitted:
            mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
            new_entry = pd.DataFrame([{
                "ID": mascot_row["ID"],
                "Mascot_Name": mascot_row["Mascot_Name"],
                "Start_Date": pd.to_datetime(start_date),
                "End_Date": pd.to_datetime(end_date)
            }])
            rental_log_df = pd.concat([rental_log_df, new_entry], ignore_index=True)
            rental_log_df.to_excel("rental_log.xlsx", index=False)
            st.success("✅ Rental submitted and logged!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🗑️ Delete Rental Booking")

    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        # Create unique identifiers for each booking to handle multiple bookings for the same mascot
        rental_log_df['booking_id'] = rental_log_df.apply(
            lambda row: f"{row['Mascot_Name']} ({row['Start_Date'].strftime('%Y-%m-%d')} to {row['End_Date'].strftime('%Y-%m-%d')})",
            axis=1
        )
        
        booking_to_delete = st.selectbox(
            "Select booking to delete:", 
            rental_log_df['booking_id'].unique()
        )

        if st.button("❌ Delete Booking"):
            # Find the index of the booking to delete
            idx_to_delete = rental_log_df[
                rental_log_df['booking_id'] == booking_to_delete
            ].index
            
            # Drop the helper column before saving
            rental_log_df = rental_log_df.drop(columns=['booking_id'])
            
            if not idx_to_delete.empty:
                rental_log_df = rental_log_df.drop(idx_to_delete)
                rental_log_df.to_excel("rental_log.xlsx", index=False)
                st.success("🗑️ Booking deleted successfully.")
                st.rerun()

with left:

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, day in enumerate(days):
        header_cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)

    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("") # Keep the column structure
                else:
                    date = datetime(month_filter.year, month_filter.month, day)
                    status = calendar_df.loc[calendar_df["Date"] == date, "Status"].iloc[0]
                    is_booked = "❌" in status
                    
                    bg_color = "#f9e5e5" if is_booked else "#e6ffea"
                    icon, text = status.split(" ", 1)
                    
                    st.markdown(f"""
                        <div style='
                            background-color:{bg_color};
                            border: 1px solid #ddd;
                            border-radius:10px;
                            padding:10px;
                            text-align:center;
                            box-shadow:0 1px 3px rgba(0,0,0,0.05);
                            margin-bottom:8px;
                            min-height:80px;
                            display: flex;
                            flex-direction: column;
                            justify-content: flex-start;'>
                            <strong style='margin-bottom: 5px;'>{day}</strong>
                            <div style='font-size: 0.9em;'>{icon} {text}</div>
                        </div>
                    """, unsafe_allow_html=True)
