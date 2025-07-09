# ---- Layout: Calendar Grid + Rental Form ----
left, right = st.columns([3, 2], gap="small")

with left:
    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("&nbsp;", unsafe_allow_html=True)
            else:
                date = datetime(month_filter.year, month_filter.month, day)
                status = calendar_df[calendar_df["Date"] == date]["Status"].values[0]
                is_today = date.date() == datetime.today().date()
                bold = "**" if is_today else ""
                cols[i].markdown(f"{bold}{calendar.day_name[i]} {day}{bold}\n{status}")

# 🚀 Put "New Rental Entry" high up, no padding at all
with right:
    st.markdown(
        """
        <style>
        div[data-testid="column"] div:has(div[data-testid="stVerticalBlock"]) {
            padding-top: 0rem !important;
            margin-top: 0rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📌 New Rental Entry")

    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", inventory_df["Mascot_Name"].unique())
        start_date = st.date_input("Start Date", value=datetime.today())
        end_date = st.date_input("End Date", value=datetime.today())

        mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]

        weight_display = "N/A" if pd.isna(mascot_row["Weight_kg"]) else f"{mascot_row['Weight_kg']} kg"
        height_display = "N/A" if pd.isna(mascot_row["Height_cm"]) else f"{mascot_row['Height_cm']} cm"

        st.markdown("### 📋 Mascot Details")
        st.write(f"*Size:* {mascot_row['Size']}")
        st.write(f"*Weight:* {weight_display}")
        st.write(f"*Height:* {height_display}")
        st.write(f"*Quantity Available:* {mascot_row['Quantity']}")
        st.write(f"*Rent Price:* ${mascot_row['Rent_Price']}")
        st.write(f"*Sale Price:* ${mascot_row['Sale_Price']}")
        st.write(f"*Status:* {mascot_row['Status']}")

        submitted = st.form_submit_button("📩 Submit Rental")
        if submitted:
            new_entry = pd.DataFrame([{
                "ID": mascot_row["ID"],
                "Mascot_Name": mascot_row["Mascot_Name"],
                "Start_Date": pd.to_datetime(start_date),
                "End_Date": pd.to_datetime(end_date)
            }])
            rental_log_df = pd.concat([rental_log_df, new_entry], ignore_index=True)
            rental_log_df.to_excel("rental_log.xlsx", index=False)
            st.success("✅ Rental submitted and logged!")
            st.rerun()

    # ---- Delete Booking ----
    st.markdown("---")
    st.markdown("### 🗑️ Delete Rental Booking")

    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        delete_mascot = st.selectbox("Select a mascot to delete:", rental_log_df["Mascot_Name"].unique())
        matching = rental_log_df[rental_log_df["Mascot_Name"] == delete_mascot]
        delete_dates = matching.apply(lambda row: f"{row['Start_Date'].date()} to {row['End_Date'].date()}", axis=1)
        selected_range = st.selectbox("Select booking to delete:", delete_dates)

        if st.button("❌ Delete Booking"):
            idx_to_delete = matching[delete_dates == selected_range].index
            if not idx_to_delete.empty:
                rental_log_df = rental_log_df.drop(idx_to_delete)
                rental_log_df.to_excel("rental_log.xlsx", index=False)
                st.success("🗑️ Booking deleted successfully.")
                st.rerun()
