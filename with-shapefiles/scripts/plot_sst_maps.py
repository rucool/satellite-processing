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
import xarray as xr
from mpl_toolkits.axes_grid1 import make_axes_locatable
import functions.common as cf
import functions.plotting as pf


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


def plotMap(figname, figtitle, latdata, londata, data, lease_area, plan_area, blats=None, blons=None):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.title(figtitle, fontsize=17)
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)
    h = ax.pcolor(londata, latdata, data, vmin=20, vmax=26, cmap='jet')
    plt.rcParams.update({'font.size': 14})
    cb = plt.colorbar(h, cax=cax, label='Temperature ($^\circ$C)')
    cb.ax.tick_params(labelsize=14)

    #ax = pf.add_map_features(ax, axes_limits=[-76, -68, 36, 42], land_options=['face', 'gainsboro'])
    ax = pf.add_map_features(ax, land_options=['face', 'gainsboro'])
    #ax = pf.add_map_features(ax, axes_limits=[-75.5, -73.2, 38.5, 40.7], land_options=['face', 'gainsboro'])

    lease_area.plot(ax=ax, color='none', edgecolor='black')
    plan_area.plot(ax=ax, color='none', edgecolor='dimgray')

    if blats:
        # add buoy locations
        ax.scatter(blons, blats, facecolors='whitesmoke', edgecolors='black', linewidth='2', s=60)

    plt.savefig(figname, dpi=300)
    plt.close()


model = ['nam', 'avhrr1', 'avhrr3', 'rtg', 'gfs']
#model = ['avhrr1']
sDir = '/Users/lgarzio/Documents/rucool/satellite/test'
#rootdir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/composites'
#sDir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/plots'
start_date = datetime(2015, 7, 31)   # datetime(2015, 7, 1)
end_date = datetime(2015, 8, 6)  # datetime(2016, 7, 1)
buoys = ['44009', '44025', '44065']
#buoys = ['44008', '44009', '44014', '44017', '44020', '44025', '44065']  # Mid-Atlantic buoys

#boem_rootdir = '/home/coolgroup/bpu/mapdata/shapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018'
boem_rootdir = '/Users/lgarzio/Documents/rucool/satellite/BOEMshapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018'
leasing_areas, planning_areas = cf.boem_shapefiles(boem_rootdir)

buoy_lats, buoy_lons = cf.get_buoy_locations(buoys)

for n in range(int((end_date - start_date).days)):
    dt = start_date + timedelta(n)
    var_names = ['TMP_P0_L1_GLC0', 'sst', 'sst', 'TMP_173_SFC', 'TMP_P0_L1_GLL0']
    lat_names = ['gridlat_0', 'lat', 'lat', 'lat_173', 'lat_0']
    lon_names = ['gridlon_0', 'lon', 'lon', 'lon_173', 'lon_0']
    # var_names = ['TMP_173_SFC']
    # lat_names = ['lat_173']
    # lon_names = ['lon_173']
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

            cf.create_dir(os.path.join(sDir, 'sst_plots'))
            sname = '{}_sst_{}.png'.format(model[i], dt.strftime('%Y%m%d'))
            sfile = os.path.join(sDir, 'sst_plots', sname)

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
            plotMap(sfile, title, lats.values, lons.values, sst.values, leasing_areas, planning_areas, buoy_lats, buoy_lons)
