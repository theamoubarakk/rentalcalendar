import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io

# --- Configuration and Data Loading ---
st.set_page_config(layout="wide")

# This is the content you provided for rentals.csv
csv_data = """
ID,Picture,Mascot Name,Size,Kg,cm,pcs,Rent Price,Sale Price,"Status (Available, Rented, Reserved, Under Repair)"
1,,Big white bear ,3m,8.5,40*40*40,1,60,400,Available
2,,Pandas,3m,8.5,40*40*40,1,60,400,Available
3,,Santa,2.6m,7,40*40*40,1,60,400,Available
4,,Snowman,2.6m,7,40*40*40,1,60,400,Available
5,,Elf,2.6m,6.5,40*40*40,1,60,400,Available
6,,Bun red,2.6m,8,40*40*40,1,60,400,Available
7,,Bun grey,2.6m,8,40*40*40,1,60,400,Available
8,,Gorilla,3m,8,40*40*40,1,60,400,Available
9,,Labubu Pink,2.6m,8,40*40*40,1,60,400,Available
10,,Labubu Grey,2.6m,8,40*40*40,1,60,400,Available
11,,Labubu Brown,2.6m,8,40*40*40,1,60,400,Available
12,,Yellow Duck,2m,8,35*35*35,1,60,400,Available
13,,Minnie Pink,1.8m,0.3,,4,20,125,Available
14,,Mickey Mouse,1.8m,0.3,,4,20,125,Available
15,,Minnie Red,1.8m,0.3,,4,20,125,Available
16,,Moanna,1.8m,0.3,,2,20,125,Available
17,,Ours Brun,1.8m,0.3,,2,20,125,Available
18,,Oui Oui,1.8m,0.3,,2,20,125,Available
19,,Frog,1.8m,0.3,,2,20,125,Available
20,,Sheap,1.8m,0.3,,2,20,125,Available
21,,Batman,1.8m,0.3,,2,20,125,Available
22,,Superman,1.8m,0.3,,2,20,125,Available
23,,Ironman,1.8m,0.3,,2,20,125,Available
24,,Hulk,1.8m,0.3,,2,20,125,Available
25,,Capten America,1.8m,0.3,,2,20,125,Available
26,,Spiderman,1.8m,0.3,,2,20,125,Available
27,,Brown Monkey,1.8m,0.3,,2,20,125,Available
28,,LOL,1.8m,0.3,,2,20,125,Available
29,,LOL 2,1.8m,0.3,,2,20,125,Available
30,,LOL 3,1.8m,0.3,,2,20,125,Available
31,,Troll Boy,1.8m,0.3,,2,20,125,Available
32,,Troll Girl,1.8m,0.3,,2,20,125,Available
33,,Teady Bear,1.8m,0.3,,2,20,125,Available
34,,Chaperon Rouge,1.8m,0.3,,2,20,125,Available
35,,Peroquet,1.8m,0.3,,2,20,125,Available
36,,Heart,1.8m,0.3,,2,20,125,Available
37,,Pink Penter,1.8m,0.3,,2,20,125,Available
38,,Lady Bug,1.8m,0.3,,2,20,125,Available
39,,Baby Shark Pink,1.8m,0.3,,1,20,125,Available
40,,Baby Shark Blue,1.8m,0.3,,1,20,125,Available
41,,Baby Shark Yellow,1.8m,0.3,,1,20,125,Available
42,,Winnie the poo,1.8m,0.3,,2,20,125,Available
43,,Clown,1.8m,0.3,,2,20,125,Available
44,,Yellow Chick ,1.8m,0.3,,2,20,125,Available
45,,Ginger Bread,1.8m,0.3,,2,20,125,Available
46,,Sponge Bob,1.8m,0.3,,2,20,125,Available
47,,Tchoupi,1.8m,0.3,,2,20,125,Available
48,,Teletabies Red,1.8m,0.3,,1,20,125,Available
49,,Teletabies Yellow,1.8m,0.3,,1,20,125,Available
50,,Teletabies Green,1.8m,0.3,,1,20,125,Available
51,,Teletabies Blue ,1.8m,0.3,,1,20,125,Available
52,,Barney,1.8m,0.3,,2,20,125,Available
53,,Green Dinosaur,1.8m,0.3,,2,20,125,Available
54,,Charlotte Aux Fraises,1.8m,0.3,,2,20,125,Available
55,,Grey Elephant,1.8m,0.3,,2,20,125,Available
56,,Pandas,1.8m,0.3,,2,20,125,Available
57,,Cinderella,1.8m,0.3,,2,20,125,Available
58,,Belle,1.8m,0.3,,2,20,125,Available
59,,Sophia,1.8m,0.3,,2,20,125,Available
60,,Blanche Neige,1.8m,0.3,,2,20,125,Available
61,,Unicorn white,1.8m,0.3,,1,20,125,Available
62,,Unicorn pink,1.8m,0.3,,1,20,125,Available
63,,PJ Mask Red,1.8m,0.3,,1,20,125,Available
64,,PJ Mask Blue,1.8m,0.3,,1,20,125,Available
65,,PJ Mask Green,1.8m,0.3,,1,20,125,Available
66,,Donald Duck,1.8m,0.3,,2,20,125,Available
67,,Daisy,1.8m,0.3,,2,20,125,Available
68,,Michka,1.8m,0.3,,2,20,125,Available
69,,Macha,1.8m,0.3,,2,20,125,Available
70,,Smurfette,1.8m,0.3,,1,20,125,Available
71,,Brown Lion,1.8m,0.3,,2,20,125,Available
72,,Penguin,1.8m,0.3,,2,20,125,Available
73,,Paw Patrol : Rubble,1.8m,0.3,,1,20,125,Available
74,,Paw Patrol : Stella,1.8m,0.3,,1,20,125,Available
75,,Paw Patrol : Chase,1.8m,0.3,,1,20,125,Available
76,,Paw Patrol : Zuma,1.8m,0.3,,1,20,125,Available
77,,Paw Patrol : Rocky,1.8m,0.3,,1,20,125,Available
78,,Paw Patrol : Marshall,1.8m,0.3,,1,20,125,Available
79,,Paw Patrol : Ridle,1.8m,0.3,,1,20,125,Available
80,,Tom & Jerry,1.8m,0.3,,1,20,125,Available
81,,Tom & Jerry 2,1.8m,0.3,,1,20,125,Available
82,,Hello Kitty,1.8m,0.3,,2,20,125,Available
83,,Bee,1.8m,0.3,,1,20,125,Available
84,,Cow,1.8m,0.3,,1,20,125,Available
85,,Elf,1.8m,0.3,,2,20,125,Available
86,,Santa,1.8m,0.3,,2,20,125,Available
87,,Snowman,1.8m,0.3,,2,20,125,Available
88,,Rudolph,1.8m,0.3,,2,20,125,Available
89,,Lapin Rose,1.8m,0.3,,1,20,125,Available
90,,Lapin Blanc,1.8m,0.3,,1,20,125,Available
91,,Lapin Gris,1.8m,0.3,,2,20,125,Available
92,,Brown Horse,1.8m,0.3,,2,20,125,Available
93,,Smurf,1.8m,0.3,,1,20,125,Available
94,,Mario Cart,1.8m,0.3,,1,20,125,Available
95,,Luigi,1.8m,0.3,,1,20,125,Available
96,,Peppa Pig,1.8m,0.3,,1,20,125,Available
97,,Georges Pig,1.8m,0.3,,1,20,125,Available
98,,Mama Pig,1.8m,0.3,,1,20,125,Available
99,,Papa Big,1.8m,0.3,,1,20,125,Available
100,,Flower,1.8m,0.3,,2,20,125,Available
101,,Astronaut,1.8m,0.3,,2,20,125,Available
102,,Sponge Bob,1.8m,0.3,,2,20,125,Available
103,,Baby Boy,1.8m,0.3,,1,20,125,Available
104,,Baby Girl,1.8m,0.3,,1,20,125,Available
105,,Sonic,1.8m,0.3,,2,20,125,Available
106,,Coco Melon,1.8m,0.3,,2,20,125,Available
107,,Huggy Waggy,1.8m,0.3,,1,20,125,Available
108,,Kissy Missiy,1.8m,0.3,,1,20,125,Available
109,,Jay Jay,1.8m,0.3,,2,20,125,Available
110,,Sonic Red,1.8m,0.3,,2,20,125,Available
111,,Rider,1.8m,0.3,,2,20,125,Available
112,,Stitch Blue,1.8m,0.3,,2,20,125,Available
113,,Stitch Pink,1.8m,0.3,,2,20,125,Available
114,,Christmas Tree,1.8m,0.3,,2,20,125,Available
115,"Angry Birds: Yellow",1.8m,0.3,,1,20,125,Available
116,"Angry Birds: Red",1.8m,0.3,,1,20,125,Available
117,"Angry Birds: Blue",1.8m,0.3,,1,20,125,Available
118,"Angry Birds: Black",1.8m,0.3,,1,20,125,Available
119,,Green Dinosaur,1.8m,0.3,,2,20,125,Available
120,,Hot Dog,1.8m,0.3,,2,20,125,Available
121,,Dora,1.8m,0.3,,2,20,125,Available
122,,Lapin,3m,8.5,40*40*40,1,60,400,Available
123,,Minions,1.8m,0.3,,2,20,125,Available
124,,Pikabu,1.8m,0.3,,2,20,125,Available
125,,Big Brown Bear ,3m,8.5,40*40*40,1,60,400,Available
126,,Watermelon,1.8m,0.3,,2,20,125,Available
127,,Snowman,1.8m,0.3,,2,20,125,Available
128,,Olaf,1.8m,0.3,,1,20,125,Available
129,,Elsa Frozen,1.8m,0.3,,2,20,125,Available
130,,Dog,1.8m,0.3,,2,20,125,Available
131,,Black Monkey,1.8m,0.3,,2,20,125,Available
132,,Ninja Turtle,1.8m,0.3,,2,20,125,Available
133,,Ninja Turtle 2,1.8m,0.3,,2,20,125,Available
134,,Tiger,1.8m,0.3,,2,20,125,Available
135,,Strawberry,1.8m,0.3,,2,20,125,Available
136,,Anna Frozen ,1.8m,0.3,,2,20,125,Available
137,,Pumkin,1.8m,0.3,,2,20,125,Available
138,,Cupcake,1.8m,0.3,,2,20,125,Available
139,,Neon party silver,1.8m,0.3,,2,20,125,Available
140,,Neon party purple,1.8m,0.3,,2,20,125,Available
141,,Neon party gold,1.8m,0.3,,2,20,125,Available
"""

