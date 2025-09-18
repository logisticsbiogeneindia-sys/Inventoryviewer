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
st.set_page_config(page_title="Biogene India - Dispatch Viewer", layout="wide")

st.markdown(
    """
    <style>
        body {background-color: #f8f9fa; font-family: "Helvetica Neue", sans-serif;}
        .navbar {
            display: flex;
            align-items: center;
            background-color: #004a99;
            padding: 8px 16px;
            border-radius: 8px;
            color: white;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .navbar img {
            height: 50px;
            margin-right: 15px;
        }
        .navbar h1 {
            font-size: 24px;
            margin: 0;
            font-weight: 700;
        }
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #004a99; color: white; text-align: center;
            padding: 8px; font-size: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# Logo + Title Navbar
# -------------------------
logo_path = "logonew.png"
if os.path.exists(logo_path):
    logo_html = f'<img src="data:image/png;base64,{base64.b64encode(open(logo_path,"rb").read()).decode()}" alt="Logo">'
else:
    logo_html = ""

st.markdown(
    f"""
    <div class="navbar">
        {logo_html}
        <h1>🚚 Biogene India - Dispatch Viewer</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------
# File Load (Dispatches only)
# -------------------------
UPLOAD_PATH = "current_inventory.xlsx"
FILE_PATH = "Master-Stock Sheet Original.xlsx"
OWNER = "logisticsbiogeneindia-sys"
REPO = "Inventoryviewer"
BRANCH = "main"

TOKEN = st.secrets["GITHUB_TOKEN"]
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

if not os.path.exists(UPLOAD_PATH):
    url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{FILE_PATH.replace(' ', '%20')}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        xl = pd.ExcelFile(io.BytesIO(r.content))
    except Exception as e:
        st.error(f"❌ Error loading Excel from GitHub: {e}")
        st.stop()
else:
    xl = pd.ExcelFile(UPLOAD_PATH)

if "Dispatches" not in xl.sheet_names:
    st.error("❌ 'Dispatches' sheet not found in Excel file!")
    st.stop()

df = xl.parse("Dispatches")
st.success("✅ Dispatches Sheet Loaded Successfully!")

# -------------------------
# Column Detection
# -------------------------
date_col = find_column(df, ["Date", "Dispatch Date", "Invoice Date", "Order Date"])
customer_col = find_column(df, ["Customer Name", "Customer", "CustName"])
awb_col = find_column(df, ["AWB", "AWB Number", "Tracking Number", "Docket No"])

if not date_col or not customer_col or not awb_col:
    st.error("❌ Required columns not found (Date, Customer Name, AWB). Please check the Excel file.")
    st.stop()

# Ensure Date column is datetime
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

# -------------------------
# Search Filters
# -------------------------
st.subheader("🔍 Search Dispatches")

col1, col2, col3 = st.columns(3)
with col1:
    start_date = st.date_input("From Date")
with col2:
    end_date = st.date_input("To Date")
with col3:
    search_customer = st.text_input("Search by Customer Name").strip()

awb_search = st.text_input("Search by AWB Number").strip()

df_filtered = df.copy()

# Apply date range filter
if start_date and end_date:
    df_filtered = df_filtered[
        (df_filtered[date_col].dt.date >= start_date) & 
        (df_filtered[date_col].dt.date <= end_date)
    ]

# Apply customer filter
if search_customer:
    df_filtered = df_filtered[df_filtered[customer_col].astype(str).str.contains(search_customer, case=False, na=False)]

# Apply AWB filter
if awb_search:
    df_filtered = df_filtered[df_filtered[awb_col].astype(str).str.contains(awb_search, case=False, na=False)]

# -------------------------
# Show Results
# -------------------------
if df_filtered.empty:
    st.warning("⚠️ No matching records found.")
else:
    st.dataframe(df_filtered, use_container_width=True, height=600)

# -------------------------
# Footer
# -------------------------
st.markdown(
    """
    <div class="footer">
        © 2025 Biogene India | Created By Mohit Sharma
    </div>
    """,
    unsafe_allow_html=True
)
