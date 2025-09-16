import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from github import Github
import os
from datetime import datetime
import pytz

# GitHub config
REPO_OWNER = st.secrets["REPO_OWNER"]
REPO_NAME = st.secrets["REPO_NAME"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
FILE_PATH = "data/current_inventory.xlsx"

# -------------------------
# Load Excel from GitHub
# -------------------------
def load_excel_from_github():
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}"
    response = requests.get(url)
    response.raise_for_status()
    return pd.ExcelFile(BytesIO(response.content))

# -------------------------
# Upload Excel to GitHub
# -------------------------
def upload_to_github(uploaded_file):
    g = Github(GITHUB_TOKEN)
    repo = g.get_user(REPO_OWNER).get_repo(REPO_NAME)

    content = uploaded_file.getvalue()  # bytes
    try:
        existing = repo.get_contents(FILE_PATH)
        repo.update_file(
            existing.path,
            f"Update inventory {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            content,
            existing.sha
        )
        st.sidebar.success("✅ File updated on GitHub!")
    except Exception:
        repo.create_file(
            FILE_PATH,
            f"Create inventory {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            content
        )
        st.sidebar.success("✅ File created on GitHub!")

# -------------------------
# App logic
# -------------------------
password = st.sidebar.text_input("Enter Password to Upload/Download File", type="password")
correct_password = "426344"

if password == correct_password:
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    if uploaded_file is not None:
        upload_to_github(uploaded_file)

# Always load from GitHub
try:
    xl = load_excel_from_github()
    st.success("✅ File loaded from GitHub successfully!")
except Exception as e:
    st.error(f"Error loading file from GitHub: {e}")