@st.cache_data
def load_and_clean_inventory():
    """
    Loads data from CSV, handles the BOM character, and cleans the data.
    """
    # --- KEY FIX: Use encoding='utf-8-sig' to handle the hidden BOM character ---
    df = pd.read_csv(io.StringIO(csv_data), encoding='utf-8-sig')
    
    # Rename columns for consistency and ease of use in the code
    df.rename(columns={
        'Mascot Name': 'Mascot_Name',
        'Kg': 'Weight_kg',
        'cm': 'Height_cm',
        'pcs': 'Quantity',
        'Rent Price': 'Rent_Price',
        'Sale Price': 'Sale_Price',
        'Status (Available, Rented, Reserved, Under Repair)': 'Status'
    }, inplace=True)
    
    # Clean up any leading/trailing whitespace from important text columns
    for col in ['Mascot_Name', 'Size', 'Status']:
        if col in df.columns:
            df[col] = df[col].str.strip()
    
    # Drop empty rows that might exist at the end of the file
    df.dropna(subset=['ID'], inplace=True)
    df = df[df['Mascot_Name'].notna() & (df['Mascot_Name'] != '')]
    
    return df

def load_rental_log():
    try:
        # For demonstration, we'll start with an empty log. In production, this would read a file.
        return pd.read_excel("rental_log.xlsx")
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Mascot_Name", "Start_Date", "End_Date"])

