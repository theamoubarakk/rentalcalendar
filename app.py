import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import sqlite3

# --- Configuration and Core Functions ---
st.set_page_config(layout="wide")

@st.cache_data
def load_inventory_from_excel(file_path="cleaned_rentals.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(f"Error: The inventory file '{file_path}' was not found.")
        st.info("Please make sure the inventory file is in the same directory as the app script.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred while reading the Excel file: {e}")
        return pd.DataFrame()

    column_mapping = {
        'Mascot Name': 'Mascot_Name', 'Kg': 'Weight_kg', 'cm': 'Height_cm',
        'pcs': 'Quantity', 'Rent Price': 'Rent_Price', 'Sale Price': 'Sale_Price',
        'Status (Available, Rented, Reserved, Under Repair)': 'Status'
    }
    df.rename(columns=column_mapping, inplace=True)
    if 'Mascot_Name' in df.columns:
        df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    df.dropna(subset=['ID', 'Mascot_Name'], inplace=True)
    df = df[df['Mascot_Name'] != '']
    return df

def init_db(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascot_id INTEGER,
            mascot_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            contact_phone TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def load_rental_log(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM rentals", conn)
    conn.close()
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date']   = pd.to_datetime(df['end_date'])
    return df

def check_availability(log_df, mascot_name, start_dt, end_dt):
    if log_df.empty:
        return 0
    bookings = log_df[log_df['mascot_name'] == mascot_name]
    conflicts = bookings[
        (bookings['start_date'] <= end_dt) &
        (bookings['end_date'] >= start_dt)
    ]
    return len(conflicts)

# --- Initialize ---
init_db()
inventory_df   = load_inventory_from_excel()
rental_log_df  = load_rental_log()

st.title("📅 Baba Jina Mascot Rental Calendar")
if inventory_df.empty:
    st.stop()

# --- Page Layout ---
left_col, right_col = st.columns([3,2], gap="large")

with left_col:
    # ... (calendar + delete + download code unchanged) ...
    pass

with right_col:
    st.markdown("### 📌 New Rental Entry")
    with st.form("rental_form"):
        # 1) Mascot selector
        mascot_choice = st.selectbox(
            "Select a mascot:",
            sorted(inventory_df["Mascot_Name"].unique())
        )

        # 2) Customer & Phone side-by-side
        col_name, col_phone = st.columns(2)
        with col_name:
            customer_name = st.text_input("Customer Name:")
        with col_phone:
            contact_phone = st.text_input("Contact Phone Number:")

        # 3) Start & End dates side-by-side
        col_start, col_end = st.columns(2)
        with col_start:
            start_date_input = st.date_input(
                "Start Date",
                value=datetime.today()
            )
        with col_end:
            end_date_input = st.date_input(
                "End Date",
                value=datetime.today()
            )

        # 4) Mascot details in two columns
        mascot_row = inventory_df[
            inventory_df["Mascot_Name"] == mascot_choice
        ].iloc[0]
        def fmt(v):
            if pd.isna(v): return "N/A"
            try: return f"${int(float(v))}"
            except: return str(v)

        size_disp     = mascot_row.get("Size", "N/A")
        weight_disp   = f"{mascot_row.get('Weight_kg')} kg" if pd.notna(mascot_row.get('Weight_kg')) else "N/A"
        height_disp   = mascot_row.get("Height_cm", "N/A")
        quantity_disp = int(mascot_row.get("Quantity",0)) if pd.notna(mascot_row.get("Quantity")) else "N/A"
        status_disp   = mascot_row.get("Status", "N/A")

        st.markdown("### 📋 Mascot Details")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"*Size:* {size_disp}")
            st.write(f"*Weight:* {weight_disp}")
            st.write(f"*Height:* {height_disp}")
        with col2:
            st.write(f"*Quantity:* {quantity_disp}")
            st.write(f"*Rent Price:* {fmt(mascot_row.get('Rent_Price'))}")
            st.write(f"*Sale Price:* {fmt(mascot_row.get('Sale_Price'))}")
        st.write(f"*Status:* {status_disp}")

        # 5) Submit logic
        if st.form_submit_button("📩 Submit Rental"):
            if not customer_name:
                st.warning("Please enter a customer name.")
            elif end_date_input < start_date_input:
                st.warning("End date cannot be before start date.")
            else:
                sd = datetime.combine(start_date_input, datetime.min.time())
                ed = datetime.combine(end_date_input,   datetime.min.time())
                total_qty = int(mascot_row.get("Quantity",0))
                booked = check_availability(rental_log_df, mascot_choice, sd, ed)
                if booked >= total_qty:
                    st.error(
                        f"All {total_qty} units of '{mascot_choice}' are booked "
                        "for this period."
                    )
                else:
                    conn = sqlite3.connect("rental_log.db")
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO rentals "
                        "(mascot_id,mascot_name,customer_name,contact_phone,start_date,end_date) "
                        "VALUES (?,?,?,?,?,?)",
                        (
                            int(mascot_row["ID"]),
                            mascot_choice,
                            customer_name,
                            contact_phone,
                            start_date_input,
                            end_date_input
                        )
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Rental submitted! ({booked+1} of {total_qty} booked)")
                    st.experimental_rerun()
