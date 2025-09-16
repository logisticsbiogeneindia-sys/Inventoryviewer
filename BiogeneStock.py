import streamlit as st
import pandas as pd
import requests
import base64
import os

# -------------------------
# App Config
# -------------------------
st.set_page_config(page_title="Biogene Inventory Viewer", layout="wide")

# -------------------------
# Load Logo
# -------------------------
logo_path = "logonew.png"  # uploaded logo file

with open(logo_path, "rb") as f:
    logo_base64 = base64.b64encode(f.read()).decode("utf-8")

# -------------------------
# Welcome Popup (only once)
# -------------------------
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if st.session_state.show_welcome:
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
                <button onclick="window.parent.document.querySelector('iframe').contentWindow.streamlitSend('close_popup')"
                        style="margin-top:15px; padding:10px 20px; border:none; border-radius:8px;
                               background:#004a99; color:white; font-size:16px; cursor:pointer;">
                    Continue
                </button>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Close popup handler
def close_popup():
    st.session_state.show_welcome = False

st.experimental_data_editor  # hack to allow JS event communication
st.on_event("close_popup", close_popup)

# -------------------------
# Header Navbar (Logo + Title)
# -------------------------
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center;
                background-color: #004a99; padding: 12px; border-radius: 8px;">
        <img src="data:image/png;base64,{logo_base64}" style="height:55px; margin-right:15px;">
        <h1 style="color: white; font-size: 28px; margin: 0; font-weight: 700;">
            📦 Biogene India - Inventory Viewer
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# -------------------------
# GitHub Config
# -------------------------
OWNER = "logisticsbiogeneindia-sys"
REPO = "Inventoryviewer"
BRANCH = "main"
FILE_PATH = "Master-Stock Sheet Original.xlsx"

TOKEN = st.secrets["GITHUB_TOKEN"]  # ✅ Save PAT in Streamlit Secrets
headers = {"Authorization": f"token {TOKEN}"}

# -------------------------
# GitHub Push Function
# -------------------------
def push_to_github(local_file, commit_message="Update Excel file"):
    try:
        with open(local_file, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None

        payload = {
            "message": commit_message,
            "content": content,
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha

        r = requests.put(url, headers=headers, json=payload)

        if r.status_code in [200, 201]:
            st.success("✅ Excel file pushed to GitHub successfully!")
        else:
            st.error(f"❌ GitHub push failed: {r.json()}")

    except Exception as e:
        st.error(f"Error pushing file: {e}")

# -------------------------
# Auth Check
# -------------------------
def check_github_auth():
    r = requests.get("https://api.github.com/user", headers=headers)
    if r.status_code == 200:
        st.success(f"🔑 Authenticated as {r.json().get('login')}")
    else:
        st.error(f"❌ Auth failed: {r.status_code} - {r.json()}")

check_github_auth()

# -------------------------
# File Upload
# -------------------------
st.subheader("📤 Upload Excel File")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
if uploaded_file is not None:
    temp_path = "uploaded.xlsx"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Load and display dataframe
    try:
        df = pd.read_excel(temp_path)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error reading Excel: {e}")

    # Push to GitHub
    if st.button("⬆️ Save & Push to GitHub"):
        push_to_github(temp_path, commit_message="New stock upload")

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
