import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    return pd.read_excel("cleaned_rentals.xlsx")

df = load_data()

# ---- Sidebar: Filter ----
st.sidebar.header("Filter Rental Status")
status_filter = st.sidebar.selectbox("Show items with status:", ["All", "Available", "Rented", "Reserved"])

# Apply filter
if status_filter != "All":
    status_map = {
        "Available": "✅ Available",
        "Rented": "❌ Rented",
        "Reserved": "⏳ Reserved"
    }
    df = df[df['Status'] == status_map[status_filter]]

# ---- Main: Dashboard ----
st.markdown("## 🧸 Baba Jina Mascot Rental Dashboard")

cols = st.columns(3)
for i, row in df.iterrows():
    with cols[i % 3]:
        st.subheader(row['Mascot_Name'])
        st.markdown(f"**Size:** {row['Size']}")
        st.markdown(f"**Weight_kg:** {row['Weight_kg']} kg")
        st.markdown(f"**Height:** {row['Height']} cm")
        st.markdown(f"**Rent Price:** ${row['Rent Price']}")
        st.markdown(f"**Status:** {row['Status']}")
        st.markdown("---")

# ---- Section: Add New Rental Entry ----
st.markdown("## ➕ Add New Rental Item")

with st.form("rental_form"):
    name = st.text_input("Mascot_Name")
    size = st.selectbox("Size", ["S", "M", "L", "XL"])
    weight = st.number_input("Weight (kg)", min_value=1)
    height = st.number_input("Height (cm)", min_value=50)
    price = st.number_input("Rent Price ($)", min_value=1)
    status = st.selectbox("Status", ["✅ Available", "❌ Rented", "⏳ Reserved"])

    submitted = st.form_submit_button("Add Rental")
    if submitted:
        new_entry = pd.DataFrame([{
            "Mascot_Name": name,
            "Size": size,
            "Weight": weight,
            "Height": height,
            "Rent Price": price,
            "Status": status
        }])
        df_updated = pd.concat([df, new_entry], ignore_index=True)
        df_updated.to_excel("cleaned_rentals.xlsx", index=False)
        st.success("✅ Rental item added! Please refresh the page to see changes.")
