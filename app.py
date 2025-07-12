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
    df['end_date'] = pd.to_datetime(df['end_date'])
    return df

def check_availability(log_df, mascot_name, start_date_req, end_date_req):
    if log_df.empty:
        return 0
    mascot_bookings = log_df[log_df['mascot_name'] == mascot_name]
    conflicts = mascot_bookings[
        (mascot_bookings['start_date'] <= end_date_req) &
        (mascot_bookings['end_date'] >= start_date_req)
    ]
    return len(conflicts)

# --- Initialize ---
init_db()
inventory_df = load_inventory_from_excel()
rental_log_df = load_rental_log()

st.title("📅 Baba Jina Mascot Rental Calendar")

if inventory_df.empty:
    st.stop()

left_col, right_col = st.columns([3, 2], gap="large")


# ==============================================================================
# LEFT: Calendar + Delete + Download
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    c1, c2 = st.columns(2)
    with c1:
        filter_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", filter_list)
    with c2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    # filter log
    filtered_log = rental_log_df.copy()
    if selected_mascot != "All" and not filtered_log.empty:
        filtered_log = filtered_log[filtered_log["mascot_name"] == selected_mascot]

    # calendar dates
    start_m = datetime(month_filter.year, month_filter.month, 1)
    last_day = calendar.monthrange(month_filter.year, month_filter.month)[1]
    end_m = datetime(month_filter.year, month_filter.month, last_day)
    dates = pd.date_range(start=start_m, end=end_m)
    cal_df = pd.DataFrame({"Date": dates})

    # --- only tweak: escape & newline-join tooltip ---
    def get_booking_status(date):
        b = filtered_log[
            (filtered_log["start_date"] <= date) &
            (filtered_log["end_date"] >= date)
        ]
        if b.empty:
            return ("✅ Available", "This day is available.")
        lines = []
        for _, row in b.iterrows():
            name = str(row["customer_name"]).replace('"', '\\"')
            phone = str(row.get("contact_phone", "N/A")).replace('"', '\\"')
            lines.append(f"{row['mascot_name']}: {name} ({phone})")
        tt = "\n".join(lines)  
        disp = f"❌ {', '.join(b['mascot_name'].unique())}"
        return (disp, tt)

    cal_df["Status"] = cal_df["Date"].apply(get_booking_status)

    st.markdown("<hr style='margin:0 0 1rem 0'>", unsafe_allow_html=True)
    weekdays = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    header = st.columns(7)
    for i, wd in enumerate(weekdays):
        header[i].markdown(f"<div style='text-align:center;font-weight:bold;'>{wd}</div>",
                           unsafe_allow_html=True)

    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                continue
            d = datetime(month_filter.year, month_filter.month, day)
            disp, tt = cal_df.loc[cal_df["Date"]==d, "Status"].iloc[0]
            bg = "#f9e5e5" if disp.startswith("❌") else "#e6ffea"
            icon, *txt = disp.split(" ",1)
            cols[i].markdown(
                f"""
                <div title="{tt}"
                     style="
                       background-color:{bg};
                       padding:8px;
                       border-radius:8px;
                       text-align:center;
                       min-height:60px;
                       box-shadow:0 1px 2px rgba(0,0,0,0.1);
                     ">
                  <strong>{day}</strong><br>
                  <small>{icon} {txt[0] if txt else ''}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    # -- Delete --
    dcol, xcol = st.columns(2)
    with dcol:
        st.markdown("### 🗑️ Delete Booking")
        if rental_log_df.empty:
            st.info("No bookings.")
        else:
            mapping = {
                f"{r.customer_name} - {r.mascot_name} ({r.start_date.date()} to {r.end_date.date()})": r.id
                for _,r in rental_log_df.iterrows()
            }
            choice = st.selectbox("Pick to delete:", list(mapping.keys()))
            if st.button("Delete"):
                conn = sqlite3.connect("rental_log.db")
                cur = conn.cursor()
                cur.execute("DELETE FROM rentals WHERE id=?", (mapping[choice],))
                conn.commit()
                conn.close()
                st.success("Deleted.")
                st.experimental_rerun()
    # -- Download --
    with xcol:
        st.markdown("### 📥 Download Log")
        if not rental_log_df.empty:
            csv = rental_log_df.to_csv(index=False).encode("utf-8")
            st.download_button("CSV", csv,
                               file_name=f"log_{datetime.now().date()}.csv",
                               mime="text/csv")
        else:
            st.info("No data to download.")


# ==============================================================================
# RIGHT: New Rental Entry
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    # 1) choose mascot outside form so details update instantly
    mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
    mrow = inventory_df[inventory_df["Mascot_Name"]==mascot_choice].iloc[0]

    # original detail logic, N/A stays N/A
    def fmt_price(v):
        if pd.isna(v): return "N/A"
        try: return f"${int(float(v))}"
        except: return str(v)

    size_disp      = mrow.get("Size","N/A")      if pd.notna(mrow.get("Size"))      else "N/A"
    weight_disp    = f"{mrow.get('Weight_kg')} kg" if pd.notna(mrow.get("Weight_kg")) else "N/A"
    height_disp    = mrow.get("Height_cm","N/A") if pd.notna(mrow.get("Height_cm")) else "N/A"
    qty_disp       = int(mrow.get("Quantity",0)) if pd.notna(mrow.get("Quantity"))   else "N/A"
    status_disp    = mrow.get("Status","N/A")    if pd.notna(mrow.get("Status"))    else "N/A"

    st.markdown("#### Mascot Details")
    st.write(f"**Size:** {size_disp}")
    st.write(f"**Weight:** {weight_disp}")
    st.write(f"**Height:** {height_disp}")
    st.write(f"**Quantity:** {qty_disp}")
    st.write(f"**Rent Price:** {fmt_price(mrow.get('Rent_Price'))}")
    st.write(f"**Sale Price:** {fmt_price(mrow.get('Sale_Price'))}")
    st.write(f"**Status:** {status_disp}")

    # 2) now the form for customer & dates
    with st.form("rental_form"):
        customer_name    = st.text_input("Customer Name:")
        contact_phone    = st.text_input("Contact Phone Number:")
        start_date_input = st.date_input("Start Date", value=datetime.today())
        end_date_input   = st.date_input("End Date",   value=datetime.today())

        if st.form_submit_button("📩 Submit Rental"):
            if not customer_name:
                st.warning("Enter a customer name.")
            elif end_date_input < start_date_input:
                st.warning("End date before start.")
            else:
                sd = datetime.combine(start_date_input, datetime.min.time())
                ed = datetime.combine(end_date_input,   datetime.min.time())
                total_qty = int(mrow.get("Quantity",0))
                booked_ct = check_availability(rental_log_df, mascot_choice, sd, ed)

                if booked_ct >= total_qty:
                    st.error(f"All {total_qty} are booked for that period.")
                else:
                    conn = sqlite3.connect("rental_log.db")
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO rentals (mascot_id, mascot_name, customer_name, contact_phone, start_date, end_date) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (int(mrow["ID"]), mascot_choice, customer_name, contact_phone, start_date_input, end_date_input)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Booked! ({booked_ct+1} of {total_qty})")
                    st.experimental_rerun()
