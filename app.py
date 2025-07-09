import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# Load data
@st.cache_data
def load_data():
    return pd.read_excel("cleaned_rentals.xlsx")

@st.cache_data
def load_log():
    return pd.read_excel("rental_log.xlsx")

mascot_df = load_data()
log_df = load_log()

# Sidebar filters
st.sidebar.header("📊 Filters")
selected_mascot = st.sidebar.selectbox("Select Mascot", ["All"] + list(mascot_df["Mascot_Name"].unique()))
start_filter = st.sidebar.date_input("Start Date Filter", value=date(2025, 7, 1))
end_filter = st.sidebar.date_input("End Date Filter", value=date(2025, 7, 31))

# Filter rental logs
filtered_log = log_df.copy()
if selected_mascot != "All":
    filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]
filtered_log = filtered_log[
    (filtered_log["Start_Date"] <= end_filter) &
    (filtered_log["End_Date"] >= start_filter)
]

# Conflict warning
if selected_mascot != "All":
    mascot_row = mascot_df[mascot_df["Mascot_Name"] == selected_mascot].iloc[0]
    quantity_available = mascot_row["Quantity Available"]
    conflicts = len(filtered_log)
    if conflicts >= quantity_available:
        st.warning(f"⚠️ All units of '{selected_mascot}' are booked between {start_filter} and {end_filter}.")

# Title
st.markdown("## 🗓️ Rental Calendar Overview")

# Calendar Plot
if not filtered_log.empty:
    fig = px.timeline(
        filtered_log,
        x_start="Start_Date",
        x_end="End_Date",
        y="Mascot_Name",
        color="Status",
        title="Rental Periods"
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No rentals match your filters.")

# Table view
with st.expander("📋 View Rental Log Table"):
    st.dataframe(filtered_log)
