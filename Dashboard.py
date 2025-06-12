import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_javascript import st_javascript
import matplotlib.pyplot as plt

# === Config ===
st.set_page_config(page_title="DigicelPNG Field Visit Login Portal", layout="wide")

st.image("https://raw.githubusercontent.com/PNG-POM/field-dashboard/main/banner.jpg", use_column_width=True)

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

DATA_LOG_PATH = "Visit_Log.xlsx"
MASTER_DATA_PATH = "Master Data New.xlsx"
ADMIN_PASSWORD = "noc123"

# === Load Existing Data ===
def load_log():
    if os.path.exists(DATA_LOG_PATH):
        return pd.read_excel(DATA_LOG_PATH)
    else:
        return pd.DataFrame(columns=[
            "Timestamp", "FE/Contractor Name", "Phone Number", "Site ID", "RTO", "Region", "TT Number", "Remarks", "Latitude", "Longitude", "Photo", "Site Visit Time", "Activity Complete Time", "Status"
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

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    tt_number = f"TT_{site_id}_{now}"
    return rto, region, tt_number

# === Main ===
st.markdown("""
    <h1 style='text-align: center; color: #E50914;'>📍 DigicelPNG Field Visit Login Portal</h1>
    <hr style='border: 1px solid #E50914;'>
""", unsafe_allow_html=True)

# --- Admin Toggle ---
admin_mode = st.sidebar.checkbox("🔐 Admin Login")

if admin_mode:
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password == ADMIN_PASSWORD:
        st.success("Access granted.")
        df = load_log()

        filter_date = st.date_input("📅 Filter by Date", value=datetime.now().date())
        filter_fe = st.text_input("🔍 Filter by FE/Contractor Name")
        filter_region = st.text_input("🌍 Filter by Region")

        filtered_df = df.copy()
        if filter_date:
            filtered_df['Timestamp'] = pd.to_datetime(filtered_df['Timestamp'], errors='coerce')
            filtered_df = filtered_df[filtered_df['Timestamp'].dt.date == filter_date]
        if filter_fe:
            filtered_df = filtered_df[filtered_df['FE/Contractor Name'].str.contains(filter_fe, case=False)]
        if filter_region:
            filtered_df = filtered_df[filtered_df['Region'].str.contains(filter_region, case=False)]

        st.dataframe(filtered_df, use_container_width=True)
        st.download_button("🗕️ Download Filtered Log", data=filtered_df.to_csv(index=False).encode(), file_name="Filtered_Visit_Log.csv")

        # === Chart Section ===
        st.subheader("📊 Visit Summary Charts")
        col1, col2 = st.columns(2)

        with col1:
            visits_by_region = df['Region'].value_counts()
            fig, ax = plt.subplots()
            visits_by_region.plot(kind='bar', ax=ax)
            ax.set_title("Visits by Region")
            ax.set_ylabel("Count")
            st.pyplot(fig)

        with col2:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            visits_by_day = df.groupby(df['Timestamp'].dt.date).size()
            fig2, ax2 = plt.subplots()
            visits_by_day.plot(kind='line', marker='o', ax=ax2)
            ax2.set_title("Visits Per Day")
            ax2.set_ylabel("Count")
            st.pyplot(fig2)
    else:
        st.error("Access denied.")
else:
    st.subheader("📌 Enter Visit Details")

    site_id = st.text_input("Site ID", key="site_id")
    if site_id:
        rto, region, tt_number = get_master_details(site_id)
        st.markdown(f"**RTO:** {rto}  ")
        st.markdown(f"**Region:** {region}  ")
        st.markdown(f"**TT Number:** {tt_number}")

        st.markdown("---")
        st.markdown("### 🚪 Site Login")

        with st.form("visit_form", clear_on_submit=True):
            name = st.text_input("FE/Contractor Name", key="name")
            phone = st.text_input("Phone Number", key="phone")
            remarks = st.text_area("Remarks", key="remarks")

            lat, lon = get_location()
            submit = st.form_submit_button("Site Login")

        if submit:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df = load_log()
            existing_entry = df[(df['Site ID'] == site_id) & (df['FE/Contractor Name'] == name) & (df['Status'] == "IN")]

            if existing_entry.empty:
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
                    "Photo": "N/A",
                    "Site Visit Time": timestamp,
                    "Activity Complete Time": "",
                    "Status": "IN"
                }])

                df = pd.concat([df, new_entry], ignore_index=True)
                save_log(df)

                st.success("✅ Site Login recorded!")
                st.experimental_rerun()
            else:
                idx = existing_entry.index[0]
                df.at[idx, "Activity Complete Time"] = timestamp
                df.at[idx, "Status"] = "OUT"

                site_visit_time = datetime.strptime(df.at[idx, "Site Visit Time"], "%Y-%m-%d %H:%M:%S")
                activity_complete_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                duration = activity_complete_time - site_visit_time

                save_log(df)
                st.success(f"📤 Site Logout Successful! Total time spent: {duration}")
                st.experimental_rerun()
    else:
        st.info("Enter Site ID above to begin visit process.")
