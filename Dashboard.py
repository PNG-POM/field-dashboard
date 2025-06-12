import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_javascript import st_javascript
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import schedule
import time
import threading
import socket
import json

st.set_page_config(page_title="Field Engineer Dashboard", layout="wide")

# === Config ===
FILE_PATH = "Combined Site Down Report.xlsx"
VISIT_LOG_PATH = "Visit_Log.csv"
PHOTO_UPLOAD_DIR = "Photos"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Load credentials from Streamlit secrets
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
DRIVE_FOLDER_ID = st.secrets["DRIVE_FOLDER_ID"]

os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)

# === Upload to Google Drive ===
def upload_to_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(FILE_PATH),
        'parents': [DRIVE_FOLDER_ID]
    }

    media = MediaFileUpload(FILE_PATH, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return True

# === Background Auto Upload Scheduler ===
def run_scheduler():
    schedule.every(60).minutes.do(upload_to_drive)
    while True:
        schedule.run_pending()
        time.sleep(10)

threading.Thread(target=run_scheduler, daemon=True).start()

# === Display Host IP for LAN Access ===
host_ip = socket.gethostbyname(socket.gethostname())
st.sidebar.info(f"🌐 LAN URL: http://{host_ip}:8501")

# === Login ===
user_type = st.sidebar.selectbox("Login as", ["General User", "Admin"])
password = st.sidebar.text_input("Password", type="password")

if user_type == "Admin" and password != "admin123":
    st.error("🔐 Incorrect password for Admin view")
    st.stop()

# === Load Data ===
@st.cache_data
def load_data():
    df = pd.read_excel(FILE_PATH, sheet_name="Summary")
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

df = load_data()

st.title("📡 Field Engineer Dashboard")

# === Filters ===
st.sidebar.header("🔍 Filters")
regions = st.sidebar.multiselect("Region", sorted(df["Region"].dropna().unique()), default=None)
rto = st.sidebar.multiselect("RTO", sorted(df["RTO"].dropna().unique()), default=None)
priority = st.sidebar.multiselect("Priority", sorted(df["Priority"].dropna().unique()), default=None)

filtered_df = df.copy()
if regions:
    filtered_df = filtered_df[filtered_df["Region"].isin(regions)]
if rto:
    filtered_df = filtered_df[filtered_df["RTO"].isin(rto)]
if priority:
    filtered_df = filtered_df[filtered_df["Priority"].isin(priority)]

st.subheader(f"Showing {len(filtered_df)} site(s)")
st.dataframe(filtered_df, use_container_width=True)

# === Select Site for TT/Visit ===
st.divider()
st.subheader("🛠 Create TT / Mark Visit")

site_options = filtered_df["Site ID"].dropna().unique().tolist()
selected_site = st.selectbox("Select Site ID", ["-- Select --"] + site_options)

if selected_site and selected_site != "-- Select --":
    contractor_name = st.text_input("FE/Contractor Name")
    phone_number = st.text_input("FE/Contractor Phone Number")
    site_info = filtered_df[filtered_df["Site ID"] == selected_site].iloc[0]
    site_name = site_info.get("Site Name", "")
    region = site_info.get("Region", "")
    rto_name = site_info.get("RTO", "")

    st.text_input("Site Name", value=site_name, disabled=True)
    st.text_input("Region", value=region, disabled=True)
    st.text_input("RTO Name", value=rto_name, disabled=True)

    coords = st_javascript("""await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
            (err) => resolve({ lat: "Not Available", lon: "Not Available" }),
            { enableHighAccuracy: true }
        );
    });""")

    latitude = coords.get("lat", "")
    longitude = coords.get("lon", "")

    st.text_input("Latitude", value=str(latitude), disabled=True)
    st.text_input("Longitude", value=str(longitude), disabled=True)

    auto_tt_no = f"TT-{selected_site}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    st.text_input("Auto-generated TT Number", value=auto_tt_no, disabled=True)

    remarks = st.text_area("Remarks / Action Taken")
    uploaded_photo = st.file_uploader("Upload Site Photo", type=["jpg", "jpeg", "png"])

    if st.button("✅ Submit Visit Record"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        photo_filename = ""

        if uploaded_photo:
            photo_ext = os.path.splitext(uploaded_photo.name)[1]
            photo_filename = f"{selected_site}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{photo_ext}"
            photo_path = os.path.join(PHOTO_UPLOAD_DIR, photo_filename)
            with open(photo_path, "wb") as f:
                f.write(uploaded_photo.getbuffer())

        log_entry = pd.DataFrame([[timestamp, selected_site, site_name, region, rto_name, contractor_name, phone_number, latitude, longitude, auto_tt_no, remarks, photo_filename]],
                                 columns=["Timestamp", "Site ID", "Site Name", "Region", "RTO Name", "Contractor Name", "Phone Number", "Latitude", "Longitude", "TT Number", "Remarks", "Photo"])

        try:
            if os.path.exists(VISIT_LOG_PATH):
                existing = pd.read_csv(VISIT_LOG_PATH, on_bad_lines='skip')
                combined = pd.concat([existing, log_entry], ignore_index=True)
                combined.to_csv(VISIT_LOG_PATH, index=False)
            else:
                log_entry.to_csv(VISIT_LOG_PATH, index=False)

            st.success("✅ Visit record submitted successfully!")
        except PermissionError:
            st.error("❌ Unable to write to Visit_Log.csv. Please close the file if it's open in another program.")

# === View Visit Logs (Admin Only) ===
if user_type == "Admin":
    st.divider()
    st.subheader("📋 Visit Log Summary")

    if os.path.exists(VISIT_LOG_PATH):
        try:
            log_df = pd.read_csv(VISIT_LOG_PATH, on_bad_lines='skip')
            st.dataframe(log_df.style.set_properties(**{
                'background-color': '#f9f9f9',
                'color': '#000000',
                'border-color': '#c1c1c1',
                'font-size': '14px'
            }), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Failed to load Visit Log: {e}")
    else:
        st.info("No visit records found yet.")
