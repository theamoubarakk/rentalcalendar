import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---- Load base mascot inventory ----
@st.cache_data
def load_inventory():
    return pd.read_excel("cleaned_rentals.xlsx")

# ---- Load rental log ----
@st.cache_data
def load_rental_log():
    try:
        return pd.read_excel("rental_log.xlsx")
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "ID", "Mascot_Name", "Start_Date", "End_Date", 
            "Size", "Weight_kg", "Height_cm", "Quantity",
            "Rent_Price", "Sale_Price", "Status"])

inventory_df = load_inventory()
rental_log_df = load_rental_log()

# ---- Sidebar Filters ----
st.sidebar.header("📊 Filters")
selected_mascot = st.sidebar.selectbox("Select Mascot", ["All"] + sorted(inventory_df["Mascot_Name"].unique()))
start_filter = st.sidebar.date_input("Start Date Filter", value=datetime.today())
end_filter = st.sidebar.date_input("End Date Filter", value=datetime.today())

# ---- Main Title ----
st.title(":calendar: Baba Jina Mascot Rental Calendar")
st.markdown("### :date: Booking Calendar Overview")

# ---- Filtered Calendar View ----
filtered_log = rental_log_df.copy()

# Convert date columns to datetime
filtered_log["Start_Date"] = pd.to_datetime(filtered_log["Start_Date"], errors="coerce")
filtered_log["End_Date"] = pd.to_datetime(filtered_log["End_Date"], errors="coerce")

# Apply filters
if selected_mascot != "All":
    filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]

filtered_log = filtered_log[
    (filtered_log["Start_Date"] <= end_filter) &
    (filtered_log["End_Date"] >= start_filter)
]

# ---- Calendar Gantt View ----
if not filtered_log.empty:
    fig = px.timeline(
        filtered_log,
        x_start="Start_Date",
        x_end="End_Date",
        y="Mascot_Name",
        color="Mascot_Name",
        title="Rental Schedule",
    )
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No rentals in the selected period.")

# ---- Booking Form ----
st.markdown("### 📌 New Rental Entry")

with st.form("rental_form"):
    mascot_choice = st.selectbox("Select a mascot:", inventory_df["Mascot_Name"].unique())
    start_date = st.date_input("Start Date", value=datetime.today())
    end_date = st.date_input("End Date", value=datetime.today())

    mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]

    st.markdown("### 📋 Mascot Details")
    st.write(f"**Size:** {mascot_row['Size']}")
    st.write(f"**Weight:** {mascot_row['Weight_kg']} kg")
    st.write(f"**Height:** {mascot_row['Height_cm']} cm")
    st.write(f"**Quantity Available:** {mascot_row['Quantity']}")
    st.write(f"**Rent Price:** ${mascot_row['Rent_Price']}")
    st.write(f"**Sale Price:** ${mascot_row['Sale_Price']}")
    st.write(f"**Status:** {mascot_row['Status']}")

    submitted = st.form_submit_button(":inbox_tray: Submit Rental")

    if submitted:
        new_entry = pd.DataFrame([{
            "ID": mascot_row["ID"],
            "Mascot_Name": mascot_row["Mascot_Name"],
            "Start_Date": start_date,
            "End_Date": end_date,
            "Size": mascot_row["Size"],
            "Weight_kg": mascot_row["Weight_kg"],
            "Height_cm": mascot_row["Height_cm"],
            "Quantity": mascot_row["Quantity"],
            "Rent_Price": mascot_row["Rent_Price"],
            "Sale_Price": mascot_row["Sale_Price"],
            "Status": mascot_row["Status"]
        }])
        rental_log_df = pd.concat([rental_log_df, new_entry], ignore_index=True)
        rental_log_df.to_excel("rental_log.xlsx", index=False)
        st.success("✅ Rental submitted and logged!")
