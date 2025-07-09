import streamlit as st
import pandas as pd

# Step 1: Set up page configuration
st.set_page_config(page_title="Mascot Rental Dashboard", layout="wide")

# Step 2: App title
st.title("🧸 Baba Jina Mascot Rental Dashboard")

# Step 3: Load or create example data
# Here we use a simple example DataFrame instead of loading an Excel file
sample_data = {
    "Mascot_Name": ["Lion", "Bear", "Unicorn"],
    "Size": ["L", "M", "XL"],
    "Weight_kg": [12, 10, 15],
    "Height_cm": [150, 130, 160],
    "Rent_Price": [40, 35, 50],
    "Status": ["Available", "Rented", "Reserved"]
}

df = pd.DataFrame(sample_data)

# Step 4: Display the DataFrame with styled status
status_color = {
    "Available": "✅",
    "Rented": "❌",
    "Reserved": "⏳",
    "Under Repair": "🛠️"
}

# Step 5: Render each mascot in a 3-column layout
cols = st.columns(3)
for idx, row in df.iterrows():
    col = cols[idx % 3]
    with col:
        st.markdown(f"### {row['Mascot_Name']}")
        st.markdown(f"**Size:** {row['Size']}")
        st.markdown(f"**Weight:** {row['Weight_kg']} kg")
        st.markdown(f"**Height:** {row['Height_cm']} cm")
        st.markdown(f"**Rent Price:** ${row['Rent_Price']}")
        st.markdown(f"**Status:** {status_color.get(row['Status'], '')} {row['Status']}")
        st.markdown("---")
