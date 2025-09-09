import streamlit as st
import pandas as pd
import os

# Config - Apply vibrant theme to the Streamlit app
st.set_page_config(page_title="Inventory Viewer", layout="wide", initial_sidebar_state="expanded")
st.title("📦 **Biogene-India Inventory Viewer**")

# Apply some custom styles
st.markdown(
    """
    <style>
        .css-1d391kg { 
            background-color: #FF6347 !important;
            color: white;
            font-size: 30px;
            font-weight: bold;
        }
        .stButton>button {
            background-color: #32CD32;
            color: white;
            font-size: 16px;
            border-radius: 10px;
        }
        .stDataFrame {
            border: 1px solid #32CD32;
            padding: 10px;
            border-radius: 8px;
        }
        .css-1v0mbdj {
            background-color: #FF6347;
            color: white;
            font-weight: bold;
        }
        /* Custom style for file uploader */
        .upload-section {
            position: relative;
            bottom: 0;
            left: 0;
            z-index: 1000;
            width: 100%;
            padding: 20px;
        }
    </style>
    """, unsafe_allow_html=True
)

# File paths
UPLOAD_PATH = "current_inventory.xlsx"
ITEM_WISE_UPLOAD_PATH = "item_wise_inventory.xlsx"

# Sidebar for inventory selection and file upload
st.sidebar.header("⚙️ **Settings**")
inventory_type = st.sidebar.selectbox(
    "Choose Inventory Type",
    ["Current Inventory", "Item Wise Current Inventory"],
    index=0
)

# Password input
password = st.sidebar.text_input("Enter Password to Upload File", type="password")

# Correct password for uploading
correct_password = "426344"

# Only show upload button if password is correct
if password == correct_password:
    # File upload in the sidebar
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    # Save the uploaded file, replacing the old one
    if uploaded_file is not None:
        with open(UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.success("✅ File uploaded & replaced!")
else:
    if password:
        st.sidebar.error("❌ Incorrect password!")

# Main content layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📂 **Inventory Data Viewer**")
    if os.path.exists(UPLOAD_PATH):
        try:
            xl = pd.ExcelFile(UPLOAD_PATH)

            if inventory_type == "Current Inventory":
                sheet_name = "Current Inventory"
                sheet_display_name = "Current Inventory"
            elif inventory_type == "Item Wise Current Inventory":
                sheet_name = "Item Wise Current Inventory"
                sheet_display_name = "Item Wise Current Inventory"

            if sheet_name in xl.sheet_names:
                df = xl.parse(sheet_name)
                st.success(f"✅ **{sheet_display_name}** Loaded Successfully!")

                # Check if 'Check' column exists
                if "Check" not in df.columns:
                    st.error("❌ 'Check' column not found in the sheet!")
                else:
                    # Split data based on the "Check" column
                    df_local = df[df["Check"].str.lower() == "local"]
                    df_outstation = df[df["Check"].str.lower() == "outstation"]
                    df_rest = df[~df["Check"].str.lower().isin(["local", "outstation"])]

                    # Show in tabs
                    tab1, tab2, tab3 = st.tabs(["🏠 **Local**", "🚚 **Outstation**", "📦 **Other/OnStock**"])

                    with tab1:
                        st.subheader("🏠 **Local Inventory**")
                        st.dataframe(df_local, use_container_width=True)

                    with tab2:
                        st.subheader("🚚 **Outstation Inventory**")
                        st.dataframe(df_outstation, use_container_width=True)

                    with tab3:
                        st.subheader("📦 **Rest Inventory**")
                        st.dataframe(df_rest, use_container_width=True)

            else:
                st.error(f"❌ **'{sheet_display_name}'** sheet not found in uploaded file!")

        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
    else:
        st.info("📂 **Please upload an Excel file from the sidebar.**")
