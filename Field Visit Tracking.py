import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from streamlit_javascript import st_javascript

# === Config ===
st.set_page_config(page_title="Field Visit Tracking", layout="wide")

DATA_LOG_PATH = "Visit_Log.xlsx"
MASTER_DATA_PATH = "Master Data New.xlsx"
PHOTO_FOLDER = "Photos"
ADMIN_PASSWORD = "noc123"

# Ensure photo folder exists
os.makedirs(PHOTO_FOLDER, exist_ok=True)

# === Load Existing Data ===
def load_log():
    if os.path.exists(DATA_LOG_PATH):
        return pd.read_excel(DATA_LOG_PATH)
    else:
        return pd.DataFrame(columns=[
            "Timestamp", "FE/Contractor Name", "Phone Number", "Site ID", "RTO", "Region", "TT Number", "Remarks", "Latitude", "Longitude", "Photo"
        ])

# === Save Data ===
def save_log(df):
    df.to_excel(DATA_LOG_PATH, index=False)

# === Auto-fetch Location ===
def get_location():
    try:
        loc = st_javascript(
            """
            async () => {
                return await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        (pos) => resolve({latitude: pos.coords.latitude, longitude: pos.coords.longitude}),
                        (err) => resolve({latitude: null, longitude: null})
                    );
                });
            }
            """
        )
        return loc.get("latitude"), loc.get("longitude")
    except:
        return None, None

# === Master Lookup ===
def get_master_details(site_id):
    if os.path.exists(MASTER_DATA_PATH):
        master_df = pd.read_excel(MASTER_DATA_PATH)
        match = master_df[master_df['Site ID'] == site_id]
        if not match.empty:
            return match.iloc[0]['RTO'], match.iloc[0]['Region'], match.iloc[0]['TT Number']
    return "", "", ""

# === Main ===
st.title("📋 Field Visit Tracking")

# --- Admin Toggle ---
admin_mode = st.sidebar.checkbox("🔐 Admin Login")

if admin_mode:
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password == ADMIN_PASSWORD:
        st.success("Access granted.")
        df = load_log()
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download Full Log", data=df.to_csv(index=False).encode(), file_name="Visit_Log.csv")
        with st.expander("📸 View Uploaded Photos"):
            photo_files = sorted(os.listdir(PHOTO_FOLDER))
            for file in photo_files:
                st.image(os.path.join(PHOTO_FOLDER, file), caption=file, use_column_width=True)
    else:
        st.error("Access denied.")
else:
    st.subheader("📌 Enter Visit Details")

    with st.form("visit_form"):
        site_id = st.text_input("Site ID")
        rto, region, tt_number = get_master_details(site_id)

        st.markdown(f"**RTO:** {rto}  ")
        st.markdown(f"**Region:** {region}  ")
        st.markdown(f"**TT Number:** {tt_number}")

        name = st.text_input("FE/Contractor Name")
        phone = st.text_input("Phone Number")
        remarks = st.text_area("Remarks")
        photo = st.file_uploader("Upload Site Photo", type=["jpg", "png", "jpeg"])

        lat, lon = get_location()
        submit = st.form_submit_button("Submit")

    if submit:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        photo_filename = ""
        if photo:
            photo_filename = f"{site_id}_{timestamp.replace(':', '').replace(' ', '_')}.jpg"
            image = Image.open(photo)
            image.save(os.path.join(PHOTO_FOLDER, photo_filename))

        new_entry = pd.DataFrame([{ 
            "Timestamp": timestamp,
            "FE/Contractor Name": name,
            "Phone Number": phone,
            "Site ID": site_id,
            "RTO": rto,
            "Region": region,
            "TT Number": tt_number,
            "Remarks": remarks,
            "Latitude": lat,
            "Longitude": lon,
            "Photo": photo_filename
        }])

        df = load_log()
        df = pd.concat([df, new_entry], ignore_index=True)
        save_log(df)
        st.success("✅ Visit logged successfully!")
