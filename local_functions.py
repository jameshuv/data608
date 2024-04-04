from math import floor
import plotly.graph_objects as go
import plotly.subplots as pls
import pandas as pd
import numpy as np

def get_color(row, min, max):
    #Define custom RGBA colur scheme
    diff = max - min

    color_scheme = [
        [255,255,178],
        [254,217,118],
        [254, 178, 76],
        [253, 141, 60],
        [240,59,32],
        [189,0,38]
    ]

    number_of_colors = len(color_scheme)
    index = floor(number_of_colors * (row['traffic_sum'] - min) / diff)
    if index == number_of_colors:
        index = number_of_colors - 1
    elif index == -1:
        index = 0
    return color_scheme[index]

def side_plot(chart_data):
    
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
    return(fig)