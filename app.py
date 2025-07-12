import streamlit as st

# ─────────── remove white-space ───────────
st.markdown(
    """
    <style>
      /* remove the big top and bottom padding from every page block */
      .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
      }
      /* collapse the extra margin under headers, forms, etc */
      .css-1avcm0n, /* hr container */
      .css-18e3th9 { /* main gap container */
        margin-bottom: 0.25rem !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)
# ─────────────────────────────────────────────

import pandas as pd
from datetime import datetime, timedelta
import calendar
import sqlite3

# --- Configuration ---
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

    df.rename(columns={
        'Mascot Name': 'Mascot_Name',
        'Kg': 'Weight_kg',
        'cm': 'Height_cm',
        'pcs': 'Quantity',
        'Rent Price': 'Rent_Price',
        'Sale Price': 'Sale_Price',
        'Status (Available, Rented, Reserved, Under Repair)': 'Status'
    }, inplace=True)
    if 'Mascot_Name' in df.columns:
        df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    df.dropna(subset=['ID','Mascot_Name'], inplace=True)
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
      (bookings['end_date']   >= start_dt)
    ]
    return len(conflicts)

# --- Init ---
init_db()
inventory_df  = load_inventory_from_excel()
rental_log_df = load_rental_log()

st.title("📅 Baba Jina Mascot Rental Calendar")
if inventory_df.empty:
    st.stop()

left_col, right_col = st.columns([3,2], gap="large")

# ==============================================================================
# LEFT: Calendar Only
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    c1, c2 = st.columns(2)
    with c1:
        mascot_list      = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot  = st.selectbox("Filter by Mascot:", mascot_list)
    with c2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    filtered_log = rental_log_df.copy()
    if selected_mascot != "All":
        filtered_log = filtered_log[filtered_log["mascot_name"] == selected_mascot]

    # build calendar dataframe
    month_start = datetime(month_filter.year, month_filter.month, 1)
    last_day    = calendar.monthrange(month_filter.year, month_filter.month)[1]
    month_end   = datetime(month_filter.year, month_filter.month, last_day)
    date_range  = pd.date_range(start=month_start, end=month_end)
    cal_df      = pd.DataFrame({"Date": date_range})

    def get_booking_status(date):
        booked = filtered_log[
          (filtered_log["start_date"] <= date) &
          (filtered_log["end_date"]   >= date)
        ]
        if booked.empty:
            return ("✅ Available","This day is available for booking.")
        txt = f"❌ {', '.join(booked['mascot_name'].unique())}"
        tips = [f'{r.mascot_name}: {r.customer_name} ({r.contact_phone})'
                for _,r in booked.iterrows()]
        return (txt, "\n".join(tips))

    cal_df["Status"] = cal_df["Date"].apply(get_booking_status)
    st.markdown("<hr style='margin-top:0; margin-bottom:1rem;'>",unsafe_allow_html=True)

    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdrs = st.columns(7)
    for i,d in enumerate(days):
        hdrs[i].markdown(f"<div style='text-align:center;font-weight:bold'>{d}</div>",unsafe_allow_html=True)

    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i,day in enumerate(week):
            if day==0: continue
            dt = datetime(month_filter.year, month_filter.month, day)
            status_txt, tip = cal_df.loc[cal_df["Date"]==dt,"Status"].iloc[0]
            bg = "#f9e5e5" if status_txt.startswith("❌") else "#e6ffea"
            icon,*txt = status_txt.split(" ",1)
            cols[i].markdown(f"""
              <div title="{tip}" style="
                background-color:{bg};
                border-radius:10px;
                padding:10px;
                text-align:center;
                box-shadow:0 1px 3px rgba(0,0,0,0.05);
                margin-bottom:8px;
                min-height:80px;
              ">
                <strong>{day}</strong><br>
                <div style='font-size:0.9em; word-wrap:break-word'>
                  {icon} {txt[0] if txt else ''}
                </div>
              </div>
            """,unsafe_allow_html=True)

# ==============================================================================
# RIGHT: New Entry + Feedback + Details + Delete/Download
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    # 1) Mascot selector OUTSIDE form, so details update immediately
    mascot_choice = st.selectbox(
      "Select a mascot:",
      sorted(inventory_df["Mascot_Name"].unique())
    )

    # 2) Booking form
    with st.form("rental_form"):
        cn, cp = st.columns(2)
        with cn:
            customer_name = st.text_input("Customer Name:")
        with cp:
            contact_phone = st.text_input("Contact Phone Number:")

        cs, ce = st.columns(2)
        with cs:
            start_date_input = st.date_input("Start Date", value=datetime.today())
        with ce:
            end_date_input   = st.date_input("End Date",   value=datetime.today())

        submitted = st.form_submit_button("📩 Submit Rental")

    # 3) Inline feedback
    if submitted:
        if not customer_name:
            st.warning("Please enter a customer name.")
        elif end_date_input < start_date_input:
            st.warning("End date cannot be before start date.")
        else:
            sd    = datetime.combine(start_date_input, datetime.min.time())
            ed    = datetime.combine(end_date_input,   datetime.min.time())
            row   = inventory_df.query("Mascot_Name == @mascot_choice").iloc[0]
            total = int(row["Quantity"])
            used  = check_availability(rental_log_df, mascot_choice, sd, ed)

            if used >= total:
                st.error(f"⚠️ Booking Failed: All {total} units of '{mascot_choice}' are already booked.")
            else:
                conn = sqlite3.connect("rental_log.db")
                c    = conn.cursor()
                c.execute(
                  "INSERT INTO rentals (mascot_id,mascot_name,customer_name,contact_phone,start_date,end_date) VALUES (?,?,?,?,?,?)",
                  (int(row["ID"]), mascot_choice, customer_name, contact_phone, start_date_input, end_date_input)
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Rental submitted! ({used+1} of {total} booked)")
                st.experimental_rerun()

    # 4) Mascot Details (including true inventory Status)
    row = inventory_df.query("Mascot_Name == @mascot_choice").iloc[0]
    def fmt_price(v):
        if pd.isna(v): return "N/A"
        try: return f"${int(float(v))}"
        except: return str(v)

    size  = row.get("Size","N/A")
    wt    = f"{row['Weight_kg']} kg"    if pd.notna(row["Weight_kg"]) else "N/A"
    ht    = row.get("Height_cm","N/A")
    qty   = int(row["Quantity"])        if pd.notna(row["Quantity"])  else "N/A"
    rent  = fmt_price(row.get("Rent_Price"))
    sale  = fmt_price(row.get("Sale_Price"))
    stat  = row.get("Status","N/A")

    st.markdown("### 📋 Mascot Details")
    d1,d2 = st.columns(2)
    with d1:
        st.write(f"*Size:* {size}")
        st.write(f"*Weight:* {wt}")
        st.write(f"*Height:* {ht}")
    with d2:
        st.write(f"*Quantity:* {qty}")
        st.write(f"*Rent Price:* {rent}")
        st.write(f"*Sale Price:* {sale}")
    st.write(f"*Status:* {stat}")

    # 5) Delete & Download
    st.markdown("---")
    dc, dl = st.columns(2)
    with dc:
        st.markdown("### 🗑️ Delete Rental Booking")
        if rental_log_df.empty:
            st.info("No bookings to delete.")
        else:
            m = {
              f"{r.customer_name} - {r.mascot_name} ({r.start_date.date()} to {r.end_date.date()})": r.id
              for _,r in rental_log_df.iterrows()
            }
            sel = st.selectbox("Select booking to delete:", list(m.keys()), key="del")
            if st.button("❌ Delete Booking"):
                conn = sqlite3.connect("rental_log.db")
                c    = conn.cursor()
                c.execute("DELETE FROM rentals WHERE id = ?", (m[sel],))
                conn.commit()
                conn.close()
                st.success("🗑️ Booking deleted successfully.")
                st.experimental_rerun()
    with dl:
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
