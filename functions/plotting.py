#! /usr/bin/env python

import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean.cm as cmo
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import make_axes_locatable


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


def plot_pcolor_quiver(save_file, figtitle, latdata, londata, ws, us, vs, lease_area, plan_area, blats, blons, model, diff_plot=None):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.title(figtitle, fontsize=17)

    if diff_plot == 'yes':
        h = ax.pcolor(londata, latdata, ws, vmin=-3.0, vmax=3.0, cmap=cmo.balance)
        cblabel = 'Wind Speed Difference (m/s)'
    else:
        #h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=14.0, cmap='jet')
        h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=16.0, cmap='jet')
        cblabel = 'Wind Speed (m/s)'

    plt.rcParams.update({'font.size': 14})
    if model == 'gfs':
        ax.quiver(londata, latdata, us, vs, scale=40, width=.0015, headlength=3)
    else:
        if model == 'nam':
            sub = 2
        else:
            sub = 5

        ax.quiver(londata[::sub, ::sub], latdata[::sub, ::sub], us[::sub, ::sub], vs[::sub, ::sub], scale=40,
                  width=.0015, headlength=3)

    ax = add_map_features(ax)

    lease_area.plot(ax=ax, color='none', edgecolor='black')
    plan_area.plot(ax=ax, color='none', edgecolor='dimgray')

    if diff_plot != 'diff_plot':
        CS = ax.contour(londata, latdata, ws, [0, 12.5], colors='whitesmoke', linewidths=2)
        ax.clabel(CS, inline=1, fontsize=10.5, fmt='%.1f')

    # add buoy locations
    ax.scatter(blons, blats, facecolors='whitesmoke', edgecolors='black', linewidth='2', s=60)

    # add DOE LIDAR buoy location
    ax.scatter(-74.401, 39.314, facecolors='magenta', edgecolors='black', linewidth='2', s=60, label='DOE LIDAR')

    # add colorbar
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)
    cb = plt.colorbar(h, cax=cax, label=cblabel)
    cb.ax.tick_params(labelsize=14)
    plt.savefig(save_file, dpi=300)
    plt.close('all')


def save_fig(save_dir, file_name, res=300):
    # save figure to a directory with a resolution of 300 DPI
    save_file = os.path.join(save_dir, file_name)
    plt.savefig(str(save_file), dpi=res)
    plt.close()


def y_axis_disable_offset(axis):
    # format y-axis to disable offset
    y_formatter = ticker.ScalarFormatter(useOffset=False)
    axis.yaxis.set_major_formatter(y_formatter)
