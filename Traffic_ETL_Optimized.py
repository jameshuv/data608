import os
import pandas as pd
import requests
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
import torch
from io import StringIO
import time 
from multiprocessing import Pool

start_time = time.time()


API_URL = 'https://data.calgary.ca/resource/k7p9-kppz.csv'
IMAGES_DIR = "/Users/mohamad/Desktop/Data_608/Data608_Project/images_downloaded"
YOLO_OUTPUT_DIR = "/Users/mohamad/Desktop/Data_608/Data608_Project/images_detected"
TIMEAPI_URL = 'https://www.timeapi.io/api/Time/current/zone?timeZone=America/Edmonton'


os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(YOLO_OUTPUT_DIR, exist_ok=True)

def get_data_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from {url}: {e}")
        return None

# Request data from API
data = get_data_from_url(API_URL)
if data:
    df = pd.read_csv(StringIO(data))
    print("Data loaded successfully.")
else:
    print("Failed to get data")

# Data transformation
df[['Camera_Number', 'URL']] = df['camera_url'].str.extract(r'Camera (\d+) \((http[^\)]+)\)')
df[['longitude', 'latitude']] = df['point'].str.extract(r'POINT \(([^ ]+) ([^ ]+)\)', expand=True)
df[['latitude', 'longitude']] = df[['latitude', 'longitude']].apply(pd.to_numeric)
df.drop(columns=['camera_url', 'point'], inplace=True)
df['Camera_Number'] = df['Camera_Number'].astype(int)
df = df.sort_values(by='Camera_Number').reset_index(drop=True)

failed_downloads = []

# Disable SSL certificate verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

#define function to download images
def download_images(image_url, images_dir):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            #extract filename from URL
            filename = os.path.basename(image_url)
            
            #save image to output directory
            with open(os.path.join(images_dir, filename), 'wb') as f:
                f.write(response.content)
            print(f"Downloaded {filename}")
        else:
            print(f"Failed to download image from {image_url}")
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")

#utilize multiprocessing to download images
if __name__ == "__main__":
    #define the list of image URLs
    image_urls = df['URL']
    
    #define the number of CPU processors
    num_processes = os.cpu_count()
    
    #download the images
    with Pool(processes=num_processes) as pool:
        pool.starmap(download_images, [(url, images_dir) for url in image_urls])


# Load YOLOv5
yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')


all_detections = []

for image_name in os.listdir(IMAGES_DIR):
    local_img_file = os.path.join(IMAGES_DIR, image_name)
    results = yolo_model(local_img_file)
    detections = results.pandas().xyxy[0]['name'].value_counts().reset_index()
    detections.columns = ['name', 'count']
    detections_pivot = detections.set_index('name').T.fillna(0).astype(int)
    camera_number = int(image_name.split('_')[-1].split('.')[0]) + 1
    detections_pivot['Camera Number'] = camera_number
    all_detections.append(detections_pivot)

all_detections_df = pd.concat(all_detections, ignore_index=True).fillna(0)


consolidated_detections_df = all_detections_df.groupby('Camera Number').sum().reset_index()
df_detections = consolidated_detections_df.filter(items=['Camera Number', 'car', 'truck', 'bus'])
final_detection_table = pd.merge(df_detections, df, how='inner', left_on='Camera Number', right_on='Camera_Number')

# Fetch time data from API
try:
    response = requests.get(TIMEAPI_URL)
    response.raise_for_status()
    time_data = response.json()
    current_date, current_time, current_dayofweek = time_data['date'], time_data['time'], time_data['dayOfWeek']
    final_detection_table['Current Date'] = current_date
    final_detection_table['Current Time'] = current_time
    final_detection_table['Day of Week'] = current_dayofweek
except requests.exceptions.RequestException as e:
    print(f"Failed to fetch time data from {TIMEAPI_URL}: {e}")

# Save dataframe into a csv file
final_detection_table.to_csv('Traffic_detection.csv', index=False)


end_time = time.time()
execution_time = end_time - start_time
print(f"Execution time:{execution_time} seconds")
