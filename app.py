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
st.title("\U0001F4C5 Baba Jina Mascot Rental Calendar")

# ---- Top Filters Row ----
st.markdown("### \U0001F5D3\ufe0f Monthly Grid View")
with st.container():
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
        return "❌ Booked: " + ", ".join(booked["Mascot_Name"].unique())

calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)

# ---- Layout: Calendar Grid + Rental Form ----
left, right = st.columns([3, 2], gap="small")

with left:
    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("** **")
            else:
                date = datetime(month_filter.year, month_filter.month, day)
                status = calendar_df[calendar_df["Date"] == date]["Status"].values[0]
                is_today = date.date() == datetime.today().date()
                bold = "**" if is_today else ""
                cols[i].markdown(f"{bold}{calendar.day_name[i]} {day}{bold}\n{status}")

with right:
    with st.container():
        st.markdown("### \U0001F4CC New Rental Entry")

        with st.form("rental_form"):
            mascot_choice = st.selectbox("Select a mascot:", inventory_df["Mascot_Name"].unique())
            start_date = st.date_input("Start Date", value=datetime.today())
            end_date = st.date_input("End Date", value=datetime.today())

            mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]

            # Handle NA for weight and height
            weight_display = "N/A" if pd.isna(mascot_row["Weight_kg"]) else f"{mascot_row['Weight_kg']} kg"
            height_display = "N/A" if pd.isna(mascot_row["Height_cm"]) else f"{mascot_row['Height_cm']} cm"

            st.markdown("### \U0001F4CB Mascot Details")
            st.write(f"**Size:** {mascot_row['Size']}")
            st.write(f"**Weight:** {weight_display}")
            st.write(f"**Height:** {height_display}")
            st.write(f"**Quantity Available:** {mascot_row['Quantity']}")
            st.write(f"**Rent Price:** ${mascot_row['Rent_Price']}")
            st.write(f"**Sale Price:** ${mascot_row['Sale_Price']}")
            st.write(f"**Status:** {mascot_row['Status']}")

            submitted = st.form_submit_button("\U0001F4E9 Submit Rental")

            if submitted:
                new_entry = pd.DataFrame([{
                    "ID": mascot_row["ID"],
                    "Mascot_Name": mascot_row["Mascot_Name"],
                    "Start_Date": pd.to_datetime(start_date),
                    "End_Date": pd.to_datetime(end_date)
                }])
                rental_log_df = pd.concat([rental_log_df, new_entry], ignore_index=True)
                rental_log_df.to_excel("rental_log.xlsx", index=False)
                st.success("\u2705 Rental submitted and logged!")
                st.rerun()

    # ---- Delete Booking ----
    st.markdown("---")
    st.markdown("### \U0001F5D1\ufe0f Delete Rental Booking")

    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        delete_mascot = st.selectbox("Select a mascot to delete:", rental_log_df["Mascot_Name"].unique())
        matching = rental_log_df[rental_log_df["Mascot_Name"] == delete_mascot]

        delete_dates = matching.apply(lambda row: f"{row['Start_Date'].date()} to {row['End_Date'].date()}", axis=1)
        selected_range = st.selectbox("Select booking to delete:", delete_dates)

        if st.button("❌ Delete Booking"):
            idx_to_delete = matching[
                delete_dates == selected_range
            ].index

            if not idx_to_delete.empty:
                rental_log_df = rental_log_df.drop(idx_to_delete)
                rental_log_df.to_excel("rental_log.xlsx", index=False)
                st.success("🗑️ Booking deleted successfully.")
                st.rerun()
