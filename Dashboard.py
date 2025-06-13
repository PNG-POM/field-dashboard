import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_javascript import st_javascript
from PIL import Image
import pytz

# === Config ===
st.set_page_config(page_title="DigicelPNG Field Visit Login Portal", layout="wide")

st.markdown(
    """
    <style>
    footer {
        visibility: hidden;
    }
    .custom-footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        text-align: center;
        padding: 10px;
        background-color: rgba(255, 255, 255, 0.85);
        font-size: 14px;
        color: #333;
    }
    @media only screen and (max-width: 600px) {
        h1 { font-size: 24px !important; }
        .stTextInput > div > input, .stTextArea > div > textarea {
            font-size: 16px !important;
        }
        button[kind="primary"] {
            width: 100% !important;
            font-size: 18px !important;
        }
    }
    </style>
    <div class='custom-footer'>
        © 2025 Digicel PNG | Contact: support@digicelpng.com | Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
)

if "rerun_flag" in st.session_state:
    del st.session_state["rerun_flag"]
    st.experimental_rerun()

DATA_LOG_PATH = "Visit_Log.xlsx"
MASTER_DATA_PATH = "Master Data New.xlsx"
PHOTO_FOLDER = "Photos"
ADMIN_PASSWORD = "noc123"
os.makedirs(PHOTO_FOLDER, exist_ok=True)

# === Load Existing Data ===
def load_log():
    if os.path.exists(DATA_LOG_PATH):
        return pd.read_excel(DATA_LOG_PATH)
    else:
        return pd.DataFrame(columns=[
            "Timestamp", "FE/Contractor Name", "Phone Number", "Site ID", "RTO", "Region", "TT Number", "Remarks",
            "Latitude", "Longitude", "Photo", "Site Visit Time", "Activity Complete Time", "Status"
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
            rto = match.iloc[0]['RTO']
            region = match.iloc[0]['Region']
        else:
            rto = region = ""
    else:
        rto = region = ""
    now = datetime.now(pytz.timezone("Pacific/Port_Moresby")).strftime("%Y%m%d_%H%M%S")
    tt_number = f"TT_{site_id}_{now}"
    return rto, region, tt_number

# === Main ===
st.markdown("""
    <h1 style='text-align: center; color: #E50914;'>📍 DigicelPNG Field Visit Login Portal</h1>
    <hr style='border: 1px solid #E50914;'>
""", unsafe_allow_html=True)

admin_mode = st.sidebar.checkbox("🔐 Admin Login")

if admin_mode:
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password == ADMIN_PASSWORD:
        st.success("Access granted.")
        df = load_log()

        st.dataframe(df.drop(columns=["Photo"]), use_container_width=True)

        st.markdown("### 🖼️ Uploaded Photos (Session Only)")
        if "uploaded_photos" in st.session_state:
            for photo_data in st.session_state["uploaded_photos"]:
                st.image(photo_data["image"], caption=photo_data["caption"], use_column_width=True)

        st.download_button("🗕 Download Log", data=df.to_csv(index=False).encode(), file_name="Visit_Log.csv")
else:
    st.subheader("📌 Enter Visit Details")

    site_id = st.text_input("Site ID")
    if site_id:
        rto, region, tt_number = get_master_details(site_id)
        st.markdown(f"**RTO:** {rto}  ")
        st.markdown(f"**Region:** {region}  ")
        st.markdown(f"**TT Number:** {tt_number}")

        if st.button("🔓 Site Login"):
            login_time = datetime.now(pytz.timezone("Pacific/Port_Moresby")).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.clear()
            st.session_state["logged_in"] = True
            st.session_state["login_time"] = login_time
            st.session_state["site_id"] = site_id
            st.session_state["rto"] = rto
            st.session_state["region"] = region
            st.session_state["tt_number"] = tt_number
            st.success(f"✅ Site Login recorded at {login_time}")

        if st.session_state.get("logged_in") and st.session_state.get("site_id") == site_id:
            st.markdown("---")
            st.markdown("### 📸 Activity at Site")

            name = st.text_input("FE/Contractor Name", value="" if "name" not in st.session_state else st.session_state["name"])
            phone = st.text_input("Phone Number", value="" if "phone" not in st.session_state else st.session_state["phone"])
            remarks = st.text_area("Remarks", value="" if "remarks" not in st.session_state else st.session_state["remarks"])
            uploaded_photo = st.file_uploader("Upload Site Photo", type=["jpg", "jpeg", "png"])
            lat, lon = get_location()

            if st.button("🚪 Site Logout & Submit"):
                logout_time = datetime.now(pytz.timezone("Pacific/Port_Moresby")).strftime("%Y-%m-%d %H:%M:%S")
                photo_filename = "N/A"

                if uploaded_photo is not None:
                    photo_filename = f"{site_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    if "uploaded_photos" not in st.session_state:
                        st.session_state["uploaded_photos"] = []
                    st.session_state["uploaded_photos"].append({"image": uploaded_photo, "caption": f"{site_id} - {name}"})

                if site_id and name and phone:
                    df = load_log()
                    new_entry = pd.DataFrame([{ 
                        "Timestamp": logout_time,
                        "FE/Contractor Name": name,
                        "Phone Number": phone,
                        "Site ID": site_id,
                        "RTO": rto,
                        "Region": region,
                        "TT Number": tt_number,
                        "Remarks": remarks,
                        "Latitude": lat,
                        "Longitude": lon,
                        "Photo": photo_filename,
                        "Site Visit Time": st.session_state.get("login_time", ""),
                        "Activity Complete Time": logout_time,
                        "Status": "Complete"
                    }])

                    try:
                        df = pd.concat([df, new_entry], ignore_index=True)
                        save_log(df)
                        time_spent = datetime.strptime(logout_time, '%Y-%m-%d %H:%M:%S') - datetime.strptime(st.session_state['login_time'], '%Y-%m-%d %H:%M:%S')
                        st.success(f"✅ Visit logged successfully! Time spent: {time_spent}")
                    except Exception as e:
                        st.error(f"❌ Error during log saving: {e}")

                st.session_state.clear()
                st.experimental_rerun()
    else:
        st.info("Enter Site ID above to begin visit process.")
