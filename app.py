import streamlit as st
import pandas as pd
from datetime import datetime

# ---- Load Master Data ----
@st.cache_data
def load_mascot_data():
    return pd.read_excel("cleaned_rentals.xlsx")

mascots_df = load_mascot_data()

# ---- Load or Create Rental Log ----
def load_rental_log():
    try:
        return pd.read_excel("rental_log.xlsx")
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "ID", "Timestamp", "Mascot_Name", "Start_Date", "End_Date",
            "Size", "Weight_kg", "Height_cm", "Quantity",
            "Rent_Price", "Sale_Price", "Status"
        ])

rental_log_df = load_rental_log()

# ---- Streamlit App ----
st.title("🗓️ Baba Jina Mascot Rental Calendar")

# ---- Mascot Selection ----
mascot_names = mascots_df["Mascot_Name"].unique()
selected_mascot = st.selectbox("Select a mascot:", mascot_names)

# ---- Date Range Selection ----
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date")
with col2:
    end_date = st.date_input("End Date")

# ---- Auto-Fill Mascot Details ----
mascot_info = mascots_df[mascots_df["Mascot_Name"] == selected_mascot].iloc[0]

st.markdown("### Mascot Details")
st.write(f"**Size:** {mascot_info['Size']}")
st.write(f"**Weight:** {mascot_info['Weight_kg']} kg")
st.write(f"**Height:** {mascot_info['Height_cm']} cm")
st.write(f"**Quantity Available:** {mascot_info['Quantity']}")
st.write(f"**Rent Price:** ${mascot_info['Rent_Price']}")
st.write(f"**Sale Price:** ${mascot_info['Sale_Price']}")
st.write(f"**Status:** {mascot_info['Status']}")

# ---- Submit Rental ----
if st.button("📩 Submit Rental"):
    new_id = rental_log_df["ID"].max() + 1 if not rental_log_df.empty else 1
    new_rental = pd.DataFrame([{
        "ID": new_id,
        "Timestamp": datetime.now(),
        "Mascot_Name": selected_mascot,
        "Start_Date": start_date,
        "End_Date": end_date,
        "Size": mascot_info['Size'],
        "Weight_kg": mascot_info['Weight_kg'],
        "Height_cm": mascot_info['Height_cm'],
        "Quantity": mascot_info['Quantity'],
        "Rent_Price": mascot_info['Rent_Price'],
        "Sale_Price": mascot_info['Sale_Price'],
        "Status": mascot_info['Status']
    }])

    rental_log_df = pd.concat([rental_log_df, new_rental], ignore_index=True)
    rental_log_df.to_excel("rental_log.xlsx", index=False)
    st.success("✅ Rental submitted and logged!")
