#!/usr/bin/env python
"""
Create by Lori Garzio on 4/2/2019
@brief Create pcolor quiver plots of wind speeds for RU-WRF output
"""

import numpy as np
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
from oceans.ocfis import uv2spdir, spdir2uv
from mpl_toolkits.axes_grid1 import make_axes_locatable
import geopandas as gpd
import functions.common as cf


def get_data(ncfilepath, height):
    nc = xr.open_dataset(ncfilepath, mask_and_scale=False)
    fnc = nc.sel(height=height)  # subset variables at height=120
    u120 = np.squeeze(fnc['U'])
    v120 = np.squeeze(fnc['V'])
    lat = fnc['XLAT'].values
    lon = fnc['XLONG'].values

    angle, speed = uv2spdir(u120, v120)
    us, vs = spdir2uv(np.ones_like(speed), angle, deg=True)

    return lat, lon, speed, us, vs, u120, v120


def plot_pcolor_quiver(save_file, figtitle, latdata, londata, ws, us, vs, lease_area, plan_area, diff_plot=None):
    sub = 5
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.title(figtitle)

    if diff_plot == 'diff_plot':
        h = ax.pcolor(londata, latdata, ws, cmap='jet')
        cblabel = 'Wind Speed Difference (m/s)'
    else:
        h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=14.0, cmap='jet')
        cblabel = 'Wind Speed (m/s)'

    ax.quiver(londata[::sub, ::sub], latdata[::sub, ::sub], us[::sub, ::sub], vs[::sub, ::sub], cmap='jet',
              scale=40, width=.0015, headlength=3)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=2, color='gray', alpha=0.5,
                      linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    ax.set_extent([-76, -72.5, 37, 41])  # [min lon, max lon, min lat, max lat]

    LAND = cfeature.NaturalEarthFeature('physical', 'land', '10m')

    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none')

    ax.add_feature(LAND, zorder=5, edgecolor='black', facecolor='none')
    ax.add_feature(cfeature.BORDERS, zorder=6)
    ax.add_feature(state_lines, zorder=7, edgecolor='black')
    areas = lease_area.plot(ax=ax, color='none', edgecolor='black')
    areas = plan_area.plot(ax=ax, color='none', edgecolor='darkgray')

    if diff_plot != 'diff_plot':
        CS = ax.contour(londata, latdata, ws, [0, 12.5], colors='dimgray')
        ax.clabel(CS, inline=1, fontsize=10, fmt='%.1f')

    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)
    cb = plt.colorbar(h, cax=cax, label=cblabel)
    plt.savefig(save_file, dpi=300)
    plt.close('all')


sDir = '/Users/lgarzio/Documents/rucool/satellite/201508_upwelling_analysis/test'
time_range = cf.range1(16, 22)
ht = 120  # wind speed height

rootdir = '/Volumes/boardwalk/coolgroup/ru-wrf/case_studies/20150803/3km/processed/'
cpdir = os.path.join(rootdir, 'coldestpixel')
rtgdir = os.path.join(rootdir, 'rtg')
shape_file_lease = '/Users/lgarzio/Documents/rucool/satellite/BOEMshapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018/BOEM_Lease_Areas_10_24_2018.shp'
shape_file_plan = '/Users/lgarzio/Documents/rucool/satellite/BOEMshapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018/BOEM_Wind_Planning_Areas_10_24_2018.shp'
leasing_areas = gpd.read_file(shape_file_lease)
leasing_areas = leasing_areas.to_crs(crs={'init': 'epsg:4326'})
planning_areas = gpd.read_file(shape_file_plan)
planning_areas = planning_areas.to_crs(crs={'init': 'epsg:4326'})

for r in time_range:
    fend = '*H{}.nc'.format('%03d' % r)

    # Coldest pixel
    cpf = glob.glob(cpdir + '/wrfproc_3km' + fend)
    fname = cpf[0].split('/')[-1]
    print('Plotting {}'.format(fname))

    cp_lat, cp_lon, cp_speed, cp_us, cp_vs, cp_u, cp_v = get_data(cpf[0], ht)

    cptitle = 'RU-WRF Winds: 120m, Coldest Pixel SST'
    title2 = '{} {}{}'.format(datetime.strftime(datetime.strptime(fname.split('_')[2], '%Y%m%d'), '%Y-%m-%d'),
                              fname.split('_')[-1][2:4], 'Z')
    cpfigtitle = '{}\n{}'.format(cptitle, title2)
    cpfigname = 'coldestpixel_{}'.format(fname.split('.')[0])
    cpsfile = os.path.join(sDir, cpfigname)
    plot_pcolor_quiver(cpsfile, cpfigtitle, cp_lat, cp_lon, cp_speed, cp_us, cp_vs, leasing_areas, planning_areas)

    # RTG
    rtgf = glob.glob(rtgdir + '/wrfproc_3km' + fend)
    rtg_lat, rtg_lon, rtg_speed, rtg_us, rtg_vs, rtg_u, rtg_v = get_data(rtgf[0], ht)

    rtgtitle = 'RU-WRF Winds: 120m, RTG SST'
    rtgfigtitle = '{}\n{}'.format(rtgtitle, title2)
    rtgfigname = 'rtg_{}'.format(fname.split('.')[0])
    rtgsfile = os.path.join(sDir, rtgfigname)
    plot_pcolor_quiver(rtgsfile, rtgfigtitle, rtg_lat, rtg_lon, rtg_speed, rtg_us, rtg_vs, leasing_areas, planning_areas)

    # difference
    diff_u = cp_u - rtg_u
    diff_v = cp_v - rtg_v

    diff_angle, diff_speed = uv2spdir(diff_u, diff_v)
    diff_us, diff_vs = spdir2uv(np.ones_like(diff_speed), diff_angle, deg=True)

    # exclude outliers > 5 SD
    if np.nanmax(diff_speed) > 1:
        stdev = np.nanstd(diff_speed)
        dmax = np.nanmean(diff_speed) + 5 * stdev
        diff_speed[diff_speed > dmax] = np.nan

    difftitle = 'RU-WRF Winds: 120m, Difference (Coldest Pixel - RTG)'
    difffigtitle = '{}\n{}'.format(difftitle, title2)
    difffigname = 'difference_{}'.format(fname.split('.')[0])
    diffsfile = os.path.join(sDir, difffigname)
    plot_pcolor_quiver(diffsfile, difffigtitle, rtg_lat, rtg_lon, diff_speed, diff_us, diff_vs, leasing_areas,
                       planning_areas, 'diff_plot')
