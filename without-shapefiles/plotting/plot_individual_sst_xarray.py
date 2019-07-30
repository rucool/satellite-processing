#!/usr/bin/env python
"""
@author Laura Nazarro
@modified by Lori Garzio on 1/30/2019
@brief Plot daily coldest pixel data for historical AVHRR satellite data (from 9/1/2013 to 9/19/2018)
"""

import numpy as np
import os
import glob
from datetime import datetime, timedelta
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1 import make_axes_locatable
import functions.common as cf


def plotMap(figname, figtitle, data, lon, lat):
    fig, ax = plt.subplots(figsize=(11, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    plt.title(figtitle)
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.05, axes_class=plt.Axes)
    fig.add_axes(cax)
    ax.set_extent([np.min(lon), np.max(lon), np.min(lat), np.max(lat)])
    ax.add_feature(LAND, zorder=0, edgecolor='black')
    ax.add_feature(cfeature.LAKES, facecolor='white')
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(state_lines, edgecolor='black')
    h = ax.pcolor(lon, lat, data, vmin=0, vmax=30, cmap='jet')
    cb = plt.colorbar(h, cax=cax)
    plt.savefig(figname, dpi=300)
    plt.close()


#rootdir = '/Users/lgarzio/Documents/rucool/satellite/coldest_pixel/daily_avhrr/composites'
rootdir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/'
sDir = '/Users/lgarzio/Documents/rucool/satellite/coldest_pixel/daily_avhrr/plots/test'
flst = ['/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131105.309.1854.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131105.309.1713.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131105.309.1923.n18.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131123.327.1923.n18.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131123.327.1859.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131123.327.1719.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131125.329.1657.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131125.329.1837.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131125.329.1901.n18.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131213.347.1702.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131213.347.1843.n19.BPU.CF.nc', '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/131213.347.1901.n18.BPU.CF.nc']
start_date = datetime(2013, 8, 30)   # datetime(2015, 7, 1)
# end_date = datetime(2016, 8, 31)  # datetime(2016, 7, 1)
#
# for n in range(int((end_date - start_date).days)):
#     d = start_date + timedelta(n)
#     yr = d.year
#     avhrr_dir = os.path.join(rootdir, str(yr))
#     ff = glob.glob(avhrr_dir + '/avhrr_coldest-pixel_' + d.strftime('%Y%m%d') + '*.nc')
for ff in flst:
    # f = '161009.283.1348.n18.BPU.CF.nc'
    # ff = glob.glob(rootdir + f)
    if len(ff) > 0:
        #sstnc = xr.open_dataset(ff[0], mask_and_scale=False)
        sstnc = xr.open_dataset(ff, mask_and_scale=False)
        lon = sstnc['lon'].values
        lat = sstnc['lat'].values
        # get rid of crazy lats and lons
        lon_ind = np.logical_and(lon > -90, lon < -42)
        lat_ind = np.logical_and(lat > 20, lat < 55)
        sst = np.squeeze(sstnc['mcsst'][:, lat_ind, lon_ind])
        sst.values[sst == -999] = np.nan
        cf.create_dir(os.path.join(sDir, str(start_date.year)))
        sname = 'avhrr_individual_plt_{}.png'.format(ff.split('/')[-1][:-10])
        sfile = os.path.join(sDir, str(start_date.year), sname)

        LAND = cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='tan')

        state_lines = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none')

        print('plotting {}'.format(ff.split('/')[-1][:-10]))
        plotMap(sfile, 'AVHRR pass {}'.format(ff.split('/')[-1][:-10]), sst, lon[lon_ind], lat[lat_ind])
