import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import pytz
import requests
import base64
import io

# -------------------------
# Helpers
# -------------------------
def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def find_column(df: pd.DataFrame, candidates: list) -> str | None:
    norm_map = {normalize(col): col for col in df.columns}
    for cand in candidates:
        key = normalize(cand)
        if key in norm_map:
            return norm_map[key]
    for cand in candidates:
        key = normalize(cand)
        for norm_col, orig in norm_map.items():
            if key in norm_col or norm_col in key:
                return orig
    return None

# -------------------------
# Config & Styling
# -------------------------
st.set_page_config(page_title="Biogene India - Inventory Viewer", layout="wide")

st.markdown(
    """
    <style>
        body {background-color: #f8f9fa; font-family: "Helvetica Neue", sans-serif;}
        .navbar {
            display: flex;
            align-items: center;
            background-color: #004a99;
            padding: 8px 16px;
            
        .footer {
            text-align: center;
            padding: 10px;
            margin-top: 20px;
            font-size: 12px;
            color: #888;
        }
    </style>
    """, unsafe_allow_html=True
)

# -------------------------
# About Section
# -------------------------
with st.expander("About Biogene India - Inventory Viewer"):
    st.markdown(
        """
        ### About Us
        Welcome to the Biogene India Inventory Viewer. This application is designed to provide a real-time, searchable view of our extensive inventory.

        Biogene India is a leading distributor of high-quality **biotech and life sciences products**. Our mission is to support scientific and research communities across India by ensuring the timely and efficient delivery of essential products.

        This tool helps our team and partners quickly find specific items by **Item Code**, **Customer Name**, and **Brand**, streamlining our workflow and enhancing customer service.

        ---
        **Contact Us**: [info@biogene-india.com](mailto:info@biogene-india.com)
        """
    )


# -------------------------
# UI & Logic
# -------------------------
st.title("📦 Biogene Inventory Viewer")

# File uploader section
uploaded_file = st.file_uploader("Upload Your Excel File", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.success("✅ File uploaded successfully!")

        st.subheader("Inventory Search")

        col1, col2, col3 = st.columns(3)
        with col1:
            search_item_code = st.text_input("Search by Item Code")
        with col2:
            search_customer = st.text_input("Search by Customer Name")
        with col3:
            search_brand = st.text_input("Search by Brand")
        
        search_remarks = st.text_input("Search by Remarks")

        df_filtered = df.copy()
        search_performed = False

        item_code_col = find_column(df, ["Item Code", "Material Code", "Product Code", "Item No", "Product ID", "Item ID"])
        customer_col = find_column(df, ["Customer Name", "Customer", "Client", "Distributor"])
        brand_col = find_column(df, ["Brand", "Company", "Manufacturer"])
        remarks_col = find_column(df, ["Remarks", "Notes", "Description", "Comments"])

        if search_item_code:
            search_performed = True
            if item_code_col:
                df_filtered = df_filtered[df_filtered[item_code_col].astype(str).str.contains(search_item_code, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find an Item Code column in this sheet.")
        if search_customer:
            search_performed = True
            if customer_col:
                df_filtered = df_filtered[df_filtered[customer_col].astype(str).str.contains(search_customer, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find a Customer Name column in this sheet.")
        if search_brand:
            search_performed = True
            if brand_col:
                df_filtered = df_filtered[df_filtered[brand_col].astype(str).str.contains(search_brand, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find a Brand column in this sheet.")
        if search_remarks:
            search_performed = True
            if remarks_col:
                df_filtered = df_filtered[df_filtered[remarks_col].astype(str).str.contains(search_remarks, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find a Remarks column in this sheet.")
        if search_performed:
            if df_filtered.empty:
                st.warning("No matching records found.")
            else:
                st.dataframe(df_filtered, use_container_width=True, height=600)

# -------------------------
# Footer
# -------------------------
st.markdown(
    """
    <div class="footer">
        © Biogene India. All Rights Reserved.
    </div>
    """,
    unsafe_allow_html=True
)
