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
st.set_page_config(page_title="Biogene India - Inventory & Dispatch Viewer", layout="wide")

st.markdown("""
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
""", unsafe_allow_html=True)

# -------------------------
# Logo + Title Navbar
# -------------------------
logo_path = "logonew.png"
if os.path.exists(logo_path):
    logo_html = f'<img src="data:image/png;base64,{base64.b64encode(open(logo_path,"rb").read()).decode()}" alt="Logo">'
else:
    logo_html = ""

st.markdown(f"""
    <div class="navbar">
        {logo_html}
        <h1>🚚 Biogene India - Inventory & Dispatch Viewer</h1>
    </div>
""", unsafe_allow_html=True)

# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("⚙️ Settings")
inventory_type = st.sidebar.selectbox("Choose Inventory Type", ["Current Inventory", "Item Wise Current Inventory", "Dispatches"])
password = st.sidebar.text_input("Enter Password to Upload/Download File", type="password")
correct_password = "426344"
UPLOAD_PATH = "current_inventory.xlsx"
TIMESTAMP_PATH = "timestamp.txt"
FILENAME_PATH = "uploaded_filename.txt"

def save_timestamp(timestamp):
    with open(TIMESTAMP_PATH, "w") as f:
        f.write(timestamp)

def save_uploaded_filename(filename):
    with open(FILENAME_PATH, "w") as f:
        f.write(filename)

def load_uploaded_filename():
    if os.path.exists(FILENAME_PATH):
        with open(FILENAME_PATH, "r") as f:
            return f.read().strip()
    return "uploaded_inventory.xlsx"

# GitHub Config
OWNER = "logisticsbiogeneindia-sys"
REPO = "Inventoryviewer"
BRANCH = "main"
FILE_PATH = "Master-Stock Sheet Original.xlsx"
TOKEN = st.secrets["GITHUB_TOKEN"]
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

# -------------------------
# GitHub Timestamp (always used)
# -------------------------
def get_github_file_timestamp():
    try:
        url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/timestamp.txt"
        r = requests.get(url)
        if r.status_code == 200:
            return r.text.strip()
        else:
            return "No GitHub timestamp found."
    except Exception as e:
        return f"Error fetching timestamp: {e}"

github_timestamp = get_github_file_timestamp()
st.markdown(f"🕒 **Last Updated (from GitHub):** {github_timestamp}")

# -------------------------
# File Load (Dispatches only)
# -------------------------
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
# Column Detection (Dispatches)
# -------------------------
date_col = find_column(df, ["Date", "Dispatch Date", "Invoice Date", "Order Date"])
customer_col = find_column(df, ["Customer Name", "Customer", "CustName"])
awb_col = find_column(df, ["AWB", "AWB Number", "Tracking Number", "Docket No"])

if not date_col or not customer_col or not awb_col:
    st.error("❌ Required columns not found (Date, Customer Name, AWB). Please check the Excel file.")
    st.stop()

df[date_col] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)

# -------------------------
# Search Filters (Dispatches)
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

# Apply filters for dispatches
if start_date and end_date:
    df_filtered = df_filtered[
        (df_filtered[date_col].dt.date >= start_date) & 
        (df_filtered[date_col].dt.date <= end_date)
    ]

if search_customer:
    df_filtered = df_filtered[df_filtered[customer_col].astype(str).str.contains(search_customer, case=False, na=False)]

if awb_search:
    df_filtered = df_filtered[df_filtered[awb_col].astype(str).str.contains(awb_search, case=False, na=False)]

if not df_filtered.empty:
    df_filtered[date_col] = df_filtered[date_col].dt.strftime("%d/%m/%Y")

# -------------------------
# Show Results (Dispatches)
# -------------------------
if df_filtered.empty:
    st.warning("⚠️ No matching records found.")
else:
    st.dataframe(df_filtered, use_container_width=True, height=600)

