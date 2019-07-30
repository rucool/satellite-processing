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
from netCDF4 import Dataset, num2date
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1 import make_axes_locatable
import functions.common as cf


def plotMap(figname, figtitle, data):
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


rootdir = '/Users/lgarzio/Documents/rucool/satellite/coldest_pixel/daily_avhrr/composites'
sDir = '/Users/lgarzio/Documents/rucool/satellite/coldest_pixel/daily_avhrr/plots'
#rootdir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/composites'
#sDir = '/home/lgarzio/rucool/satellite/coldest_pixel/daily_avhrr/plots'
start_date = datetime(2013, 12, 13)   # datetime(2015, 7, 1)
end_date = datetime(2013, 12, 14)  # datetime(2016, 7, 1)

for n in range(int((end_date - start_date).days)):
    d = start_date + timedelta(n)
    yr = d.year
    avhrr_dir = os.path.join(rootdir, str(yr))
    ff = glob.glob(avhrr_dir + '/avhrr_coldest-pixel_' + d.strftime('%Y%m%d') + '*.nc')
    if len(ff) > 0:
        sstnc = Dataset(ff[0], 'r')
        lon = sstnc.variables['lon'][:]
        lat = sstnc.variables['lat'][:]
        sst = np.squeeze(sstnc.variables['sst'][:])
        sst[sst == -999] = np.nan
        sstt = sstnc.variables['time']
        t = num2date(sstt[0], units=sstt.units, calendar=sstt.calendar)
        cf.create_dir(os.path.join(sDir, str(t.year)))
        sname = 'avhrr_daily_plt_{}.png'.format(t.strftime('%Y%m%d'))
        sfile = os.path.join(sDir, str(t.year), sname)

        LAND = cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='tan')

        state_lines = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none')

        print('plotting {}'.format(ff[0].split('/')[-1]))
        plotMap(sfile, '1-day Coldest Pixel AVHRR Composite ' + t.strftime('%Y-%m-%d'), sst)
