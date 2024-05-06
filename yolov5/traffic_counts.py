#YOLOv5 traffic counts
#---
#Script to count the traffic at each intersection in the city of Calgary using the YOLOv5 object recognition model

#import libraries
import urllib.request
import requests
import pandas as pd
import io
import os
import shutil
import ssl
import torch
import subprocess
from multiprocessing import Pool
import re
from datetime import datetime
import pytz


#Define global variables
#---
#setup directories
images_dir = "/usr/src/calgary_traffic/yolov5/images"


#Downloading intersection images (via city of Calgary API)
#---
#get the current datetime
current_datetime = datetime.now(pytz.timezone('America/Edmonton')).strftime("%Y-%m-%d_%H-%M")

#create API request
api_url = 'https://data.calgary.ca/resource/k7p9-kppz.csv'
response = requests.get(api_url)
if response.status_code == 200:
    data = io.StringIO(response.text)
    df = pd.read_csv(data)
    print("Data loaded successfully.")
else:
    print("Failed to get data")

#data frame transformation 
df[['Camera_Number', 'URL']] = df['camera_url'].str.extract(r'Camera (\d+) \((http[^\)]+)\)')
df[['longitude', 'latitude']] = df['point'].str.extract(r'POINT \(([^ ]+) ([^ ]+)\)', expand=True)
df['latitude'] = pd.to_numeric(df['latitude'])
df['longitude'] = pd.to_numeric(df['longitude'])
df.drop(columns=['camera_url','point'], inplace = True)
df['Camera_Number'] = df['Camera_Number'].astype(int)
df = df.sort_values(by='Camera_Number', ascending=True)
df.reset_index(drop=True, inplace=True)

#disable SSL certificate verification
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


#Object detection using YOLOv5 to count traffic
#---
#define a function to load the YOLOv5 model
def load_yolov5_model(model_type='s'): #default model is small
    model_names = {
        's': 'yolov5s',
        'm': 'yolov5m',
        'l': 'yolov5l',
        'x': 'yolov5x'
    }
    
    if model_type not in model_names:
        raise ValueError(f"Invalid model type '{model_type}'. Use one of: {' '.join(model_names.keys())}")
        
    yolo_model = torch.hub.load('ultralytics/yolov5', model_names[model_type], pretrained = True)
    return yolo_model

#load the YOLOv5 model
yolo_model = load_yolov5_model()


#Counting intersection traffic with YOLOv5
#---
#prepare a data frame 
all_detections = []

#iterate over each image in the directory
for image_name in os.listdir(images_dir):
    #define the image
    local_img_file = os.path.join(images_dir, image_name)
    
    #run the model on the image
    results = yolo_model(local_img_file)
    
    #obtain the traffic counts
    dt = results.pandas().xyxy[0]
    
    #format the data with traffic counts
    detection_counts = dt['name'].value_counts().reset_index()
    detection_counts.columns = ['name', 'count']
    detections_pivot = detection_counts.set_index('name').T.fillna(0).astype(int)
    
    #add the camera number to the image
    camera_number = int(re.search(r'\d+', image_name).group()) + 1
    detections_pivot['Camera Number'] = camera_number
    
    #store the results
    all_detections.append(detections_pivot)

#transform and format the data frame of traffic count results
all_detections_df = pd.concat(all_detections, ignore_index=True)
all_detections_df = all_detections_df.fillna(0)
cols = list(all_detections_df)
cols.insert(0, cols.pop(cols.index('Camera Number')))
all_detections_df = all_detections_df.loc[:, cols]

#count the different vehicle types
consolidated_detections_df = all_detections_df.groupby('Camera Number').sum().reset_index()
df_detections = consolidated_detections_df.filter(items=['Camera Number','car', 'truck','bus'])
final_detection_table = pd.merge(df_detections, df, how='inner', left_on ='Camera Number', right_on='Camera_Number')


#Adding time stamps to the data frame
#---
#timestamp API
timeapi_url = 'https://www.timeapi.io/api/Time/current/zone?timeZone=America/Edmonton'

#obtain the current date and time
response = requests.get(timeapi_url)
time_data = response.json()

#format the results
current_date = time_data['date']
current_time = time_data['time']
current_dayofweek = time_data['dayOfWeek']
df_time =pd.DataFrame({
    'Current Date':[current_date],
    'Current Time':[current_time],
    'Day of Week' :[current_dayofweek]
})

#append the date and time to the traffic count results
final_detection_table = final_detection_table.assign(
        **{'Current Date': current_date, 'Current Time': current_time, 'Day of Week': current_dayofweek}
    )

#save the traffic counts data frame as a csv
file_name = f"traffic_detection-{current_datetime}.csv"
final_detection_table.to_csv(f"results/{file_name}", index=False)

#keep only the most recent results table
result_tables = os.listdir('results')
result_tables.sort(key = lambda x: os.path.getctime(os.path.join('results', x)), reverse=True)
for result_table in result_tables[1:]:
    os.remove(os.path.join('results', result_table))


#Delete downloaded images to save storage
#---
#define the bash command to delete the images
delete_images = f"rm -f {images_dir}/*"

#run the delete command
process = subprocess.Popen(delete_images, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

#get the output and error (if any)
output, error = process.communicate()

#decode the output and error from bytes to string
output = output.decode("utf-8")
error = error.decode("utf-8")

#print the output and error
print("Output:", output)
print("Error:", error)