# -------------------------
# Inventory Viewer (Current Inventory)
# -------------------------
allowed_sheets = [s for s in ["Current Inventory", "Item Wise Current Inventory", "Dispatches"] if s in xl.sheet_names]
if not allowed_sheets:
    st.error("❌ Neither 'Current Inventory' nor 'Item Wise Current Inventory' sheets found in file!")
else:
    sheet_name = inventory_type
    df = xl.parse(sheet_name)
    st.success(f"✅ **{sheet_name}** Loaded Successfully!")

    check_col = find_column(df, ["Check", "Location", "Status", "Type", "StockType"])
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Local", "🚚 Outstation", "📦 Other", "🔍 Search"])

    if check_col:
        check_vals = df[check_col].astype(str).str.strip().str.lower()
        with tab1:
            st.subheader("🏠 Local Inventory")
            st.dataframe(df[check_vals == "local"], use_container_width=True, height=600)
        with tab2:
            st.subheader("🚚 Outstation Inventory")
            st.dataframe(df[check_vals == "outstation"], use_container_width=True, height=600)
        with tab3:
            st.subheader("📦 Other Inventory")
            st.dataframe(df[~check_vals.isin(["local", "outstation"])], use_container_width=True, height=600)
    else:
        st.error("❌ Could not find a 'Check' column in this sheet.")

    with tab4:
        st.subheader("🔍 Search Inventory")
        search_sheet = st.selectbox("Select sheet to search", allowed_sheets, index=0)
        search_df = xl.parse(search_sheet)
        item_col = find_column(search_df, ["Item Code", "ItemCode", "SKU", "Product Code"])
        customer_col = find_column(search_df, ["Customer Name", "CustomerName", "Customer", "CustName"])
        brand_col = find_column(search_df, ["Brand", "BrandName", "Product Brand", "Company"])
        remarks_col = find_column(search_df, ["Remarks", "Remark", "Notes", "Comments"])

       col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            search_item = st.text_input("Search by Item Code").strip()
        with col2:
            search_customer = st.text_input("Search by Customer Name").strip()
        with col3:
            search_brand = st.text_input("Search by Brand").strip()
        with col4:
            search_remarks = st.text_input("Search by Remarks").strip()
        with col5:
            Search_ByDate = st.text_input("Search by Date").strip()

        df_filtered = search_df.copy()
        search_performed = False

        # Item Code Filter
        if search_item:
            search_performed = True
            if item_col:
                df_filtered = df_filtered[df_filtered[item_col].astype(str).str.contains(search_item, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find an Item Code column in this sheet.")
        
        # Customer Name Filter
        if search_customer:
            search_performed = True
            if customer_col:
                df_filtered = df_filtered[df_filtered[customer_col].astype(str).str.contains(search_customer, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find a Customer Name column in this sheet.")

        # Brand Filter
        if search_brand:
            search_performed = True
            if brand_col:
                df_filtered = df_filtered[df_filtered[brand_col].astype(str).str.contains(search_brand, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find a Brand column in this sheet.")
        
        # Remarks Filter
        if search_remarks:
            search_performed = True
            if remarks_col:
                df_filtered = df_filtered[df_filtered[remarks_col].astype(str).str.contains(search_remarks, case=False, regex=False, na=False)]
            else:
                st.error("❌ Could not find a Remarks column in this sheet.")
        
        # Date Filter (if specified)
        if Search_ByDate:
            search_performed = True
            df_filtered = df_filtered[df_filtered[date_col].astype(str).str.contains(Search_ByDate, case=False, na=False)]

        # Display Search Results
        if search_performed:
            if df_filtered.empty:
                st.warning("⚠️ No matching records found.")
            else:
                st.dataframe(df_filtered, use_container_width=True, height=600)

# -------------------------
# Footer
# -------------------------
st.markdown("""
    <div class="footer">
        © 2025 Biogene India | Created By Mohit Sharma
    </div>
""", unsafe_allow_html=True)

