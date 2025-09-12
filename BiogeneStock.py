import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import pytz

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
password = st.sidebar.text_input("Enter Password to Upload File", type="password")
correct_password = "426344"

UPLOAD_PATH = "current_inventory.xlsx"
TIMESTAMP_PATH = "timestamp.txt"

def load_timestamp():
    if os.path.exists(TIMESTAMP_PATH):
        with open(TIMESTAMP_PATH, "r") as f:
            return f.read().strip()
    return "No upload yet."

def save_timestamp(timestamp):
    with open(TIMESTAMP_PATH, "w") as f:
        f.write(timestamp)

if 'upload_time' not in st.session_state:
    st.session_state.upload_time = load_timestamp()

st.markdown(f"🕒 **Last Updated At:** {st.session_state.upload_time}")

if password == correct_password:
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        timezone = pytz.timezone("Asia/Kolkata")
        upload_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.upload_time = upload_time
        save_timestamp(upload_time)
        st.sidebar.success(f"✅ File uploaded at {upload_time}")
else:
    if password:
        st.sidebar.error("❌ Incorrect password!")

# -------------------------
# Load Excel
# -------------------------
if os.path.exists(UPLOAD_PATH):
    try:
        xl = pd.ExcelFile(UPLOAD_PATH)

        # --- Load sheet based on dropdown ---
        sheet_name = "Current Inventory" if inventory_type == "Current Inventory" else "Item Wise Current Inventory"
        if sheet_name not in xl.sheet_names:
            st.error(f"❌ Sheet '{sheet_name}' not found in uploaded file!")
            df = None
        else:
            df = xl.parse(sheet_name)
            st.success(f"✅ **{sheet_name}** Loaded Successfully!")

        # --- Always load Item Wise sheet for search ---
        search_df = None
        if "Item Wise Current Inventory" in xl.sheet_names:
            search_df = xl.parse("Item Wise Current Inventory")

        # --- Detect 'Check' column in selected sheet ---
        if df is not None:
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

            # --- Search tab (always from Item Wise Current Inventory) ---
            with tab4:
                st.subheader("🔍 Search in Item Wise Current Inventory")
                if search_df is None:
                    st.error("❌ 'Item Wise Current Inventory' sheet not found in the uploaded file.")
                else:
                    item_col = find_column(search_df, ["Item Code", "ItemCode", "SKU", "Product Code"])
                    customer_col = find_column(search_df, ["Customer Name", "CustomerName", "Customer", "CustName"])

                    col1, col2 = st.columns(2)
                    with col1:
                        search_item = st.text_input("Search by Item Code").strip()
                    with col2:
                        search_customer = st.text_input("Search by Customer Name").strip()

                    df_filtered = search_df.copy()
                    search_performed = False

                    if search_item:
                        search_performed = True
                        if item_col:
                            df_filtered = df_filtered[df_filtered[item_col].astype(str).str.contains(search_item, case=False, na=False)]
                        else:
                            st.error("❌ Could not find an Item Code column in Item Wise sheet.")

                    if search_customer:
                        search_performed = True
                        if customer_col:
                            df_filtered = df_filtered[df_filtered[customer_col].astype(str).str.contains(search_customer, case=False, na=False)]
                        else:
                            st.error("❌ Could not find a Customer Name column in Item Wise sheet.")

                    if search_performed:
                        if df_filtered.empty:
                            st.warning("No matching records found.")
                        else:
                            st.dataframe(df_filtered, use_container_width=True)

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("📂 Please upload an Excel file from the sidebar.")
