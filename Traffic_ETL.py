
#Importing
import urllib.request
import requests
import pandas as pd
import io

#--------------------------------------------------------------------------------------------------------------
#Request api to city of calgary webiste 

api_url = 'https://data.calgary.ca/resource/k7p9-kppz.csv'
response = requests.get(api_url)
if response.status_code == 200:
  data = io.StringIO(response.text)
  df = pd.read_csv(data)
  print("Data loaded successfully.")
else:
  print("Failed to get data")

#--------------------------------------------------------------------------------------------------------------
#Data transformation 

df[['Camera_Number', 'URL']] = df['camera_url'].str.extract(r'Camera (\d+) \((http[^\)]+)\)')
df[['longitude', 'latitude']] = df['point'].str.extract(r'POINT \(([^ ]+) ([^ ]+)\)', expand=True)
df['latitude'] = pd.to_numeric(df['latitude'])
df['longitude'] = pd.to_numeric(df['longitude'])
df.drop(columns=['camera_url','point'], inplace = True)
df['Camera_Number'] = df['Camera_Number'].astype(int)
df = df.sort_values(by='Camera_Number', ascending=True)
df.reset_index(drop=True, inplace=True)
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#Downloading the images and running YOLOV5

import os
import shutil
import urllib.request
import ssl
import pandas as pd

# Directories setup
images_dir = "/Users/mohamad/Desktop/Data_608/Data608_Project/images_downloaded"
yolo_output_dir = "/Users/mohamad/Desktop/Data_608/Data608_Project/images_detected"

# Ensure the directories exist
os.makedirs(images_dir, exist_ok=True)
os.makedirs(yolo_output_dir, exist_ok=True)

failed_downloads = []  # Keep track of failed downloads

# Disable SSL certificate verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


for i, row in df.iterrows():
    image_url = row['URL']
    image_name = f"image_{i}.jpg"
    local_img_file = os.path.join(images_dir, image_name)

    try:
        # Attempt to download and save the images
        with urllib.request.urlopen(image_url, context=ssl_context) as response, open(local_img_file, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except urllib.error.HTTPError as e:
        print(f"Failed to download {image_url}: {e.reason}")
        failed_downloads.append((image_url, e.code))
        continue  # Skip to the next image



# Run YOLOv5 detection
import subprocess
# Define YOLOv5 detection command
yolov5_command = f"python /Users/mohamad/Desktop/Data_608/Data608_Project/yolov5/detect.py --weights yolov5s.pt --img 1024 --conf 0.25 --source {images_dir} --name /Users/mohamad/Desktop/Data_608/Data608_Project/images_detected"

subprocess.run(yolov5_command, shell=True)

print("Failed downloads:", failed_downloads)

#--------------------------------------------------------------------------------------------------------------
#Extracing the data from YOLOV5

import os
import pandas as pd
import torch

def load_yolov5_model(model_type='s'):
    model_names = {
        's': 'yolov5s',
        'm': 'yolov5m',
        'l': 'yolov5l',
        'x': 'yolov5x'
    }

    if model_type not in model_names:
        raise ValueError(f"Invalid model type '{model_type}'. Use one of: {' '.join(model_names.keys())}")

    yolo_model = torch.hub.load('ultralytics/yolov5', model_names[model_type])

    return yolo_model

# Load YOLOv5 model
yolo_model = load_yolov5_model()

images_dir = "/Users/mohamad/Desktop/Data_608/Data608_Project/images_downloaded"

# Prepare a DataFrame 
all_detections = []

# Iterate over each image in the directory
for image_name in os.listdir(images_dir):
    local_img_file = os.path.join(images_dir, image_name)

    results = yolo_model(local_img_file)

    dt = results.pandas().xyxy[0]

    detection_counts = dt['name'].value_counts().reset_index()
    detection_counts.columns = ['name', 'count']

    detections_pivot = detection_counts.set_index('name').T.fillna(0).astype(int)

    camera_number = int(image_name.split('_')[-1].split('.')[0]) + 1
    detections_pivot['Camera Number'] = camera_number

    all_detections.append(detections_pivot)

all_detections_df = pd.concat(all_detections, ignore_index=True)


all_detections_df = all_detections_df.fillna(0)

cols = list(all_detections_df)
cols.insert(0, cols.pop(cols.index('Camera Number')))
all_detections_df = all_detections_df.loc[:, cols]

consolidated_detections_df = all_detections_df.groupby('Camera Number').sum().reset_index()

df_detections = consolidated_detections_df.filter(items=['Camera Number','car', 'truck','bus'])
final_detection_table = pd.merge(df_detections, df, how='inner', left_on ='Camera Number', right_on='Camera_Number')

#--------------------------------------------------------------------------------------------------------------------
#Adding time stamps to dataframe using timeAPI

timeapi_url = 'https://www.timeapi.io/api/Time/current/zone?timeZone=America/Edmonton'

response = requests.get(timeapi_url)
time_data = response.json()

current_date = time_data['date']
current_time = time_data['time']
current_dayofweek = time_data['dayOfWeek']
df_time =pd.DataFrame({
    'Current Date':[current_date],
    'Current Time':[current_time],
    'Day of Week' :[current_dayofweek]
})

final_detection_table = final_detection_table.assign(
        **{'Current Date': current_date, 'Current Time': current_time, 'Day of Week': current_dayofweek}
    )

final_detection_table

#Saving dataframe into a csv file 
final_detection_table.to_csv('Traffic_detection.csv', index=False)