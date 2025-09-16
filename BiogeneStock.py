import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from github import Github
from datetime import datetime
import pytz

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Biogene India - Inventory Viewer", layout="wide")

# GitHub config (stored in Streamlit Secrets)
REPO_OWNER = st.secrets["REPO_OWNER"]
REPO_NAME = st.secrets["REPO_NAME"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
FILE_PATH = "Master-Stock Sheet Original.xlsx"  # Excel file in repo

# -------------------------
# Helpers
# -------------------------
def load_excel_from_github():
    """Fetch Excel file from GitHub (raw URL)."""
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH.replace(' ', '%20')}"
    response = requests.get(url)
    response.raise_for_status()
    return pd.ExcelFile(BytesIO(response.content))

def upload_to_github(uploaded_file):
    """Upload or update Excel file on GitHub repo."""
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
# STYLING
# -------------------------
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
# SIDEBAR (Password + Upload)
# -------------------------
st.sidebar.header("⚙️ Settings")
password = st.sidebar.text_input("Enter Password to Upload File", type="password")
correct_password = "426344"  # 🔑 Change this if needed

if password == correct_password:
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    if uploaded_file is not None:
        upload_to_github(uploaded_file)

# -------------------------
# MAIN APP
# -------------------------
try:
    xl = load_excel_from_github()
    st.success("✅ File loaded from GitHub successfully!")

    # Show available worksheets
    sheet_name = st.sidebar.selectbox("Choose Worksheet", xl.sheet_names)

    # Load selected worksheet
    df = xl.parse(sheet_name)
    st.subheader(f"📄 Sheet: {sheet_name}")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error loading file from GitHub: {e}")
