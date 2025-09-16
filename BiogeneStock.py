import streamlit as st
import pandas as pd
import requests
import base64
import os
from datetime import datetime
import pytz

# -------------------------
# GitHub Config
# -------------------------
GITHUB_REPO = "logisticsbiogeneindia-sys/Inventoryviewer"
FILE_PATH = "Master-Stock Sheet Original.xlsx"
BRANCH = "main"
TOKEN = st.secrets["GITHUB_TOKEN"]

def load_excel_from_github():
    """Always load the latest Excel file from GitHub raw URL."""
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{FILE_PATH}"
    return pd.ExcelFile(url)

def upload_excel_to_github(file_bytes, filename=FILE_PATH):
    """Upload/replace Excel file in GitHub repo via API."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
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
# Your Existing Sidebar Upload
# -------------------------
st.sidebar.header("⚙️ Settings")
password = st.sidebar.text_input("Enter Password to Upload/Download File", type="password")
correct_password = "426344"

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
# Always load Excel from GitHub
# -------------------------
try:
    xl = load_excel_from_github()
    st.success(f"✅ Loaded {FILE_PATH} from GitHub")
except Exception as e:
    st.error(f"Error loading from GitHub: {e}")
