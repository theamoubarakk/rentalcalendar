import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# ---- Load inventory from Excel ----
@st.cache_data
def load_inventory():
    # Make sure to have a file named 'cleaned_rentals.xlsx' in the same directory
    # or provide the correct path.
    try:
        return pd.read_excel("cleaned_rentals.xlsx")
    except FileNotFoundError:
        st.error("Error: 'cleaned_rentals.xlsx' not found. Please add it to the app directory.")
        # Create a dummy dataframe to prevent the app from crashing
        return pd.DataFrame({
            "Mascot_Name": ["Sample Mascot"], "ID": [0], "Size": ["M"], "Weight_kg": [10],
            "Height_cm": [180], "Quantity": [1], "Rent_Price": [100], "Sale_Price": [500], "Status": ["Available"]
        })

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
st.markdown("### 🗓️ Monthly Calendar")
col1, col2, _ = st.columns([2, 2, 6]) # Use _ to ignore the third column
with col1:
    # Ensure mascot names are unique and sorted
    mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
    selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
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
        names = ", ".join(booked["Mascot_Name"].unique())
        return f"❌ {names}"

calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)

# ---- NEW, MORE RELIABLE CSS SOLUTION ----
# We inject a hidden div as an anchor point.
st.markdown('<div id="move-up-anchor"></div>', unsafe_allow_html=True)

# Then we use CSS to target the element that comes immediately after our anchor.
# This moves the entire next block (our two columns) up.
st.markdown("""
    <style>
    #move-up-anchor + div[data-testid="stHorizontalBlock"] {
        margin-top: -45px !important;
    }
    </style>
""", unsafe_allow_html=True)


# ---- Layout: Calendar Grid + Rental Form ----
left, right = st.columns([3, 2], gap="large")

with right:
    # ---- New Rental Entry Form ----
    st.markdown("### 📌 New Rental Entry")

    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        start_date = st.date_input("Start Date", value=datetime.today())
        end_date = st.date_input("End Date", value=datetime.today())

        if not inventory_df[inventory_df["Mascot_Name"] == mascot_choice].empty:
            mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]

            weight_display = "N/A" if pd.isna(mascot_row.get("Weight_kg")) else f"{mascot_row['Weight_kg']} kg"
            height_display = "N/A" if pd.isna(mascot_row.get("Height_cm")) else f"{mascot_row['Height_cm']} cm"
            size_display = mascot_row.get('Size', 'N/A')
            quantity_display = mascot_row.get('Quantity', 'N/A')
            rent_price_display = f"${mascot_row.get('Rent_Price', 'N/A')}"
            sale_price_display = f"${mascot_row.get('Sale_Price', 'N/A')}"
            status_display = mascot_row.get('Status', 'N/A')


            st.markdown("### 📋 Mascot Details")
            st.write(f"Size: {size_display}")
            st.write(f"Weight: {weight_display}")
            st.write(f"Height: {height_display}")
            st.write(f"Quantity Available: {quantity_display}")
            st.write(f"Rent Price: {rent_price_display}")
            st.write(f"Sale Price: {sale_price_display}")
            st.write(f"Status: {status_display}")

        submitted = st.form_submit_button("📩 Submit Rental")

        if submitted:
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
    
    # Other components for the right column can follow here...


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
                    st.markdown("")
                else:
                    date = datetime(month_filter.year, month_filter.month, day)
                    status_series = calendar_df.loc[calendar_df["Date"] == date, "Status"]
                    
                    if not status_series.empty:
                        status = status_series.iloc[0]
                        is_booked = "❌" in status
                        bg_color = "#f9e5e5" if is_booked else "#e6ffea"
                        icon, text = status.split(" ", 1)

                        st.markdown(f"""
                            <div style='
                                background-color:{bg_color};
                                border-radius:10px;
                                padding:10px;
                                text-align:center;
                                box-shadow:0 1px 3px rgba(0,0,0,0.05);
                                margin-bottom:8px;
                                min-height:80px;'>
                                <strong>{day}</strong><br>
                                <div style='font-size: 0.9em;'>{icon} {text}</div>
                            </div>
                        """, unsafe_allow_html=True)
