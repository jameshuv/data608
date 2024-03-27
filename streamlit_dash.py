import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.subplots as pls
import plotly.graph_objects as go

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


########################################################################################
##################### Example Data Viz #################################################
########################################################################################
chart_data = pd.read_csv('traffic_detection.csv')
chart_data.rename(columns = {'camera_location': 'Intersection'}, inplace = True)
chart_data['traffic_sum'] = chart_data[['car','truck','bus']].sum(axis = 1)
chart_data['Traffic'] = pd.cut(chart_data['traffic_sum'], 
                            bins = chart_data['traffic_sum'].quantile([0,.33, .67,1]),
                            labels = ['Low', 'Moderate', 'High'])

#Customize sidebar
st.sidebar.title("Current Conditions")
st.sidebar.write(chart_data[['Intersection', 'Traffic']])

col1, col2 = st.columns([0.2, 0.8])


with col1:
    labels = list(chart_data['Traffic'].unique())
    values = list(chart_data['Traffic'].value_counts())

        
    fig = pls.make_subplots(rows=2, cols=1, specs=[[{'type':'domain'}],[{'type':'xy'}]], row_width=[0.3, 0.7])
    fig.add_trace(go.Pie(labels=labels, values=values, title=f"Traffic <br> <b>Levels</b>", 
                        title_font=dict(size=20, color = "white", family='Arial, sans-serif'),
                        hole=.4, hoverinfo="label+value+name", textinfo='percent+label',
                        marker=dict(colors=['darkorange', 'lightyellow', 'darkred'], line=dict(color='#000000', width=2))), 
                    row=1, col=1) 
    n=16
    x_example = np.arange(n)
    fig.add_trace(go.Scatter(
        x = pd.date_range('2024-03-26', periods=n, freq='1h'),
        y = np.sin(4*np.pi*x_example/n)+np.cos(8*np.pi*x_example/n) + 100,
        marker=dict(color='grey'),
        name="Historical Traffic",
        mode = 'lines'
    ), row=2, col=1)

    fig.update_layout(
        title_text="PE",
        showlegend=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True)

    fig.update_yaxes(title_text="Traffic Volume", row=2, col=1, showgrid=False)
    fig.update_xaxes(title_text="Time", row=2, col=1, showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

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
            'HexagonLayer',
            data=chart_data,
            get_position='[longitude, latitude]',
            radius=200,
            elevation_scale=4,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
            )
        ],
    ))