# --- Load Data ---
inventory_df = load_and_clean_inventory()
rental_log_df = load_rental_log()

# --- Main App ---
st.title("📅 Baba Jina Mascot Rental Calendar")

if inventory_df.empty:
    st.error("Could not load inventory data. Please check the source.")
    st.stop()

# --- Layout Definition ---
left_col, right_col = st.columns([3, 2], gap="large")

# ==============================================================================
# LEFT COLUMN: Calendar and its controls
# ==============================================================================
with left_col:
    st.markdown("### 🗓️ Monthly Calendar")
    # (Calendar code remains the same as it was working correctly)
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        mascot_list = ["All"] + sorted(inventory_df["Mascot_Name"].unique())
        selected_mascot = st.selectbox("Filter by Mascot:", mascot_list)
    with filter_col2:
        month_filter = st.date_input("Select Month:", value=datetime.today().replace(day=1))

    filtered_log = rental_log_df.copy()
    filtered_log["Start_Date"] = pd.to_datetime(filtered_log["Start_Date"], errors="coerce")
    filtered_log["End_Date"] = pd.to_datetime(filtered_log["End_Date"], errors="coerce")
    if selected_mascot != "All":
        filtered_log = filtered_log[filtered_log["Mascot_Name"] == selected_mascot]

    month_start = datetime(month_filter.year, month_filter.month, 1)
    last_day = calendar.monthrange(month_filter.year, month_filter.month)[1]
    month_end = datetime(month_filter.year, month_filter.month, last_day)
    date_range = pd.date_range(month_start, month_end)
    calendar_df = pd.DataFrame({"Date": date_range})

    def get_booking_status(date):
        booked = filtered_log[(filtered_log["Start_Date"] <= date) & (filtered_log["End_Date"] >= date)]
        if booked.empty:
            return "✅ Available"
        else:
            names = ", ".join(booked["Mascot_Name"].unique())
            return f"❌ {names}"

    calendar_df["Status"] = calendar_df["Date"].apply(get_booking_status)
    st.markdown("<hr style='margin-top: 0; margin-bottom: 1rem'>", unsafe_allow_html=True)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, day in enumerate(days):
        header_cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)
    for week in calendar.monthcalendar(month_filter.year, month_filter.month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    date = datetime(month_filter.year, month_filter.month, day)
                    status = calendar_df.loc[calendar_df["Date"] == date, "Status"].iloc[0]
                    is_booked = "❌" in status
                    bg_color = "#f9e5e5" if is_booked else "#e6ffea"
                    icon, *text_parts = status.split(" ", 1)
                    text = text_parts[0] if text_parts else ""
                    st.markdown(f"""
                        <div style='background-color:{bg_color}; border-radius:10px; padding:10px; text-align:center;
                                    box-shadow:0 1px 3px rgba(0,0,0,0.05); margin-bottom:8px; min-height:80px;
                                    display: flex; flex-direction: column; justify-content: flex-start;'>
                            <strong style='margin-bottom: 5px;'>{day}</strong>
                            <div style='font-size: 0.9em; word-wrap: break-word;'>{icon} {text}</div>
                        </div>""", unsafe_allow_html=True)

# ==============================================================================
# RIGHT COLUMN: All Forms
# ==============================================================================
with right_col:
    st.markdown("### 📌 New Rental Entry")

    with st.form("rental_form"):
        mascot_choice = st.selectbox("Select a mascot:", sorted(inventory_df["Mascot_Name"].unique()))
        start_date = st.date_input("Start Date", value=datetime.today())
        end_date = st.date_input("End Date", value=datetime.today())

        # --- ACCURATE DYNAMIC MASCOT DETAILS ---
        mascot_row = inventory_df[inventory_df["Mascot_Name"] == mascot_choice].iloc[0]
        
        # Prepare display strings, handling potential empty values gracefully
        size_display = mascot_row.get('Size', 'N/A')
        weight_display = f"{mascot_row['Weight_kg']} kg" if pd.notna(mascot_row.get('Weight_kg')) else 'N/A'
        height_display = mascot_row.get('Height_cm', 'N/A')
        quantity_display = int(mascot_row['Quantity']) if pd.notna(mascot_row.get('Quantity')) else 'N/A'
        rent_price_display = f"${int(mascot_row['Rent_Price'])}" if pd.notna(mascot_row.get('Rent_Price')) else 'N/A'
        sale_price_display = f"${int(mascot_row['Sale_Price'])}" if pd.notna(mascot_row.get('Sale_Price')) else 'N/A'
        status_display = mascot_row.get('Status', 'N/A')

        st.markdown("### 📋 Mascot Details")
        st.write(f"**Size:** {size_display}")
        st.write(f"**Weight:** {weight_display}")
        st.write(f"**Height:** {height_display}")
        st.write(f"**Quantity Available:** {quantity_display}")
        st.write(f"**Rent Price:** {rent_price_display}")
        st.write(f"**Sale Price:** {sale_price_display}")
        st.write(f"**Status:** {status_display}")
        # --- END OF DETAILS SECTION ---

        submitted = st.form_submit_button("📩 Submit Rental")

        if submitted:
            new_entry = pd.DataFrame([{"ID": mascot_row["ID"], "Mascot_Name": mascot_row["Mascot_Name"], "Start_Date": pd.to_datetime(start_date), "End_Date": pd.to_datetime(end_date)}])
            rental_log_df = pd.concat([rental_log_df, new_entry], ignore_index=True)
            rental_log_df.to_excel("rental_log.xlsx", index=False)
            st.success("✅ Rental submitted and logged!")
            st.rerun()

    # --- DELETE BOOKING SECTION ---
    st.markdown("---")
    st.markdown("### 🗑️ Delete Rental Booking")

    if rental_log_df.empty:
        st.info("No bookings to delete.")
    else:
        rental_log_df['display'] = rental_log_df.apply(lambda row: f"{row['Mascot_Name']} ({row['Start_Date'].strftime('%Y-%m-%d')} to {row['End_Date'].strftime('%Y-%m-%d')})", axis=1)
        booking_to_delete = st.selectbox("Select booking to delete:", rental_log_df['display'].unique())
        if st.button("❌ Delete Booking"):
            idx_to_delete = rental_log_df[rental_log_df['display'] == booking_to_delete].index
            rental_log_df = rental_log_df.drop(columns=['display'])
            if not idx_to_delete.empty:
                rental_log_df = rental_log_df.drop(idx_to_delete)
                rental_log_df.to_excel("rental_log.xlsx", index=False)
                st.success("🗑️ Booking deleted successfully.")
                st.rerun()
