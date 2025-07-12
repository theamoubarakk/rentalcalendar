import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import sqlite3

# ─── helper to format any NaN as “N/A” (with optional prefix/suffix) ───
def _fmt_val(val, prefix: str = "", suffix: str = "") -> str:
    if pd.notna(val):
        return f"{prefix}{val}{suffix}"
    return "N/A"

# ─── remove white-space and collapse all header margins ───
st.markdown(
    """
    <style>
      /* remove the big top/bottom padding around blocks */
      .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
      }
      /* collapse default gaps under hr, forms, etc */
      .css-1avcm0n,
      .css-18e3th9 {
        margin-bottom: 0.25rem !important;
      }
      /* pull all headings up a bit */
      .stMarkdown h1,
      .stMarkdown h2,
      .stMarkdown h3 {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
      }
      /* specifically nudge H3s further up */
      .stMarkdown h3 {
        margin-top: -1rem !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.set_page_config(layout="wide")

# ─── header: title on left, logo on right ───
hdr_left, hdr_right = st.columns([9, 1], gap="small")
with hdr_left:
    st.title("📅 Baba Jina Mascot Rental Calendar")
with hdr_right:
    st.image("logo.png", width=200)

# … all your existing data-loading and calendar code here …

# RIGHT: Form, then Mascot Details, then Delete/Download
with right_col:
    st.markdown("### 📌 New Rental Entry")
    # … your form code here …

    # ─── Mascot Details now using _fmt_val ───────────────────────────────
    md = inventory_df.query("Mascot_Name==@choice").iloc[0]
    st.markdown("### 📋 Mascot Details")

    det_c1, det_c2 = st.columns(2)
    with det_c1:
        size   = _fmt_val(md.get("Size"))
        weight = _fmt_val(md.get("Weight_kg"), suffix=" kg")
        height = _fmt_val(md.get("Height_cm"))

        st.write(f"*Size:* {size}")
        st.write(f"*Weight:* {weight}")
        st.write(f"*Height:* {height}")

    with det_c2:
        quantity   = _fmt_val(md.get("Quantity"))
        rent_price = _fmt_val(md.get("Rent_Price"), prefix="$")
        sale_price = _fmt_val(md.get("Sale_Price"), prefix="$")

        st.write(f"*Quantity:* {quantity}")
        st.write(f"*Rent Price:* {rent_price}")
        st.write(f"*Sale Price:* {sale_price}")

    # ─── Delete & Download (unchanged) ───────────────────────────────────
    st.markdown("---")
    # … your deletion & download button code here …
