#!/usr/bin/env python3
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import cv2
import numpy as np
import glob

##########CALIBRATION CODE############

# You should replace these 3 lines with the output in calibration step
DIM=(1280, 720)
K=np.array([[457.4134104878147, 0.0, 642.3731712697281], [0.0, 455.5924425764764, 364.36867870129714], [0.0, 0.0, 1.0]])
D=np.array([[0.001687992320423369], [-0.09534188590203489], [0.22135838220525605], [-0.15951510014255257]])
def undistort(img_path):
    img = cv2.imread(img_path)
#     print(img_path)
    h,w = img.shape[:2]
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    output_image_path = '/home/ciroh-uwrlphoto/hydroPhotos/'+  img_path.split('Photo/')[1].split()[0] 
#     print(output_image_path)
    # Save the mask
    cv2.imwrite(output_image_path, undistorted_img)
    
    
images_directory = '/home/ciroh-uwrlphoto/lettucePhoto'
# Go through each chessboard image, one by one (this may take some time)
for file in glob.glob(os.path.join(images_directory, '*')):   
     # Undistort the image
    undistort(file)
    # The image path will be different, because the .split is specific to my path to take the date of the name 

############ UPLOAD TO GOOGLE DRIVE CODE #############
# Path to your service account key JSON file
SERVICE_ACCOUNT_FILE = '/home/ciroh-uwrlphoto/daisy22-service-account.json'

# Define the folder name and path
LOCAL_FOLDER_PATH = '/home/ciroh-uwrlphoto/hydroPhotos'
DRIVE_FOLDER_NAME = 'hydroponicsHillcrest'

folder_path = "/home/ciroh-uwrlphoto/hydroPhotos"
csv_file = "/home/ciroh-uwrlphoto/tracker.csv"
# Authenticate with the service account
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)

# Find the folder ID of 'hydroponicHillcrest' on Drive (create it if it doesn't exist)
def get_or_create_folder(service, folder_name):
    # Search for folder
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive',
                                   fields="files(id, name)").execute()
    items = results.get('files', [])

    if items:
        return items[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

# Step 2: List just the file names
def list_file_names_in_folder(folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    file_names = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            corpora='allDrives',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='nextPageToken, files(name)',
            pageToken=page_token
        ).execute()
        file_names.extend([f['name'] for f in response.get('files', [])])
        page_token = response.get('nextPageToken')
        if page_token is None:
            break

    return file_names

# Run
folder_name = 'hydroponicHillcrest'
folder_id = '18XXvHJSwe27ZpGpmPiM_wxbdKGeJA01z'
file_names = list_file_names_in_folder(folder_id)

# Print result
# for name in file_names:
#     print(name)
# Upload a single file to a folder
def upload_file(service, file_path, folder_id):
    file_name = os.path.basename(file_path)
    media = MediaFileUpload(file_path, resumable=True)

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

# Main logic

def upload_folder_to_drive(local_folder, drive_folder_name):
    folder_id = get_or_create_folder(service, drive_folder_name)

    for file_name in os.listdir(local_folder):
        file_path = os.path.join(local_folder, file_name)
        if os.path.isfile(file_path):
            if file_name not in file_names:
                print(f"Uploading {file_name}...")
                upload_file(service, file_path, folder_id)

    # Run it
upload_folder_to_drive(LOCAL_FOLDER_PATH, DRIVE_FOLDER_NAME)

