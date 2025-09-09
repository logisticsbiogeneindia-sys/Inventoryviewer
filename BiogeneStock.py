import streamlit as st
import pandas as pd
import os

# Config
st.set_page_config(page_title="Inventory Viewer", layout="wide")
st.title("📦 Biogene-India Inventory Viewer")

UPLOAD_PATH = "current_inventory.xlsx"

# Sidebar upload
st.sidebar.header("⚙️ Settings")
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])

# Save new file, replace old one
if uploaded_file is not None:
    with open(UPLOAD_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("✅ File uploaded & replaced!")

# Load data if available
if os.path.exists(UPLOAD_PATH):
    try:
        xl = pd.ExcelFile(UPLOAD_PATH)
        if "Current Inventory" in xl.sheet_names:
            df = xl.parse("Current Inventory")

            st.success("✅ Current Inventory Loaded Successfully!")

            if "Check" not in df.columns:
                st.error("❌ 'Check' column not found in the sheet!")
            else:
                # Split data
                df_local = df[df["Check"].str.lower() == "local"]
                df_outstation = df[df["Check"].str.lower() == "outstation"]
                df_rest = df[~df["Check"].str.lower().isin(["local", "outstation"])]

                # Show in tabs
                tab1, tab2, tab3 = st.tabs(["🏠 Local", "🚚 Outstation", "📦 Other/OnStock"])

                with tab1:
                    st.subheader("🏠 Local Inventory")
                    st.dataframe(df_local, use_container_width=True)

                with tab2:
                    st.subheader("🚚 Outstation Inventory")
                    st.dataframe(df_outstation, use_container_width=True)

                with tab3:
                    st.subheader("📦 Rest Inventory")
                    st.dataframe(df_rest, use_container_width=True)

        else:
            st.error("❌ 'Current Inventory' sheet not found in uploaded file!")

    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
else:
    st.info("📂 Please upload an Excel file from the sidebar.")
