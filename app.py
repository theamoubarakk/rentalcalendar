import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
        'Mascot Name': 'Mascot_Name',
        'Kg': 'Weight_kg',
        'cm': 'Height_cm',
        'pcs': 'Quantity',
        'Rent Price': 'Rent_Price',
        'Sale Price': 'Sale_Price',
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
    cursor = conn.cursor()
    cursor.execute("""
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

# --- Initialize Database and Load Data ---
init_db()
inventory_df  = load_inventory_from_excel()
rental_log_df = load_rental_log()

# --- Main App ---
st.title("📅 Baba Jina Mascot Rental Calendar")
if inventory_df.empty:
    st.stop()

# --- Layout Definition ---
left_col, right_col = st.columns([3, 2], gap="large")

# ==============================================================================
# LEFT COLUMN: Calendar ONLY
# ==============================================================================
with left_col:
    # ... your existing calendar code unchanged ...
    pass

# ==============================================================================
# RIGHT COLUMN: Form + Submit Messages + Details + Delete/Download
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    # 1) Mascot selector (outside form)
    mascot_choice = st.selectbox(
        "Select a mascot:",
        sorted(inventory_df["Mascot_Name"].unique())
    )

    # 2) The booking form
    with st.form("rental_form"):
        col_name, col_phone = st.columns(2)
        with col_name:
            customer_name = st.text_input("Customer Name:")
        with col_phone:
            contact_phone = st.text_input("Contact Phone Number:")

        col_start, col_end = st.columns(2)
        with col_start:
            start_date_input = st.date_input("Start Date", value=datetime.today())
        with col_end:
            end_date_input   = st.date_input("End Date",   value=datetime.today())

        submitted = st.form_submit_button("📩 Submit Rental")

    # 3) Immediately handle submit-logic here,
    #    so any warnings/errors appear right under the button:
    if submitted:
        if not customer_name:
            st.warning("Please enter a customer name.")
        elif end_date_input < start_date_input:
            st.warning("End date cannot be before start date.")
        else:
            sd = datetime.combine(start_date_input, datetime.min.time())
            ed = datetime.combine(end_date_input,   datetime.min.time())
            row = inventory_df.loc[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
            total_qty = int(row["Quantity"])
            already = check_availability(rental_log_df, mascot_choice, sd, ed)

            if already >= total_qty:
                st.error(f"⚠️ Booking Failed: All {total_qty} units of '{mascot_choice}' are already booked.")
            else:
                conn = sqlite3.connect("rental_log.db")
                c = conn.cursor()
                c.execute(
                    "INSERT INTO rentals (mascot_id,mascot_name,customer_name,contact_phone,start_date,end_date) "
                    "VALUES (?,?,?,?,?,?)",
                    (
                        int(row["ID"]),
                        mascot_choice,
                        customer_name,
                        contact_phone,
                        start_date_input,
                        end_date_input
                    )
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Rental submitted! ({already+1} of {total_qty} booked)")
                st.experimental_rerun()

    # 4) Mascot Details (updates immediately)
    row = inventory_df.loc[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
    def _fmt(v):
        if pd.isna(v): return "N/A"
        try: return f"${int(float(v))}"
        except: return str(v)

    size_disp     = row["Size"]      if pd.notna(row["Size"])      else "N/A"
    weight_disp   = f"{row['Weight_kg']} kg" if pd.notna(row["Weight_kg"]) else "N/A"
    height_disp   = row["Height_cm"] if pd.notna(row["Height_cm"]) else "N/A"
    quantity_disp = int(row["Quantity"])    if pd.notna(row["Quantity"])    else "N/A"
    rent_disp     = _fmt(row["Rent_Price"])
    sale_disp     = _fmt(row["Sale_Price"])
    status_disp   = row["Status"]    if pd.notna(row["Status"])    else "N/A"

    st.markdown("### 📋 Mascot Details")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.write(f"*Size:* {size_disp}")
        st.write(f"*Weight:* {weight_disp}")
        st.write(f"*Height:* {height_disp}")
    with dc2:
        st.write(f"*Quantity:* {quantity_disp}")
        st.write(f"*Rent Price:* {rent_disp}")
        st.write(f"*Sale Price:* {sale_disp}")
    st.write(f"*Status:* {status_disp}")

    # 5) Delete & Download (still at bottom of right column)
    st.markdown("---")
    dcol, xcol = st.columns(2)
    with dcol:
        st.markdown("### 🗑️ Delete Rental Booking")
        if rental_log_df.empty:
            st.info("No bookings to delete.")
        else:
            options = {
                f"{r['customer_name']} – {r['mascot_name']} "
                f"({r['start_date'].date()} to {r['end_date'].date()})": r["id"]
                for _, r in rental_log_df.iterrows()
            }
            choice = st.selectbox("Select booking to delete:", options.keys())
            if st.button("❌ Delete Booking"):
                conn = sqlite3.connect("rental_log.db")
                c = conn.cursor()
                c.execute("DELETE FROM rentals WHERE id = ?", (options[choice],))
                conn.commit()
                conn.close()
                st.success("🗑️ Booking deleted successfully.")
                st.experimental_rerun()

    with xcol:
        st.markdown("### 📥 Download Rental Log")
        if not rental_log_df.empty:
            csv = rental_log_df.to_csv(index=False).encode("utf-8")
            st.download_button(
               "Download Log as CSV",
               data=csv,
               file_name=f"rental_log_{datetime.today().date()}.csv",
               mime="text/csv"
            )
        else:
            st.info("No rental log data to download.")
