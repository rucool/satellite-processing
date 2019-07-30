#! /usr/bin/env python

import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates


def add_map_features(ax, axes_limits=None, land_options=None):
    """
    :param ax: plotting axis object
    :param axes_limits: optional list of axes limits [min lon, max lon, min lat, max lat]
    :param land_options: optional list of land color options [edgecolor, facecolor]
    """
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xlabel_style = {'size': 14.5}
    gl.ylabel_style = {'size': 14.5}
    if axes_limits is not None:
        ax.set_extent(axes_limits)
    else:
        ax.set_extent([-76, -72.5, 37.8, 41])  # [min lon, max lon, min lat, max lat]

    if land_options is not None:
        land = cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor=land_options[0],
                                            facecolor=land_options[1])
        ax.add_feature(land, zorder=5, edgecolor='black')
    else:
        land = cfeature.NaturalEarthFeature('physical', 'land', '10m')
        ax.add_feature(land, zorder=5, edgecolor='black', facecolor='none')

    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none')

    #ax.add_feature(land, zorder=5, edgecolor='black', facecolor='none')
    ax.add_feature(cfeature.LAKES, zorder=8, facecolor='white')
    ax.add_feature(cfeature.BORDERS, zorder=6)
    ax.add_feature(state_lines, zorder=7, edgecolor='black')

    return ax


def format_date_axis(axis, figure):
    df = mdates.DateFormatter('%Y-%m-%d')
    axis.xaxis.set_major_formatter(df)
    figure.autofmt_xdate()


def format_date_axis_month(axis, figure):
    df = mdates.DateFormatter('%Y-%m')
    axis.xaxis.set_major_formatter(df)
    figure.autofmt_xdate()


def save_fig(save_dir, file_name, res=300):
    # save figure to a directory with a resolution of 300 DPI
    save_file = os.path.join(save_dir, file_name)
    plt.savefig(str(save_file), dpi=res)
    plt.close()


def y_axis_disable_offset(axis):
    # format y-axis to disable offset
    y_formatter = ticker.ScalarFormatter(useOffset=False)
    axis.yaxis.set_major_formatter(y_formatter)
