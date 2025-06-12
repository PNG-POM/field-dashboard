import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

def upload_to_drive(file_path, folder_id):
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_authorized_user_info(creds_dict)

    service = build("drive", "v3", credentials=creds)
    file_metadata = {"name": file_path.split("/")[-1], "parents": [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()
    return uploaded_file.get("id")
