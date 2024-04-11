from math import floor
import plotly.graph_objects as go
import plotly.subplots as pls
import pandas as pd
import numpy as np
import pydeck as pdk
import streamlit as st

def get_colour(row, min, max):
    #Define custom RGBA colur scheme
    diff = max - min

    colour_scheme = [
        [255,255,178],
        [254,217,118],
        [254, 178, 76],
        [253, 141, 60],
        [240,59,32],
        [189,0,38]
    ]

    number_of_colors = len(colour_scheme)
    index = floor(number_of_colors * (row['traffic_sum'] - min) / diff)
    if index == number_of_colors:
        index = number_of_colors - 1
    elif index == -1:
        index = 0
    return colour_scheme[index]

def get_sideplot(chart_data):
    
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
        margin={"r": 5, "t": 0, "l": 0, "b": 0}, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', autosize = True)

    fig.update_yaxes(title_text="Avg. Traffic Vol.", row=2, col=1, showgrid=False)
    fig.update_xaxes(title_text="Time", row=2, col=1, showgrid=False)
    return(fig)


def get_map(chart_data, sel_row):
    if sel_row.empty:

        latitude=51.066886
        longitude=-114.065353
        zoom = 10
        opacity = 0.9
    else:
        intersection = str(sel_row['Intersection'][0])
        latitude = chart_data['latitude'][chart_data['Intersection'] == intersection].mean()
        longitude = chart_data['longitude'][chart_data['Intersection'] == intersection].mean()
        zoom = 12.5
        opacity = 0.3

    fig = pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=latitude,
                longitude=longitude,
                zoom=zoom,
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
                opacity=opacity
                )
            ],
        )
    return(fig)