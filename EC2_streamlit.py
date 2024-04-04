import streamlit as st
import pandas as pd
import numpy as np
import io
import pydeck as pdk
import plotly.subplots as pls
import plotly.graph_objects as go
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
##################### Example Data Viz #################################################
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

#Customize sidebar
st.sidebar.title("Current Conditions")
st.sidebar.write(chart_data[['Intersection', 'Traffic']])

#Populate col 1
with col1:
    labels = list(chart_data['Traffic'].dropna().unique())
    values = list(chart_data['Traffic'].value_counts())

        
    fig = pls.make_subplots(rows=2, cols=1, specs=[[{'type':'domain'}],[{'type':'xy'}]], row_width=[0.3, 0.7])
    fig.add_trace(go.Pie(labels=labels, values=values, title=f"Traffic <br> <b>Levels</b>", 
                        title_font=dict(size=20, color = "white", family='Arial, sans-serif'),
                        hole=.4, hoverinfo="label+value+name", textinfo='percent+label',
                        marker=dict(colors=['darkorange', 'lightyellow', 'darkred'], line=dict(color='#000000', width=2))), 
                    row=1, col=1) 
    n=16 #example hours
    x_example = np.arange(n*12)
    fig.add_trace(go.Scatter(
        x = pd.date_range('2024-04-01', periods=24*12, freq='5min'),
        y = np.sin(1/2*np.pi*x_example/n)+np.cos(1/4*np.pi*x_example/n) + 100,
        marker=dict(color='grey'),
        name="Historical Traffic",
        mode = 'lines'
    ), row=2, col=1)

    fig.update_layout(
        title_text="PE",
        showlegend=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True)

    fig.update_yaxes(title_text="Avg. Traffic Vol.", row=2, col=1, showgrid=False)
    fig.update_xaxes(title_text="Time", row=2, col=1, showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

#Populate col 2

#Project traffic sum observations onto linear representation of custom RGBA values
min_count = min(chart_data['traffic_sum'])
max_count = max(chart_data['traffic_sum'])

chart_data['color_column'] = chart_data.apply(lf.get_color, min = min_count, max = max_count, axis = 1)

with col2:
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=51.066886,
            longitude=-114.065353,
            zoom=10,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
            'ColumnLayer',
            data=chart_data,
            get_position='[longitude, latitude]',
            get_elevation="traffic_sum",
            radius=200,
            elevation_scale=100,
            get_fill_color='color_column',
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
            )
        ],
    ))
