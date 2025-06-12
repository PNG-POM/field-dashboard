from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

# Path of your report
REPORT_PATH = "Combined Site Down Report.xlsx"
FOLDER_ID = "1u9AI97zUYoE5ui-rRrG-EKw6ZW1lmRQy"  # Your Google Drive folder ID

# Step 1: Authenticate
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Opens a browser window for Google login (1st time only)

drive = GoogleDrive(gauth)

# Step 2: Create & upload the file
file = drive.CreateFile({'title': os.path.basename(REPORT_PATH), 'parents': [{'id': FOLDER_ID}]})
file.SetContentFile(REPORT_PATH)
file.Upload()

print("✅ Report uploaded to Google Drive successfully.")
