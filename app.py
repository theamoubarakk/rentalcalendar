import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

# Load rental inventory
@st.cache_data
def load_inventory():
    return pd.read_excel("cleaned_rentals.xlsx")

# Load rental log
def load_log():
    try:
        log = pd.read_excel("rental_log.xlsx")
        log["Start_Date"] = pd.to_datetime(log["Start_Date"])
        log["End_Date"] = pd.to_datetime(log["End_Date"])
        return log
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Mascot_Name", "Start_Date", "End_Date"])

# Save new log
def save_log(df):
    df.to_excel("rental_log.xlsx", index=False)

# App layout
st.set_page_config("Baba Jina Mascot Rental Calendar", layout="wide")
st.title("📅 Baba Jina Mascot Rental Calendar")

# Load data
df = load_inventory()
log_df = load_log()

# ---- Rental Form ----
st.markdown("### 🎟️ Submit a Rental")

mascot_options = df["Mascot_Name"].unique()
selected_mascot = st.selectbox("Select a mascot:", mascot_options)
start_date = st.date_input("Start Date", date.today())
end_date = st.date_input("End Date", date.today())

# Show mascot details
mascot_row = df[df["Mascot_Name"] == selected_mascot].iloc[0]

st.markdown("### 📋 Mascot Details")
st.write(f"**Size:** {mascot_row['Size']}")
st.write(f"**Weight:** {mascot_row['Weight_kg']} kg")
st.write(f"**Height:** {mascot_row['Height']} cm")
st.write(f"**Quantity Available:** {mascot_row['Quantity']}")
st.write(f"**Rent Price:** ${mascot_row['Rent Price']}")
st.write(f"**Sale Price:** ${mascot_row['Sale Price']}")
st.write(f"**Status:** {mascot_row['Status']}")

# Rental submission
if st.button("📮 Submit Rental"):
    new_log = {
        "ID": mascot_row["ID"],
        "Mascot_Name": selected_mascot,
        "Start_Date": start_date,
        "End_Date": end_date
    }
    log_df = pd.concat([log_df, pd.DataFrame([new_log])], ignore_index=True)
    save_log(log_df)
    st.success("✅ Rental submitted and logged!")

# ---- Rental History Filter ----
st.sidebar.header("📊 Filters")
filter_name = st.sidebar.selectbox("Select Mascot", ["All"] + list(df["Mascot_Name"].unique()))
start_filter = st.sidebar.date_input("Start Date Filter", date(2025, 7, 1))
end_filter = st.sidebar.date_input("End Date Filter", date(2025, 7, 31))

filtered_log = log_df.copy()

if filter_name != "All":
    filtered_log = filtered_log[filtered_log["Mascot_Name"] == filter_name]

# Convert date filter inputs to datetime
start_filter = pd.to_datetime(start_filter)
end_filter = pd.to_datetime(end_filter)

# Filter by date range
filtered_log = filtered_log[
    (filtered_log["Start_Date"] <= end_filter) &
    (filtered_log["End_Date"] >= start_filter)
]

# Show log
st.markdown("### 📘 Rental Log")
st.dataframe(filtered_log)

# ---- Optional: Calendar Overview ----
st.markdown("### 📆 Calendar Heatmap")
if not filtered_log.empty:
    heatmap_df = filtered_log.copy()
    heatmap_df["Start_Date"] = pd.to_datetime(heatmap_df["Start_Date"])
    heatmap_df["count"] = 1
    daily_count = heatmap_df.groupby("Start_Date").count()["count"].reset_index()
    fig = px.density_heatmap(
        daily_count,
        x="Start_Date",
        y="count",
        nbinsx=30,
        title="Rental Volume Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No rentals in selected range.")
