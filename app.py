import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar

# ---- Load inventory from Excel ----
@st.cache_data
def load_inventory():
    return pd.read_excel("cleaned_rentals.xlsx")

# ---- Load rental log from Excel or create new one ----
@st.cache_data
def load_rental_log():
    try:
        return pd.read_excel("rental_log.xlsx")
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Mascot_Name", "Start_Date", "End_Date"])

# ---- Load Data ----
inventory_df = load_inventory()
rental_log_df = load_rental_log()

# ---- Sidebar Filters ----
st.sidebar.header("\U0001F4CA Filters")
selected_mascot = st.sidebar.selectbox("Select Mascot", ["All"] + sorted(inventory_df["Mascot_Name"].unique()))
start_filter = st.sidebar.date_input("Start Date Filter", value=datetime.today())
end_filter = st.sidebar.date_input("End Date Filter", value=datetime.today())

# ---- Convert filters to datetime ----
start_filter = pd.to_datetime(start_filter)
end_filter = pd.to_datetime(end_filter)

# ---- Main Header ----
st.title("\U0001F4C5 Baba Jina Mascot Rental Calendar")
st.markdown("### \U0001F5D3️ Booking Calendar Overview")

# ---- Prepare rental log ----
filtered_log = rental_log_df.copy()
filtered_log["Start_Date"] = pd.to_datetime(filtered_log["Start_Date"], errors="coerce")
filtered_log["End_Date"] = pd.to_datetime(filtered_log["End_Date"], errors="coerce")

# ---- Apply filters ----
if selected_mascot != "All":
    filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]

filtered_log = filtered_log[
    (filtered_log["Start_Date"] <= end_filter) &
    (filtered_log["End_Date"] >= start_filter)
]

# ---- Calendar Grid View ----
st.markdown("### \\U0001F4C6 Monthly Grid View")

# Generate calendar grid for the selected month
month_start = datetime(start_filter.year, start_filter.month, 1)
last_day = calendar.monthrange(start_filter.year, start_filter.month)[1]
month_end = datetime(start_filter.year, start_filter.month, last_day)
date_range = pd.date_range(month_start, month_end)

# Build calendar matrix
calendar_df = pd.DataFrame({"Date": date_range})
calendar_df["Day"] = calendar_df["Date"].dt.day_name()

# Create booking map
def get_booking_status(date):
    booked = filtered_log[(filtered_log["Start_Date"] <= date) & (filtered_log["End_Date"] >= date)]
    if booked.empty:
        return "✅ Available"
    else:
        return "❌ Booked: " + ", ".join(booked["Mascot_Name"].unique())

calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)

# Display grid view
for week in calendar.monthcalendar(start_filter.year, start_filter.month):
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown("** **")
        else:
            date = datetime(start_filter.year, start_filter.month, day)
            status = calendar_df[calendar_df["Date"] == date]["Status"].values[0]
            cols[i].markdown(f"**{calendar.day_name[i]} {day}**\n{status}")

# ---- Booking Form ----
st.markdown("### \U0001F4CC New Rental Entry")

with st.form("rental_form"):
    mascot_choice = st.selectbox("Select a mascot:", inventory_df["Mascot_Name"].unique())
    start_date = st.date_input("Start Date", value=datetime.today())
    end_date = st.date_input("End Date", value=datetime.today())

    mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]

    st.markdown("### \U0001F4CB Mascot Details")
    st.write(f"**Size:** {mascot_row['Size']}")
    st.write(f"**Weight:** {mascot_row['Weight_kg']} kg")
    st.write(f"**Height:** {mascot_row['Height_cm']} cm")
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
