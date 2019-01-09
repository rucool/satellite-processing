from sys import argv, exit
script, sstfile, imgName = argv

import matplotlib
matplotlib.use('Agg')
#import pandas as pd
import numpy as np
from netCDF4 import Dataset, num2date
import datetime
#from itertools import compress
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1 import make_axes_locatable


sstnc=Dataset(sstfile,'r')
lon=sstnc.variables['lon'][:]
lat=sstnc.variables['lat'][:]
sst=np.squeeze(sstnc.variables['sst'][:])
sst[sst==-999]=np.nan
sstt=sstnc.variables['time']
t=num2date(sstt[0],units=sstt.units,calendar=sstt.calendar)


LAND = cfeature.NaturalEarthFeature(
    'physical', 'land', '10m',
    edgecolor='face',
    facecolor='tan')

state_lines = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')


def plotMap(figname,figtitle,data):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(11, 8),subplot_kw=dict(projection=ccrs.PlateCarree()))
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    plt.title(figtitle)
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.05, axes_class=plt.Axes)
    fig.add_axes(cax)
    ax.set_extent([np.min(lon),np.max(lon),np.min(lat),np.max(lat)])
    ax.add_feature(LAND, zorder=0, edgecolor='black')
    ax.add_feature(cfeature.LAKES, facecolor='white')
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(state_lines, edgecolor='black')
    h=ax.pcolor(lon,lat,data,vmin=0,vmax=30,cmap='jet')
    cb=plt.colorbar(h,cax=cax)
    plt.savefig(figname, dpi=300)


plotMap(imgName,'1-day Coldest Pixel AVHRR Composite '+t.strftime('%Y-%m-%d'),sst)
plt.close('all')

exit()
