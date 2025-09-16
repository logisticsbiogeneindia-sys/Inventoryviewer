import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import pytz
import base64

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
# Config & Styling
# -------------------------
st.set_page_config(page_title="Biogene India - Inventory Viewer", layout="wide")

# -------------------------
# Load Logo
# -------------------------
logo_path = "logonew.png"  # make sure logo is in your repo

if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")
else:
    logo_base64 = ""

# -------------------------
# Welcome Popup (only once)
# -------------------------
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if st.session_state.show_welcome and logo_base64:
    st.markdown(
        f"""
        <div style="position: fixed; top:0; left:0; width:100%; height:100%;
                    background-color: rgba(0,0,0,0.7); display:flex;
                    align-items:center; justify-content:center; z-index:9999;">
            <div style="background:white; padding:30px; border-radius:15px;
                        text-align:center; max-width:500px; box-shadow:0 4px 12px rgba(0,0,0,0.3);">
                <img src="data:image/png;base64,{logo_base64}" style="height:80px; margin-bottom:20px;">
                <h2 style="margin-bottom:10px; color:#004a99;">Welcome to Biogene India</h2>
                <p style="font-size:16px; color:#333;">
                    📦 Inventory Management System<br>
                    Use this portal to view, upload, and manage stock data.
                </p>
                <button onclick="window.parent.document.querySelector('iframe').contentWindow.location.reload()"
                        style="margin-top:15px; padding:10px 20px; border:none; border-radius:8px;
                               background:#004a99; color:white; font-size:16px; cursor:pointer;">
                    Continue
                </button>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# -------------------------
# Navbar (Logo + Title)
# -------------------------
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center;
                background-color: #004a99; padding: 12px; border-radius: 8px;">
        {'<img src="data:image/png;base64,'+logo_base64+'" style="height:55px; margin-right:15px;">' if logo_base64 else ""}
        <h1 style="color: white; font-size: 28px; margin: 0; font-weight: 700;">
            📦 Biogene India - Inventory Viewer
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

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
# Upload & Download Section
# -------------------------
if password == correct_password:
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        timezone = pytz.timezone("Asia/Kolkata")
        upload_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.upload_time = upload_time
        save_timestamp(upload_time)
        save_uploaded_filename(uploaded_file.name)
        st.sidebar.success(f"✅ File uploaded at {upload_time}")

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
# Load Excel
# -------------------------
if os.path.exists(UPLOAD_PATH):
    try:
        xl = pd.ExcelFile(UPLOAD_PATH)
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
        st.error(f"Error reading file: {e}")
else:
    st.info("📂 Please upload an Excel file from the sidebar.")

# -------------------------
# Footer
# -------------------------
st.markdown(
    """
    <hr style="margin-top: 50px; margin-bottom: 10px;">
    <div style="text-align: center; color: gray; font-size: 14px;">
        © 2025 Biogene India Pvt. Ltd. | Inventory Management System
    </div>
    """,
    unsafe_allow_html=True
)
