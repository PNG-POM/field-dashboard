import streamlit as st
import pandas as pd
import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === Page Config ===
st.set_page_config(page_title="Site Down Report", layout="centered")
st.title("📋 Combined Site Down Report Dashboard")

# === Report File Path ===
REPORT_PATH = "Combined Site Down Report.xlsx"

# === Load Report Preview ===
if os.path.exists(REPORT_PATH):
    df = pd.read_excel(REPORT_PATH)
    st.dataframe(df)
else:
    st.error("❌ Report file not found.")

# === Upload Function ===
def upload_to_drive(file_path, folder_id):
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict)
    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return uploaded_file.get("id")

# === Upload Button ===
if st.button("📤 Upload to Google Drive"):
    if os.path.exists(REPORT_PATH):
        try:
            file_id = upload_to_drive(REPORT_PATH, st.secrets["DRIVE_FOLDER_ID"])
            st.success(f"✅ Uploaded successfully to Drive (File ID: {file_id})")
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")
    else:
        st.warning("⚠️ Report file not found.")
