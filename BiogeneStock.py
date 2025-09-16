import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import pytz
import requests
import base64

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
        .title-container {background-color: #004a99; padding: 10px; text-align: center; border-radius: 8px; color: white;}
        .title-container h1 {font-size: 28px; margin: 0; font-weight: 700;}
        .footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #004a99;
                 color: white; text-align: center; padding: 8px; font-size: 14px;}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# Logo + Title
# -------------------------
logo_path = "logonew.png"  # uploaded file
if os.path.exists(logo_path):
    st.image(logo_path, use_container_width=False, width=400)
st.markdown('<div class="title-container"><h1>📦 Biogene India - Inventory Viewer</h1></div>', unsafe_allow_html=True)

# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("⚙️ Settings")
inventory_type = st.sidebar.selectbox("Choose Inventory Type", ["Current Inventory", "Item Wise Current Inventory"])
password = st.sidebar.text_input("Enter Password to Upload/Download File", type="password")
correct_password = "426344"

UPLOAD_PATH = "current_inventory.xlsx"
TIMESTAMP_PATH = "timestamp.txt"
FILENAME_PATH = "uploaded_filename.txt"

def load_timestamp():
    if os.path.exists(TIMESTAMP_PATH):
        with open(TIMESTAMP_PATH, "r") as f:
            return f.read().strip()
    return "No upload yet."

def save_timestamp(timestamp):
    with open(TIMESTAMP_PATH, "w") as f:
        f.write(timestamp)

def load_uploaded_filename():
    if os.path.exists(FILENAME_PATH):
        with open(FILENAME_PATH, "r") as f:
            return f.read().strip()
    return "uploaded_inventory.xlsx"

def save_uploaded_filename(filename):
    with open(FILENAME_PATH, "w") as f:
        f.write(filename)

if 'upload_time' not in st.session_state:
    st.session_state.upload_time = load_timestamp()

st.markdown(f"🕒 **Last Updated At:** {st.session_state.upload_time}")

# -------------------------
# GitHub Config
# -------------------------
OWNER = "logisticsbiogeneindia-sys"
REPO = "Inventoryviewer"
BRANCH = "main"
FILE_PATH = "Master-Stock Sheet Original.xlsx"

TOKEN = st.secrets["GITHUB_TOKEN"]
headers = {"Authorization": f"token {TOKEN}"}

def check_github_auth():
    r = requests.get("https://api.github.com/user", headers=headers)
    if r.status_code == 200:
        st.sidebar.success(f"🔑 GitHub Auth OK: {r.json().get('login')}")
    else:
        st.sidebar.error(f"❌ GitHub Auth failed: {r.status_code}")
check_github_auth()

def push_to_github(local_file, commit_message="Update Excel file"):
    try:
        with open(local_file, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        payload = {"message": commit_message, "content": content, "branch": BRANCH}
        if sha:
            payload["sha"] = sha
        r = requests.put(url, headers=headers, json=payload)
        if r.status_code in [200, 201]:
            st.sidebar.success("✅ Excel file pushed to GitHub successfully!")
        else:
            st.sidebar.error(f"❌ GitHub push failed: {r.json()}")
    except Exception as e:
        st.sidebar.error(f"Error pushing file: {e}")

# -------------------------
# Upload & Download Section
# -------------------------
if password == correct_password:
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        timezone = pytz.timezone("Asia/Kolkata")
        upload_time = datetime.now(timezone).strftime("%d-%m-%Y %H:%M:%S")
        st.session_state.upload_time = upload_time
        save_timestamp(upload_time)
        save_uploaded_filename(uploaded_file.name)
        st.sidebar.success(f"✅ File uploaded at {upload_time}")
        push_to_github(UPLOAD_PATH, commit_message=f"Uploaded {uploaded_file.name}")

    if os.path.exists(UPLOAD_PATH):
        with open(UPLOAD_PATH, "rb") as f:
            st.sidebar.download_button(
                label="⬇️ Download Uploaded Excel File",
                data=f,
                file_name=load_uploaded_filename(),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    if password:
        st.sidebar.error("❌ Incorrect password!")

# -------------------------
# Load Excel (from GitHub if local missing)
# -------------------------
if not os.path.exists(UPLOAD_PATH):
    url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{FILE_PATH.replace(' ', '%20')}"
    try:
        xl = pd.ExcelFile(url)
    except Exception as e:
        st.error(f"❌ Error loading Excel from GitHub: {e}")
        st.stop()
else:
    xl = pd.ExcelFile(UPLOAD_PATH)

# -------------------------
# Allowed sheets
# -------------------------
allowed_sheets = [s for s in ["Current Inventory", "Item Wise Current Inventory"] if s in xl.sheet_names]

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
            st.dataframe(df[check_vals == "local"], use_container_width=True)
        with tab2:
            st.subheader("🚚 Outstation Inventory")
            st.dataframe(df[check_vals == "outstation"], use_container_width=True)
        with tab3:
            st.subheader("📦 Other Inventory")
            st.dataframe(df[~check_vals.isin(["local", "outstation"])], use_container_width=True)
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
        col1, col2, col3, col4 = st.columns(4)
        with col1: search_item = st.text_input("Search by Item Code").strip()
        with col2: search_customer = st.text_input("Search by Customer Name").strip()
        with col3: search_brand = st.text_input("Search by Brand").strip()
        with col4: search_remarks = st.text_input("Search by Remarks").strip()
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

