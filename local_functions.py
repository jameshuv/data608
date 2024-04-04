from math import floor

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