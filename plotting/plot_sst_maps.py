#!/usr/bin/env python
"""
@author Laura Nazarro
@modified by Lori Garzio on 3/20/2019
@brief Create daily SST plots for the Mid-Atlantic region for AVHRR, RTG, and GFS
"""

import numpy as np
import os
import glob
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import geopandas as gpd
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
    elif md == 'nam':
        fdir = os.path.join(rootdir, 'nam_nc', str(yr))
        ff = glob.glob(fdir + '/nam_*' + dt.strftime('%Y%m%d') + '*_000.nc')
    return ff


def plotMap(figname, figtitle, latdata, londata, data, lease_area, plan_area):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.title(figtitle)
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.05, axes_class=plt.Axes)
    fig.add_axes(cax)
    h = ax.pcolor(londata, latdata, data, vmin=18, vmax=28, cmap='jet')
    cb = plt.colorbar(h, cax=cax, label='Temperature ($^\circ$C)')
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    ax.set_extent([-76, -72.5, 37, 41])  # [min lon, max lon, min lat, max lat]
    LAND = cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='gainsboro')

    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none')

    ax.add_feature(LAND, zorder=5, edgecolor='black')
    ax.add_feature(cfeature.LAKES, zorder=8, facecolor='white')
    ax.add_feature(cfeature.BORDERS, zorder=6)
    ax.add_feature(state_lines, zorder=7, edgecolor='black')
    areas = lease_area.plot(ax=ax, color='none', edgecolor='black')
    areas = plan_area.plot(ax=ax, color='none', edgecolor='darkgray')
    plt.savefig(figname, dpi=300)
    plt.close()


model = ['nam', 'avhrr1', 'avhrr3', 'rtg', 'gfs']
sDir = '/Users/lgarzio/Documents/rucool/satellite/201508_upwelling_analysis'
#rootdir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/composites'
#sDir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/plots'
start_date = datetime(2015, 7, 25)   # datetime(2015, 7, 1)
end_date = datetime(2015, 8, 11)  # datetime(2016, 7, 1)

shape_file_lease = os.path.join(sDir, 'shapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018/BOEM_Lease_Areas_10_24_2018.shp')
shape_file_plan = os.path.join(sDir, 'shapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018/BOEM_Wind_Planning_Areas_10_24_2018.shp')
leasing_areas = gpd.read_file(shape_file_lease)
leasing_areas = leasing_areas.to_crs(crs={'init': 'epsg:4326'})
planning_areas = gpd.read_file(shape_file_plan)
planning_areas = planning_areas.to_crs(crs={'init': 'epsg:4326'})

for n in range(int((end_date - start_date).days)):
    dt = start_date + timedelta(n)
    var_names = ['TMP_P0_L1_GLC0', 'sst', 'sst', 'TMP_173_SFC', 'TMP_P0_L1_GLL0']
    lat_names = ['gridlat_0', 'lat', 'lat', 'lat_173', 'lat_0']
    lon_names = ['gridlon_0', 'lon', 'lon', 'lon_173', 'lon_0']
    for i in range(len(model)):
        ff = get_files(model[i], dt)
        if len(ff) == 1:
            vname = var_names[i]
            sstnc = xr.open_dataset(ff[0], mask_and_scale=False)
            sstnc.load()
            if model[i] in ['rtg', 'gfs']:
                lon = sstnc[lon_names[i]] - 360
            else:
                lon = sstnc[lon_names[i]]
            lat = sstnc[lat_names[i]]
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
            elif model[i] == 'nam':
                # find i and j indices of lon/lat in boundaries
                ind = np.where(np.logical_and(lon_ind, lat_ind))
                # subset lats, lons, sst from min i,j corner to max i,j corner
                # there will be some points outside of defined boundaries because grid is not rectangular
                lats = lat[range(np.min(ind[0]), np.max(ind[0]) + 1), range(np.min(ind[1]), np.max(ind[1]) + 1)]
                lons = lon[range(np.min(ind[0]), np.max(ind[0]) + 1), range(np.min(ind[1]), np.max(ind[1]) + 1)]
                sst = sstnc[vname]
                sst = sst[range(np.min(ind[0]), np.max(ind[0]) + 1), range(np.min(ind[1]), np.max(ind[1]) + 1)]
                title = 'NAM {}'.format(dt.strftime('%Y-%m-%d'))

            if 'nam' not in model[i]:
                lats = lat[lat_ind]
                lons = lon[lon_ind]

            if 'avhrr' not in model[i]:
                sst = sst - 273.15  # convert K to C

            print('plotting {}'.format(ff[0].split('/')[-1]))
            plotMap(sfile, title, lats.values, lons.values, sst.values, leasing_areas, planning_areas)
