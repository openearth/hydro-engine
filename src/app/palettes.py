"""
Convert between different colormap formats
"""

import matplotlib.colors
import pycpt.load


def pycpt2gee(pycpt_name='gmt/GMT_ocean.cpt'):
    """convert a pycpt colormap to a earth engine palette"""

    cmap = pycpt.load.cmap_from_cptcity_url(pycpt_name)
    colors = []
    # loop over all channels
    for item in zip(
            cmap._segmentdata['red'],
            cmap._segmentdata['green'],
            cmap._segmentdata['blue']
    ):
        colors.append((item[0][1], item[1][1], item[2][1]))

    # convert to hex and strip off the #
    ee_palette = [
        matplotlib.colors.rgb2hex(color).lstrip('#')
        for color
        in colors
    ]
    # paste together with ,
    ee_palette_str = ",".join(ee_palette)
    return ee_palette_str
