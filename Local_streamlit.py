import streamlit as st
import pandas as pd
import numpy as np
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
chart_data = pd.read_csv('traffic_detection-2.csv')


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
    fig = lf.side_plot(chart_data)
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

