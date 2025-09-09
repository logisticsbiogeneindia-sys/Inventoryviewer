import streamlit as st
import pandas as pd
import os
from datetime import datetime  # Import datetime for timestamp

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
TIMESTAMP_PATH = "timestamp.txt"  # Path to store the timestamp

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

# Function to load the last uploaded timestamp from a file
def load_timestamp():
    if os.path.exists(TIMESTAMP_PATH):
        with open(TIMESTAMP_PATH, "r") as f:
            return f.read().strip()
    return "No upload yet."

# Function to save the timestamp to a file
def save_timestamp(timestamp):
    with open(TIMESTAMP_PATH, "w") as f:
        f.write(timestamp)

# Initialize session state variables
if 'upload_time' not in st.session_state:
    st.session_state.upload_time = load_timestamp()  # Load from file if exists

# Main content layout
col1, col2 = st.columns([2, 1])

# Always display the upload time at the front
with col1:
    st.subheader("📂 **Inventory Data Viewer**")

    # Display upload time, if the file was uploaded or replaced
    st.markdown(f"🕒 **Last Updated At:** {st.session_state.upload_time}")

    # Only show upload button if password is correct
    if password == correct_password:
        # File upload in the sidebar
        uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])

        # Save the uploaded file, replacing the old one
        if uploaded_file is not None:
            with open(UPLOAD_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Get the current date and time of upload
            upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.upload_time = upload_time
            save_timestamp(upload_time)  # Save the timestamp to the file
            st.sidebar.success(f"✅ File uploaded & replaced at {upload_time}!")

    else:
        if password:
            st.sidebar.error("❌ Incorrect password!")

    # File processing after upload
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
