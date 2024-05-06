import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import os
import sys

sys.path.append('/usr/src/calgary_traffic/app/')

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

#load the traffic counts data frame from YOLOv5
csv_file = [file for file in os.listdir('/usr/src/calgary_traffic/yolov5/results/') if file.endswith('.csv')]
csv_file = ' '.join(csv_file)
chart_data = pd.read_csv('/usr/src/calgary_traffic/yolov5/results/' + csv_file)

#format the data frame for visualization
chart_data.rename(columns = {'camera_location': 'Intersection'}, inplace = True)
chart_data['traffic_sum'] = chart_data[['car','truck','bus']].sum(axis = 1)
chart_data['Traffic'] = pd.cut(chart_data['traffic_sum'],
                               bins = chart_data['traffic_sum'].quantile([0,.3, .7,1]),
                               labels = ['Low', 'Moderate', 'High'])

#chart_data['Traffic'] = pd.qcut(chart_data['traffic_sum'],
#                               q = 4,
#                               labels = ['Low', 'Moderate', 'High'],
#                               duplicates = 'drop')

#Colour index for map (below)
min_count = min(chart_data['traffic_sum'])
max_count = max(chart_data['traffic_sum'])

chart_data['color_column'] = chart_data.apply(lf.get_colour, min= min_count, max = max_count, axis = 1)

########################################################################################
##################### Data Viz #########################################################
########################################################################################

sel_row = pd.DataFrame()

#Customize sidebar
#st.sidebar.title("Current Conditions")

#with st.sidebar:
#    gd = GridOptionsBuilder.from_dataframe(chart_data[['Intersection', 'Traffic']])
#    gd.configure_pagination(enabled=False)
#    gd.configure_side_bar()
#    gd.configure_selection(selection_mode='single',use_checkbox=True)
#    gd.configure_column("Intersection", headerCheckboxSelection = True)
#    gridoptions = gd.build()
#    grid_table = AgGrid(chart_data[['Intersection', 'Traffic']],gridOptions=gridoptions,
#                        update_mode= GridUpdateMode.SELECTION_CHANGED,
#                        height = 650,
#                        allow_unsafe_jscode=True,
#                        theme = 'alpine',
#                        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)
#    sel_row = grid_table["selected_rows"]

#Populate col 1
with col1:
    sideplot = lf.get_sideplot(chart_data)
    st.plotly_chart(sideplot, use_container_width=True)

#Populate col 2
with col2:
    map = lf.get_map(chart_data, sel_row)
    st.pydeck_chart(map)
    
    col2_1, col2_2 = st.columns([0.9, 0.1])
    
    with col2_1:
        st.write(chart_data['Current Time'].unique()[0], chart_data['Current Date'].unique()[0])
    with col2_2:
        rerun_button = st.button('Refresh')
        
        if rerun_button:
            st.rerun()
