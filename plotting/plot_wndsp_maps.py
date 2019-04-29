#!/usr/bin/env python
"""
@author Lori Garzio on 4/23/2019
@brief Create daily wind speed plots for the Mid-Atlantic region for GFS and NAM
"""

import numpy as np
import pandas as pd
import os
import glob
from datetime import datetime, timedelta
import xarray as xr
from oceans.ocfis import uv2spdir, spdir2uv
import functions.common as cf
import functions.plotting as pf


def get_files(md, dt):
    rootdir = '/Volumes/boardwalk/jad438/validation_data'

    if md == 'nam':
        fdir = os.path.join(rootdir, 'historicalnamdata')
        ff = glob.glob(fdir + '/nams_data_hist_' + dt.strftime('%Y%m%d') + '.nc')
    elif md == 'gfs':
        fdir = os.path.join(rootdir, 'historicalgfsdata')
        ff = glob.glob(fdir + '/gfs_data_hist_' + dt.strftime('%Y%m%d') + '.nc')

    return ff


def main(sDir, start_date, end_date, buoys, models):
    #boem_rootdir = '/home/coolgroup/bpu/mapdata/shapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018'
    boem_rootdir = '/Users/lgarzio/Documents/rucool/satellite/BOEMshapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018'
    leasing_areas, planning_areas = cf.boem_shapefiles(boem_rootdir)

    buoy_lats, buoy_lons = cf.get_buoy_locations(buoys)

    for n in range(int((end_date - start_date).days)):
        dt = start_date + timedelta(n)
        nam_vars = ['lv_HTGL3', 'gridlon_0', 'gridlat_0']
        gfs_vars = ['lv_HTGL7', 'lon_0', 'lat_0']
        for model in models:
            ff = get_files(model, dt)
            if len(ff) == 1:
                nc = xr.open_dataset(ff[0], mask_and_scale=False)
                if model == 'nam':
                    vars = nam_vars
                elif model =='gfs':
                    vars = gfs_vars

                heights = nc[vars[0]].values
                times = nc['time'].values
                for h in heights:
                    if model == 'nam':
                        fnc = nc.sel(lv_HTGL3=h)
                        lon = fnc[vars[1]]
                    elif model == 'gfs':
                        fnc = nc.sel(lv_HTGL7=h)
                        lon = fnc[vars[1]] - 360

                    lat = fnc[vars[2]]
                    lon_ind = np.logical_and(lon > -78, lon < -68)
                    lat_ind = np.logical_and(lat > 35, lat < 45)

                    for i in range(len(times)):
                        # get variables at time 00:00Z
                        u = fnc['eastward_wind'][i]
                        v = fnc['northward_wind'][i]
                        tm = pd.to_datetime(str(fnc['time'][i].values))

                        if model == 'nam':
                            # find i and j indices of lon/lat in boundaries
                            ind = np.where(np.logical_and(lon_ind, lat_ind))
                            # subset lats, lons, variables from min i,j corner to max i,j corner
                            # there will be some points outside of defined boundaries because grid is not rectangular
                            lats = lat[range(np.min(ind[0]), np.max(ind[0]) + 1), range(np.min(ind[1]), np.max(ind[1]) + 1)]
                            lons = lon[range(np.min(ind[0]), np.max(ind[0]) + 1), range(np.min(ind[1]), np.max(ind[1]) + 1)]

                            u = u[range(np.min(ind[0]), np.max(ind[0]) + 1), range(np.min(ind[1]), np.max(ind[1]) + 1)]
                            v = v[range(np.min(ind[0]), np.max(ind[0]) + 1), range(np.min(ind[1]), np.max(ind[1]) + 1)]

                            figtitle = 'NAM Winds: {}m\n{}'.format(int(h), tm.strftime('%Y-%m-%d %HZ'))
                            figname = 'nam_{}m_{}_H0{}'.format(int(h), tm.strftime('%Y%m%d'), tm.strftime('%H'))
                            sdir = os.path.join(sDir, 'nam_windspeed')

                        elif model == 'gfs':
                            u = u[lat_ind, lon_ind]
                            v = v[lat_ind, lon_ind]
                            lats = lat[lat_ind]
                            lons = lon[lon_ind]

                            figtitle = 'GFS Winds: {}m\n{}'.format(int(h), tm.strftime('%Y-%m-%d %HZ'))
                            figname = 'gfs_{}m_{}_H0{}'.format(int(h), tm.strftime('%Y%m%d'), tm.strftime('%H'))
                            sdir = os.path.join(sDir, 'gfs_windspeed')

                        cf.create_dir(sdir)
                        sfile = os.path.join(sdir, figname)

                        angle, speed = uv2spdir(u, v)
                        us, vs = spdir2uv(np.ones_like(speed), angle, deg=True)
                        pf.plot_pcolor_quiver(sfile, figtitle, lats, lons, speed, us, vs, leasing_areas,
                                              planning_areas, buoy_lats, buoy_lons, model)


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    save_dir = '/Users/lgarzio/Documents/rucool/satellite/20160724_upwelling_analysis'
    sdate = datetime(2016, 7, 23)  # datetime(2015, 7, 1)
    edate = datetime(2016, 7, 25)  # datetime(2016, 7, 1)
    ndbc_buoys = ['44009', '44025', '44065']
    plt_models = ['gfs', 'nam']
    main(save_dir, sdate, edate, ndbc_buoys, plt_models)
