#!/usr/bin/env python
"""
@author Laura Nazarro
@modified by Lori Garzio on 3/20/2019
@brief
"""

import numpy as np
import os
import glob
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
from mpl_toolkits.axes_grid1 import make_axes_locatable
import functions.common as cf


def get_files(md, dt):
    rootdir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data'
    yr = dt.year

    if md == 'avhrr1':
        fdir = os.path.join(rootdir, 'daily_avhrr/composites', str(yr))
        ff = glob.glob(fdir + '/avhrr_coldest-pixel_' + dt.strftime('%Y%m%d') + '*.nc')
    elif md == 'avhrr3':
        fdir = os.path.join(rootdir, 'composites/archive_no_time_field')
        ff = glob.glob(fdir + '/sport_' + dt.strftime('%Y%m%d') + '*.nc')
    elif md == 'rtg':
        fdir = os.path.join(rootdir, 'rtg_nc', str(yr))
        ff = glob.glob(fdir + '/rtg_sst_grb_*' + dt.strftime('%Y%m%d') + '.nc')
    elif md == 'gfs':
        fdir = os.path.join(rootdir, 'gfs_nc', str(yr))
        ff = glob.glob(fdir + '/gfs.0p25.*' + dt.strftime('%Y%m%d') + '*f000.nc')
    return ff


def plotMap(figname, figtitle, latdata, londata, data):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.title(figtitle)
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.05, axes_class=plt.Axes)
    fig.add_axes(cax)
    h = ax.pcolor(londata, latdata, data, vmin=10, vmax=30, cmap='jet')
    cb = plt.colorbar(h, cax=cax, label='Temperature (degrees C)')
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    ax.set_extent([-78, -69, 36.5, 43])  # [min lon, max lon, min lat, max lat]
    LAND = cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='tan')

    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none')

    ax.add_feature(LAND, zorder=5, edgecolor='black')
    ax.add_feature(cfeature.LAKES, zorder=8, facecolor='white')
    ax.add_feature(cfeature.BORDERS, zorder=6)
    ax.add_feature(state_lines, zorder=7, edgecolor='black')
    plt.savefig(figname, dpi=300)
    plt.close()


model = ['avhrr1', 'avhrr3', 'rtg', 'gfs']
sDir = '/Users/lgarzio/Documents/rucool/satellite/201508_upwelling_analysis'
#rootdir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/composites'
#sDir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/plots'
start_date = datetime(2015, 7, 25)   # datetime(2015, 7, 1)
end_date = datetime(2015, 8, 11)  # datetime(2016, 7, 1)

for n in range(int((end_date - start_date).days)):
    dt = start_date + timedelta(n)
    var_names = ['sst', 'sst', 'TMP_173_SFC', 'TMP_P0_L1_GLL0']
    lat_names = ['lat', 'lat', 'lat_173', 'lat_0']
    lon_names = ['lon', 'lon', 'lon_173', 'lon_0']
    for i in range(len(model)):
        ff = get_files(model[i], dt)
        if len(ff) == 1:
            vname = var_names[i]
            sstnc = xr.open_dataset(ff[0], mask_and_scale=False)
            sstnc.load()
            if 'avhrr' not in model[i]:
                lon = sstnc[lon_names[i]].values - 360
            else:
                lon = sstnc[lon_names[i]].values
            lat = sstnc[lat_names[i]].values
            lon_ind = np.logical_and(lon > -78, lon < -68)
            lat_ind = np.logical_and(lat > 35, lat < 45)

            cf.create_dir(os.path.join(sDir, str(dt.year)))
            sname = '{}_sst_{}.png'.format(model[i], dt.strftime('%Y%m%d'))
            sfile = os.path.join(sDir, str(dt.year), sname)

            if model[i] == 'avhrr1':
                sst = np.squeeze(sstnc[vname][:, :, lat_ind, lon_ind])
                sst.values[sst == sstnc[vname]._FillValue] = np.nan  # turn fill values to nans
                title = 'AVHRR 1-day Coldest Pixel {}'.format(dt.strftime('%Y-%m-%d'))
            if model[i] == 'avhrr3':
                sst = np.squeeze(sstnc[vname][lon_ind, lat_ind])
                sst.values[sst == sstnc[vname]._FillValue] = np.nan  # turn fill values to nans
                sst = sst.transpose()
                title = 'AVHRR 3-day Coldest Pixel + SPoRT {}'.format(dt.strftime('%Y-%m-%d'))
            elif model[i] == 'rtg':
                sst = np.squeeze(sstnc[vname][lat_ind, lon_ind])
                sst.values[sst == sstnc[vname]._FillValue] = np.nan  # turn fill values to nans
                title = 'RTG {}'.format(dt.strftime('%Y-%m-%d'))
            elif model[i] == 'gfs':
                sst = np.squeeze(sstnc[vname][lat_ind, lon_ind])
                title = 'GFS (f000) {}'.format(dt.strftime('%Y-%m-%d'))

            if 'avhrr' not in model[i]:
                sst = sst - 273.15  # convert K to C

            print('plotting {}'.format(ff[0].split('/')[-1]))
            plotMap(sfile, title, lat[lat_ind], lon[lon_ind], sst.values)
