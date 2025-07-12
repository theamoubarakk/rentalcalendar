import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import sqlite3

# ─────────── remove white-space ───────────
st.markdown(
    """
    <style>
      /* collapse all block padding */
      .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
      }
      /* tighten margins under headers/forms */
      .css-1avcm0n,
      .css-18e3th9 {
        margin-bottom: 0.25rem !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)
# ─────────────────────────────────────────────

st.set_page_config(layout="wide")

# ─── HEADER ROW: Title on left, Hi-Res Logo on right ───
hdr_title, hdr_logo = st.columns([9, 1], gap="small")
with hdr_title:
    st.markdown("### 📅 Baba Jina Mascot Rental Calendar")
with hdr_logo:
    # use a 2× resolution file, then display at 200px wide
    st.image("logo@2x.png", width=200)


# --- Data loading & core functions ---
@st.cache_data
def load_inventory_from_excel(file_path="cleaned_rentals.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(f"Error: The inventory file '{file_path}' was not found.")
        st.info("Please place 'cleaned_rentals.xlsx' next to this script.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred: {e}")
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
    df = df.dropna(subset=['ID','Mascot_Name'])
    df['Mascot_Name'] = df['Mascot_Name'].str.strip()
    return df[df['Mascot_Name'] != '']

def init_db(db_file="rental_log.db"):
    conn = sqlite3.connect(db_file)
    conn.execute("""
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
    df = pd.read_sql("SELECT * FROM rentals", conn)
    conn.close()
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date']   = pd.to_datetime(df['end_date'])
    return df

def check_availability(log_df, name, start_dt, end_dt):
    if log_df.empty: return 0
    busy = log_df[
      (log_df['mascot_name'] == name) &
      (log_df['start_date'] <= end_dt) &
      (log_df['end_date']   >= start_dt)
    ]
    return len(busy)

# --- Initialize & load data ---
init_db()
inventory_df  = load_inventory_from_excel()
rental_log_df = load_rental_log()
if inventory_df.empty:
    st.stop()

# --- Main two-column layout ---
left_col, right_col = st.columns([3,2], gap="large")

# LEFT: Calendar
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    c1, c2 = st.columns(2)
    with c1:
        choices = ["All"] + sorted(inventory_df["Mascot_Name"])
        sel_mascot = st.selectbox("Filter by Mascot:", choices)
    with c2:
        month_sel = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    df_log = rental_log_df.copy()
    if sel_mascot != "All":
        df_log = df_log[df_log["mascot_name"] == sel_mascot]

    start = datetime(month_sel.year, month_sel.month, 1)
    end   = datetime(month_sel.year, month_sel.month,
                     calendar.monthrange(month_sel.year, month_sel.month)[1])
    days = pd.date_range(start, end)
    cal = pd.DataFrame({"Date": days})

    def day_status(d):
        b = df_log[(df_log['start_date'] <= d) & (df_log['end_date'] >= d)]
        if b.empty:
            return ("✅", "Available")
        names = ", ".join(b['mascot_name'].unique())
        return (f"❌ {names}", "\n".join(
            f"{r.mascot_name}: {r.customer_name}" for _,r in b.iterrows()
        ))

    cal["ST"] = cal["Date"].apply(day_status)
    st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)

    # weekday headers
    wk = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdr = st.columns(7)
    for i,wd in enumerate(wk):
        hdr[i].markdown(f"**{wd}**", unsafe_allow_html=True)

    # calendar grid
    for week in calendar.monthcalendar(month_sel.year, month_sel.month):
        cols = st.columns(7)
        for i,day in enumerate(week):
            if day == 0: continue
            d = datetime(month_sel.year, month_sel.month, day)
            txt,tip = cal.loc[cal["Date"]==d,"ST"].iloc[0]
            bg = "#f9e5e5" if txt.startswith("❌") else "#e6ffea"
            icon = txt.split()[0]
            cols[i].markdown(
                f"<div title='{tip}' style='background:{bg};padding:8px;border-radius:8px;text-align:center;min-height:70px;'>"
                f"<strong>{day}</strong><br>{icon}"
                "</div>",
                unsafe_allow_html=True
            )

# RIGHT: Form, details, delete/download
with right_col:
    st.markdown("### 📌 New Rental Entry")
    choice = st.selectbox("Select a mascot:",
                          sorted(inventory_df["Mascot_Name"]))
    with st.form("rent_form"):
        cn, ph = st.columns(2)
        with cn: customer = st.text_input("Customer Name:")
        with ph: phone   = st.text_input("Contact Phone Number:")
        sd, ed = st.columns(2)
        with sd: sd_in = st.date_input("Start Date", value=datetime.today())
        with ed: ed_in = st.date_input("End Date",   value=datetime.today())
        submit = st.form_submit_button("📩 Submit Rental")

    if submit:
        if not customer:
            st.warning("Please enter a customer name.")
        elif ed_in < sd_in:
            st.warning("End date cannot be before start date.")
        else:
            sdt = datetime.combine(sd_in, datetime.min.time())
            edt = datetime.combine(ed_in, datetime.min.time())
            row = inventory_df.query("Mascot_Name==@choice").iloc[0]
            total = int(row.Quantity)
            used  = check_availability(rental_log_df, choice, sdt, edt)
            if used >= total:
                st.error(f"⚠️ All {total} are already booked.")
            else:
                conn = sqlite3.connect("rental_log.db")
                cur  = conn.cursor()
                cur.execute(
                    "INSERT INTO rentals (mascot_id,mascot_name,customer_name,contact_phone,start_date,end_date) VALUES (?,?,?,?,?,?)",
                    (int(row.ID), choice, customer, phone, sd_in, ed_in)
                )
                conn.commit(); conn.close()
                st.success(f"✅ Booked ({used+1}/{total})")
                st.experimental_rerun()

    # Mascot Details
    md = inventory_df.query("Mascot_Name==@choice").iloc[0]
    st.markdown("### 📋 Mascot Details")
    d1, d2 = st.columns(2)
    with d1:
        st.write(f"*Size:* {md.get('Size','N/A')}")
        st.write(f"*Weight:* {md.Weight_kg or 'N/A'} kg")
        st.write(f"*Height:* {md.Height_cm or 'N/A'}")
    with d2:
        st.write(f"*Quantity:* {int(md.Quantity)}")
        st.write(f"*Rent Price:* ${md.Rent_Price}")
        st.write(f"*Sale Price:* ${md.Sale_Price}")

    # Delete & Download
    st.markdown("---")
    dc, dl = st.columns(2)
    with dc:
        st.markdown("### 🗑️ Delete Rental")
        if rental_log_df.empty:
            st.info("No bookings.")
        else:
            opts = {
              f"{r.customer_name} - {r.mascot_name} ({r.start_date.date()}→{r.end_date.date()})":r.id
              for _,r in rental_log_df.iterrows()
            }
            sel = st.selectbox("Select booking to delete:", list(opts))
            if st.button("❌ Delete"):
                conn = sqlite3.connect("rental_log.db")
                sqlite3.connect("rental_log.db").cursor()\
                    .execute("DELETE FROM rentals WHERE id=?", (opts[sel],))
                conn.commit(); conn.close()
                st.success("Deleted.")
                st.experimental_rerun()
    with dl:
        st.markdown("### 📥 Download Log")
        if not rental_log_df.empty:
            csv = rental_log_df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv,
                               f"rental_log_{datetime.today().date()}.csv",
                               "text/csv")
