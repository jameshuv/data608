import streamlit as st
import pandas as pd

import local_functions as lf

########################################################################################
##################### Page Configuration ###############################################
########################################################################################

#Page layout and quick title
st.set_page_config(
    page_title="Calgary Traffic",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded")

#Page header
st.header(f"Traffic in Calgary", divider = True)

#Split into columns
col1, col2 = st.columns([0.2, 0.8])


########################################################################################
##################### Data Wrangle #####################################################
########################################################################################

# let's create client to read/write to S3
s3_client = boto3.client('s3')

# let's use that client to get our bucket
bucket_name = '' #Specify Bucket Name
object_key = '' #Specify object name '.csv'
response = s3_client.get_object(Bucket=bucket_name, Key=object_key)

# Use pandas to read the CSV directly from the S3 object
content = response['Body'].read().decode('utf-8')
chart_data = pd.read_csv(io.StringIO(content))


chart_data.rename(columns = {'camera_location': 'Intersection'}, inplace = True)
chart_data['traffic_sum'] = chart_data[['car','truck','bus']].sum(axis = 1)
chart_data['Traffic'] = pd.cut(chart_data['traffic_sum'], 
                            bins = chart_data['traffic_sum'].quantile([0,.3, .7,1]),
                            labels = ['Low', 'Moderate', 'High'])

#Colour index for map (below)
min_count = min(chart_data['traffic_sum'])
max_count = max(chart_data['traffic_sum'])

chart_data['color_column'] = chart_data.apply(lf.get_colour, min = min_count, max = max_count, axis = 1)


########################################################################################
##################### Data Viz #########################################################
########################################################################################

#Customize sidebar
st.sidebar.title("Current Conditions")
st.sidebar.write(chart_data[['Intersection', 'Traffic']])

#Populate col 1
with col1:
    sideplot = lf.get_sideplot(chart_data)
    st.plotly_chart(sideplot, use_container_width=True)

#Populate col 2
with col2:
    map = lf.get_map(chart_data)
    st.pydeck_chart(map)