#!/usr/bin/env python
"""
Created on Jan 25 2019 by Lori Garzio
@brief plot buoy locations
"""

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import cartopy.feature as cfeature
import functions.common as cf
import functions.plotting as pf


sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
# buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
#          '44017', '44018', '44020', '44025', '44027', '44065']

buoys = ['44008', '44009', '44014', '44017', '44025', '44065']  # Mid-Atlantic buoys

# buoys = ['44009', '44017', '44025', '44065']  # New York Bight buoys

lats = []
lons = []
for b in buoys:
    buoy_catalog = ['https://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/{}/catalog.html'.format(b)]
    datasets = cf.get_nc_urls(buoy_catalog)
    f = datasets[-1]  # get the lat and lon from the most recent file for that buoy
    ds = xr.open_dataset(f, mask_and_scale=False)
    lats.append(ds['latitude'].values[0])
    lons.append(ds['longitude'].values[0])

# plot
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines(resolution='50m')

ax.set_extent([-76, -68, 36, 42])  # [min lon, max lon, min lat, max lat]
#ax.set_extent([-76, -70, 37, 42])  # [min lon, max lon, min lat, max lat]

gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=.5, color='gray', alpha=0.5, linestyle='--')
gl.xlabels_top = False
gl.ylabels_right = False
gl.xlabel_style = {'size': 12}
gl.ylabel_style = {'size': 12}
land = cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='gainsboro')
ax.add_feature(land, zorder=5, edgecolor='black')
ax.add_feature(cfeature.LAKES, zorder=8, facecolor='white')
ax.add_feature(cfeature.BORDERS, zorder=6)
state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none')
ax.add_feature(state_lines, zorder=7, edgecolor='black')


# xticks = np.arange(round(min(lons)) - 2, round(max(lons)) + 2, 2)
# yticks = np.arange(round(min(lats)) - 2, round(max(lats)) + 2, 2)
# ax.set_xticks(xticks, crs=ccrs.PlateCarree())
# ax.set_yticks(yticks, crs=ccrs.PlateCarree())

# change font size of tick labels
# for tick in ax.xaxis.get_majorticklabels():
#     tick.set_fontsize(8)
#
# for tick in ax.yaxis.get_majorticklabels():
#     tick.set_fontsize(8)

plt.scatter(lons, lats, c='b', s=10)

# add the buoy labels
for i, txt in enumerate(buoys):
    #ax.annotate(txt, (lons[i] + .2, lats[i] - .05), size=6)
    ax.annotate(txt, (lons[i] + .1, lats[i]), size=7)

pf.save_fig(sDir, 'ndbc_buoy_locations_midatlantic')