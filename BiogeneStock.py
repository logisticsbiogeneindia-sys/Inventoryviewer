import streamlit as st
import pandas as pd
import requests
import base64
import os
import re
from datetime import datetime
import pytz
import urllib.parse

# -------------------------
# Helpers
# -------------------------
def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def find_column(df: pd.DataFrame, candidates: list) -> str | None:
    """Find best matching column in df for candidate names."""
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
# GitHub Config
# -------------------------
GITHUB_REPO = "logisticsbiogeneindia-sys/Inventoryviewer"
FILE_PATH = "Master-Stock Sheet Original.xlsx"   # Excel filename in your repo
BRANCH = "main"
TOKEN = st.secrets["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"]  # stored in Streamlit Secrets

def load_excel_from_github():
    """Always load the latest Excel file from GitHub raw URL."""
    safe_file = urllib.parse.quote(FILE_PATH)
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{safe_file}"
    return pd.ExcelFile(url)

def upload_excel_to_github(file_bytes, filename=FILE_PATH):
    """Upload/replace Excel file in GitHub repo via API."""
    safe_file = urllib.parse.quote(filename)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{safe_file}"
    headers = {"Authorization": f"token {TOKEN}"}

    # Get current file SHA (needed for update)
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    message = f"Auto update Excel from Streamlit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    content = base64.b64encode(file_bytes).decode("utf-8")

    data = {
        "message": message,
        "content": content,
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha  # required for updating existing file

    r = requests.put(url, headers=headers, json=data)
    if r.status_code in [200, 201]:
        return True, f"✅ Successfully pushed {filename} to GitHub"
    else:
        return False, f"❌ GitHub push failed: {r.json()}"

# -------------------------
# Config & Styling
# -------------------------
st.set_page_config(page_title="Biogene India - Inventory Viewer", layout="wide")
st.markdown(
    """
    <style>
        body {background-color: #f8f9fa; font-family: "Helvetica Neue", sans-serif;}
        .title-container {background-color: #004a99; padding: 16px; text-align: center; border-radius: 8px; color: white;}
        .title-container h1 {font-size: 28px; margin: 0; font-weight: 700;}
    </style>
    """, unsafe_allow_html=True
)
st.markdown('<div class="title-container"><h1>📦 Biogene India - Inventory Viewer</h1></div>', unsafe_allow_html=True)

# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("⚙️ Settings")
inventory_type = st.sidebar.selectbox("Choose Inventory Type", ["Current Inventory", "Item Wise Current Inventory"])
password = st.sidebar.text_input("Enter Password to Upload/Download File", type="password")
correct_password = "426344"

# Upload & push to GitHub
if password == correct_password:
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    if uploaded_file is not None:
        file_bytes = uploaded_file.getbuffer()
        success, msg = upload_excel_to_github(file_bytes)
        if success:
            st.sidebar.success(msg)
        else:
            st.sidebar.error(msg)
else:
    if password:
        st.sidebar.error("❌ Incorrect password!")

# -------------------------
# Load Excel (always from GitHub)
# -------------------------
try:
    xl = load_excel_from_github()
    st.success(f"✅ Loaded {FILE_PATH} from GitHub")

    # --- Only allow these two sheets ---
    allowed_sheets = [s for s in ["Current Inventory", "Item Wise Current Inventory"] if s in xl.sheet_names]

    if not allowed_sheets:
        st.error("❌ Neither 'Current Inventory' nor 'Item Wise Current Inventory' sheets found in file!")
    else:
        # Load main sheet for tabs
        sheet_name = inventory_type
        df = xl.parse(sheet_name)
        st.success(f"✅ **{sheet_name}** Loaded Successfully!")

        # Detect 'Check' column
        check_col = find_column(df, ["Check", "Location", "Status", "Type", "StockType"])

        # Show 4 tabs always
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Local", "🚚 Outstation", "📦 Other", "🔍 Search"])

        # --- Local / Outstation / Other tabs ---
        if check_col:
            check_vals = df[check_col].astype(str).str.strip().str.lower()
            with tab1:
                st.subheader("🏠 Local Inventory")
                st.dataframe(df[check_vals == "local"], use_container_width=True)

            with tab2:
                st.subheader("🚚 Outstation Inventory")
                st.dataframe(df[check_vals == "outstation"], use_container_width=True)

            with tab3:
                st.subheader("📦 Other Inventory")
                st.dataframe(df[~check_vals.isin(["local", "outstation"])], use_container_width=True)
        else:
            st.error("❌ Could not find a 'Check' column in this sheet.")

        # --- Search tab ---
        with tab4:
            st.subheader("🔍 Search Inventory")

            # ✅ Restrict search only to allowed sheets
            search_sheet = st.selectbox("Select sheet to search", allowed_sheets, index=0)
            search_df = xl.parse(search_sheet)

            # Detect possible columns
            item_col = find_column(search_df, ["Item Code", "ItemCode", "SKU", "Product Code"])
            customer_col = find_column(search_df, ["Customer Name", "CustomerName", "Customer", "CustName"])
            brand_col = find_column(search_df, ["Brand", "BrandName", "Product Brand", "Company"])
            remarks_col = find_column(search_df, ["Remarks", "Remark", "Notes", "Comments"])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                search_item = st.text_input("Search by Item Code").strip()
            with col2:
                search_customer = st.text_input("Search by Customer Name").strip()
            with col3:
                search_brand = st.text_input("Search by Brand").strip()
            with col4:
                search_remarks = st.text_input("Search by Remarks").strip()

            df_filtered = search_df.copy()
            search_performed = False

            if search_item:
                search_performed = True
                if item_col:
                    df_filtered = df_filtered[df_filtered[item_col].astype(str).str.contains(search_item, case=False, na=False)]
                else:
                    st.error("❌ Could not find an Item Code column in this sheet.")

            if search_customer:
                search_performed = True
                if customer_col:
                    df_filtered = df_filtered[df_filtered[customer_col].astype(str).str.contains(search_customer, case=False, na=False)]
                else:
                    st.error("❌ Could not find a Customer Name column in this sheet.")

            if search_brand:
                search_performed = True
                if brand_col:
                    df_filtered = df_filtered[df_filtered[brand_col].astype(str).str.contains(search_brand, case=False, na=False)]
                else:
                    st.error("❌ Could not find a Brand column in this sheet.")

            if search_remarks:
                search_performed = True
                if remarks_col:
                    df_filtered = df_filtered[df_filtered[remarks_col].astype(str).str.contains(search_remarks, case=False, na=False)]
                else:
                    st.error("❌ Could not find a Remarks column in this sheet.")

            if search_performed:
                if df_filtered.empty:
                    st.warning("No matching records found.")
                else:
                    st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Error loading from GitHub: {e}")
