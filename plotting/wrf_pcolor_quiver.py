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
import cmocean.cm as cmo
import functions.common as cf


def get_data(ncfilepath, height):
    nc = xr.open_dataset(ncfilepath, mask_and_scale=False)
    if height == 10:
        u = np.squeeze(nc['U10'])
        v = np.squeeze(nc['V10'])
        lat = nc['XLAT'].values
        lon = nc['XLONG'].values
    else:
        fnc = nc.sel(height=height)  # subset variables at specified height
        u = np.squeeze(fnc['U'])
        v = np.squeeze(fnc['V'])
        lat = fnc['XLAT'].values
        lon = fnc['XLONG'].values

    angle, speed = uv2spdir(u, v)
    us, vs = spdir2uv(np.ones_like(speed), angle, deg=True)

    return lat, lon, speed, us, vs, u, v


def plot_pcolor_quiver(save_file, figtitle, latdata, londata, ws, us, vs, lease_area, plan_area, blats, blons, diff_plot=None):
    sub = 5
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.title(figtitle)

    if diff_plot == 'diff_plot':
        #h = ax.pcolor(londata, latdata, ws, vmin=-3.0, vmax=3.0, cmap='seismic')
        h = ax.pcolor(londata, latdata, ws, vmin=-3.0, vmax=3.0, cmap=cmo.balance)
        cblabel = 'Wind Speed Difference (m/s)'
    else:
        h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=14.0, cmap='jet')
        #h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=14.0, cmap=cmo.amp)
        #h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=14.0, cmap='YlOrBr')
        cblabel = 'Wind Speed (m/s)'

    ax.quiver(londata[::sub, ::sub], latdata[::sub, ::sub], us[::sub, ::sub], vs[::sub, ::sub], cmap='jet',
              scale=40, width=.0015, headlength=3)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5,
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
    areas = plan_area.plot(ax=ax, color='none', edgecolor='dimgray')

    if diff_plot != 'diff_plot':
        CS = ax.contour(londata, latdata, ws, [0, 12.5], colors='whitesmoke', linewidths=2)
        ax.clabel(CS, inline=1, fontsize=10.5, fmt='%.1f')

    ax.scatter(blons, blats, facecolors='whitesmoke', edgecolors='black', linewidth='2', s=60)

    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)
    cb = plt.colorbar(h, cax=cax, label=cblabel)
    plt.savefig(save_file, dpi=300)
    plt.close('all')


sDir = '/Users/lgarzio/Documents/rucool/satellite/201508_upwelling_analysis/wrf_quiver'
time_range = cf.range1(19, 21)
ht = 120  # wind speed height
buoys = ['44009', '44025', '44065']

rootdir = '/Volumes/boardwalk/coolgroup/ru-wrf/case_studies/20150803/3km/processed/'
cpdir = os.path.join(rootdir, 'coldestpixel')
rtgdir = os.path.join(rootdir, 'rtg')
shape_file_lease = '/Users/lgarzio/Documents/rucool/satellite/BOEMshapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018/BOEM_Lease_Areas_10_24_2018.shp'
shape_file_plan = '/Users/lgarzio/Documents/rucool/satellite/BOEMshapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018/BOEM_Wind_Planning_Areas_10_24_2018.shp'
leasing_areas = gpd.read_file(shape_file_lease)
leasing_areas = leasing_areas.to_crs(crs={'init': 'epsg:4326'})
planning_areas = gpd.read_file(shape_file_plan)
planning_areas = planning_areas.to_crs(crs={'init': 'epsg:4326'})
buoy_lats, buoy_lons = [], []

for b in buoys:
    buoy_catalog = ['https://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/{}/catalog.html'.format(b)]
    buoy_datasets = cf.get_nc_urls(buoy_catalog)
    bf = buoy_datasets[-1]  # get the lat and lon from the most recent file for that buoy
    buoy_ds = xr.open_dataset(bf, mask_and_scale=False)
    buoy_lats.append(buoy_ds['latitude'].values[0])
    buoy_lons.append(buoy_ds['longitude'].values[0])

for r in time_range:
    fend = '*H{}.nc'.format('%03d' % r)

    # Coldest pixel
    cpf = glob.glob(cpdir + '/wrfproc_3km' + fend)
    fname = cpf[0].split('/')[-1]
    print('Plotting {}'.format(fname))

    cp_lat, cp_lon, cp_speed, cp_us, cp_vs, cp_u, cp_v = get_data(cpf[0], ht)

    cptitle = 'RU-WRF Winds: {}m, Coldest Pixel SST'.format(str(ht))
    title2 = '{} {}{}'.format(datetime.strftime(datetime.strptime(fname.split('_')[2], '%Y%m%d'), '%Y-%m-%d'),
                              fname.split('_')[-1][2:4], 'Z')
    cpfigtitle = '{}\n{}'.format(cptitle, title2)
    cpfigname = 'coldestpixel{}m_{}'.format(str(ht), fname.split('.')[0])
    cpsfile = os.path.join(sDir, cpfigname)
    plot_pcolor_quiver(cpsfile, cpfigtitle, cp_lat, cp_lon, cp_speed, cp_us, cp_vs, leasing_areas, planning_areas, buoy_lats, buoy_lons)

    # RTG
    rtgf = glob.glob(rtgdir + '/wrfproc_3km' + fend)
    rtg_lat, rtg_lon, rtg_speed, rtg_us, rtg_vs, rtg_u, rtg_v = get_data(rtgf[0], ht)

    rtgtitle = 'RU-WRF Winds: {}m, RTG SST'.format(str(ht))
    rtgfigtitle = '{}\n{}'.format(rtgtitle, title2)
    rtgfigname = 'rtg{}m_{}'.format(str(ht), fname.split('.')[0])
    rtgsfile = os.path.join(sDir, rtgfigname)
    plot_pcolor_quiver(rtgsfile, rtgfigtitle, rtg_lat, rtg_lon, rtg_speed, rtg_us, rtg_vs, leasing_areas, planning_areas, buoy_lats, buoy_lons)

    # difference
    diff_u = cp_u - rtg_u
    diff_v = cp_v - rtg_v

    diff_angle, __ = uv2spdir(diff_u, diff_v)
    diff_speed = cp_speed - rtg_speed
    diff_us, diff_vs = spdir2uv(np.ones_like(diff_speed), diff_angle, deg=True)

    # exclude outliers > 5 SD
    if np.nanmax(abs(diff_speed)) > 1:
        stdev = np.nanstd(diff_speed)
        dmax = np.nanmean(diff_speed) + 5 * stdev
        diff_speed[diff_speed > dmax] = np.nan

    difftitle = 'RU-WRF Winds: {}m, Difference (Coldest Pixel - RTG)'.format(str(ht))
    difffigtitle = '{}\n{}'.format(difftitle, title2)
    difffigname = 'difference{}m_{}'.format(str(ht), fname.split('.')[0])
    diffsfile = os.path.join(sDir, difffigname)
    plot_pcolor_quiver(diffsfile, difffigtitle, rtg_lat, rtg_lon, diff_speed, diff_us, diff_vs, leasing_areas,
                       planning_areas, buoy_lats, buoy_lons, 'diff_plot')
