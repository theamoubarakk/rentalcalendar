import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

# Load mascot data
@st.cache_data
def load_mascot_data():
    return pd.read_excel("cleaned_rentals.xlsx")

# Load rental log
def load_rental_log():
    try:
        return pd.read_excel("rental_log.xlsx")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Mascot_Name", "Start_Date", "End_Date"])

mascots_df = load_mascot_data()
rental_log_df = load_rental_log()

# Page config
st.set_page_config("Rental Calendar", layout="wide")
st.title("📅 Baba Jina Mascot Rental Calendar")

# ---- Sidebar Filters ----
st.sidebar.header("📊 Filters")
mascot_options = ["All"] + mascots_df["Mascot_Name"].dropna().unique().tolist()
selected_mascot = st.sidebar.selectbox("Select Mascot", mascot_options)

start_filter = st.sidebar.date_input("Start Date Filter", date(2025, 7, 1))
end_filter = st.sidebar.date_input("End Date Filter", date(2025, 7, 31))

# ---- Booking Overview Calendar ----
st.subheader("📆 Booking Calendar Overview")
filtered_log = rental_log_df.copy()
if selected_mascot != "All":
    filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]

filtered_log = filtered_log[
    pd.to_datetime(filtered_log["Start_Date"]) <= end_filter
]
filtered_log = filtered_log[
    pd.to_datetime(filtered_log["End_Date"]) >= start_filter
]

if not filtered_log.empty:
    fig = px.timeline(
        filtered_log,
        x_start="Start_Date",
        x_end="End_Date",
        y="Mascot_Name",
        color="Mascot_Name",
        title="Mascot Rental Timeline",
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Mascot", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No rentals found for the selected filter range.")

# ---- Booking Form ----
st.subheader("🧸 Book a Mascot")
mascot_choice = st.selectbox("Select a mascot:", mascots_df["Mascot_Name"].unique())
start_date = st.date_input("Start Date", date.today())
end_date = st.date_input("End Date", date.today())

if mascot_choice:
    mascot_row = mascots_df[mascots_df["Mascot_Name"] == mascot_choice].iloc[0]
    st.markdown("### 📋 Mascot Details")
    st.write(f"**Size:** {mascot_row['Size']}")
    st.write(f"**Weight:** {mascot_row['Weight_kg']} kg")
    st.write(f"**Height:** {mascot_row['Height_cm']} cm")
    st.write(f"**Quantity Available:** {mascot_row['Quantity']}")
    st.write(f"**Rent Price:** ${mascot_row['Rent_Price']}")
    st.write(f"**Sale Price:** ${mascot_row['Sale_Price']}")
    st.write(f"**Status:** {mascot_row['Status']}")

    # Submit
    if st.button("📌 Submit Rental"):
        new_rental = {
            "Mascot_Name": mascot_choice,
            "Start_Date": start_date,
            "End_Date": end_date
        }
        updated_log = pd.concat([rental_log_df, pd.DataFrame([new_rental])], ignore_index=True)
        updated_log.to_excel("rental_log.xlsx", index=False)
        st.success("✅ Rental submitted and logged!")
