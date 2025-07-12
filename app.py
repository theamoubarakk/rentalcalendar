import streamlit as st
import pandas as pd
import sqlite3
import calendar
from datetime import datetime

# ---- Page config ----
st.set_page_config(layout="wide", page_title="Baba Jina Mascot Rental Calendar")

# ---- Inventory loader (Excel) ----
@st.cache_data
def load_inventory(file_path="cleaned_rentals.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        st.error(f"Could not load inventory: {e}")
        return pd.DataFrame()
    df = df.rename(columns={
        "Mascot Name": "Mascot_Name",
        "Kg": "Weight_kg",
        "cm": "Height_cm",
        "pcs": "Quantity",
        "Rent Price": "Rent_Price",
        "Sale Price": "Sale_Price",
        "Status (Available, Rented, Reserved, Under Repair)": "Status"
    })
    df["Mascot_Name"] = df["Mascot_Name"].astype(str).str.strip()
    df.dropna(subset=["ID","Mascot_Name"], inplace=True)
    return df

# ---- SQLite setup ----
DB = "rental_log.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascot_id     INTEGER,
            mascot_name   TEXT    NOT NULL,
            customer_name TEXT    NOT NULL,
            customer_phone TEXT,
            start_date    TEXT    NOT NULL,
            end_date      TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@st.cache_data
def load_rental_log():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(
        "SELECT * FROM rentals",
        conn,
        parse_dates=["start_date","end_date"]
    )
    conn.close()
    return df

# ---- Init + Load ----
init_db()
inventory_df  = load_inventory()
rental_log_df = load_rental_log()

if inventory_df.empty:
    st.stop()

# ---- App header ----
st.title("📅 Baba Jina Mascot Rental Calendar")

# ---- Columns ----
left, right = st.columns([3,2], gap="large")

# ===== LEFT: Calendar =====
with left:
    st.markdown("### 🗓️ Monthly Calendar")
    c1, c2 = st.columns(2)
    with c1:
        mascots = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascots)
    with c2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    # filter log
    fl = rental_log_df.copy()
    if selected_mascot != "All":
        fl = fl[fl["mascot_name"] == selected_mascot]

    # build calendar df
    y, m = month_filter.year, month_filter.month
    start = datetime(y, m, 1)
    end   = datetime(y, m, calendar.monthrange(y, m)[1])
    days = pd.date_range(start, end)
    cal = pd.DataFrame({"Date": days})

    def status(d):
        b = fl[(fl["start_date"] <= d) & (fl["end_date"] >= d)]
        return (
            f"❌ {', '.join(b['mascot_name'].unique())}"
            if not b.empty else
            "✅ Available"
        )

    cal["Status"] = cal["Date"].apply(status)

    # render week grid
    hdr = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hdr_cols = st.columns(7)
    for i, h in enumerate(hdr):
        hdr_cols[i].markdown(f"**{h}**", unsafe_allow_html=True)

    for week in calendar.monthcalendar(y, m):
        row_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                row_cols[i].markdown("&nbsp;", unsafe_allow_html=True)
            else:
                dt = datetime(y, m, day)
                stt = cal.loc[cal["Date"] == dt, "Status"].iat[0]
                booked = stt.startswith("❌")
                bg = "#ffe6e6" if booked else "#e6ffea"
                icon, *txt = stt.split(" ", 1)
                detail = txt[0] if txt else "Available"
                row_cols[i].markdown(f"""
                    <div style="
                      background:{bg};
                      border-radius:8px;
                      padding:8px;
                      text-align:center;
                      box-shadow:0 1px 2px rgba(0,0,0,0.1);
                      min-height:70px;
                    ">
                      <strong>{day}</strong><br>
                      {icon} {detail}
                    </div>
                """, unsafe_allow_html=True)

# ===== RIGHT: Management =====
with right:
    # remove any extra top margin on the form
    st.markdown("""
      <style>
        section[data-testid="stForm"] {margin-top:0rem !important;}
      </style>
    """, unsafe_allow_html=True)

    # -- New Entry --
    st.markdown("### 📌 New Rental Entry")
    with st.form("new_rental"):
        mc    = st.selectbox("Mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        cname= st.text_input("Customer Name:")
        cphone=st.text_input("Customer Phone:")
        sd   = st.date_input("Start Date", value=datetime.today())
        ed   = st.date_input("End Date",   value=datetime.today())

        # show mascot details
        r = inventory_df[inventory_df["Mascot_Name"] == mc].iloc[0]
        def fmt(v,u=""): return (f"{v}{u}" if pd.notna(v) else "N/A")
        st.markdown("#### 📋 Mascot Details")
        st.write(f"• Size:   {fmt(r.get('Size',''))}")
        st.write(f"• Weight: {fmt(r.get('Weight_kg',None),' kg')}")
        st.write(f"• Height: {fmt(r.get('Height_cm',None),' cm')}")
        st.write(f"• Qty:    {fmt(r.get('Quantity',None))}")
        st.write(f"• Rent:   {fmt(r.get('Rent_Price',None))}")
        st.write(f"• Sale:   {fmt(r.get('Sale_Price',None))}")
        st.write(f"• Status: {r.get('Status','N/A')}")

        if st.form_submit_button("📩 Submit Rental"):
            if not cname.strip() or not cphone.strip():
                st.warning("Name & phone are required.")
            else:
                conn = sqlite3.connect(DB)
                cur  = conn.cursor()
                cur.execute(
                    "INSERT INTO rentals (mascot_id,mascot_name,customer_name,customer_phone,start_date,end_date) VALUES (?,?,?,?,?,?)",
                    (int(r["ID"]), mc, cname, cphone, sd.isoformat(), ed.isoformat())
                )
                conn.commit()
                conn.close()
                st.success("✅ Rental saved.")

                # ─────── Clear the cache and reload immediately ───────
                load_rental_log.clear()
                rental_log_df[:] = load_rental_log()

    st.markdown("---")

    # -- Delete Booking --
    st.markdown("### 🗑️ Delete Rental Booking")
    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        disp_map = {
            f"{x['customer_name']} | {x['customer_phone']} | {x['mascot_name']} "
            f"({x['start_date'].date()}→{x['end_date'].date()})": x["id"]
            for _, x in rental_log_df.iterrows()
        }
        choice = st.selectbox("Which booking?", list(disp_map.keys()))
        if st.button("❌ Delete Booking"):
            bid = disp_map[choice]
            conn = sqlite3.connect(DB)
            cur  = conn.cursor()
            cur.execute("DELETE FROM rentals WHERE id=?", (bid,))
            conn.commit()
            conn.close()
            st.success("🗑️ Deleted.")

            # ─────── Clear the cache and reload immediately ───────
            load_rental_log.clear()
            rental_log_df[:] = load_rental_log()

    st.markdown("---")

    # -- Download Report --
    st.markdown("### 📥 Download Report (CSV)")
    df = rental_log_df.copy()
    if selected_mascot != "All":
        df = df[df["mascot_name"] == selected_mascot]
    df = df[(df["start_date"] <= end) & (df["end_date"] >= start)]
    if df.empty:
        st.info("No bookings this month.")
    else:
        report = df[[
            "id","mascot_name","customer_name","customer_phone","start_date","end_date"
        ]].rename(columns={
            "id":"BookingID",
            "mascot_name":"Mascot",
            "customer_name":"Customer",
            "customer_phone":"Phone",
            "start_date":"Start",
            "end_date":"End"
        })
        csv = report.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            csv,
            file_name=f"bookings_{y}_{m:02d}.csv",
            mime="text/csv"
        )
