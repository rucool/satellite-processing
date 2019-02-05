#!/usr/bin/env python
"""
Created on Jan 25 2019 by Lori Garzio
@brief plot buoy locations
"""

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import itertools
import numpy as np
import os
import requests
import re
import xarray as xr
import functions.plotting as pf


def get_nc_urls(catalog_urls):
    """
    Return a list of urls to access netCDF files in THREDDS
    :param catalog_urls: List of THREDDS catalog urls
    :return: List of netCDF urls for data access
    """
    tds_url = 'https://dods.ndbc.noaa.gov/thredds/dodsC'
    datasets = []
    for i in catalog_urls:
        dataset = requests.get(i).text
        ii = re.findall(r'href=[\'"]?([^\'" >]+)', dataset)
        x = re.findall(r'(data/.*?.nc)', dataset)
        for i in x:
            if i.endswith('.nc') == False:
                x.remove(i)
        for i in x:
            try:
                float(i[-4])
            except:
                x.remove(i)
        dataset = [os.path.join(tds_url, i) for i in x]
        datasets.append(dataset)
    datasets = list(itertools.chain(*datasets))
    return datasets


sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
         '44017', '44018', '44020', '44025', '44027', '44065']

lats = []
lons = []
for b in buoys:
    buoy_catalog = ['https://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/{}/catalog.html'.format(b)]
    datasets = get_nc_urls(buoy_catalog)
    f = datasets[-1]  # get the lat and lon from the most recent file for that buoy
    ds = xr.open_dataset(f, mask_and_scale=False)
    lats.append(ds['latitude'].values[0])
    lons.append(ds['longitude'].values[0])

# plot
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines(resolution='50m')
xticks = np.arange(round(min(lons)) - 2, round(max(lons)) + 2, 2)
yticks = np.arange(round(min(lats)) - 2, round(max(lats)) + 2, 2)
ax.set_xticks(xticks, crs=ccrs.PlateCarree())
ax.set_yticks(yticks, crs=ccrs.PlateCarree())

# change font size of tick labels
for tick in ax.xaxis.get_majorticklabels():
    tick.set_fontsize(8)

for tick in ax.yaxis.get_majorticklabels():
    tick.set_fontsize(8)

plt.scatter(lons, lats, c='b', s=8)

# add the buoy labels
for i, txt in enumerate(buoys):
    ax.annotate(txt, (lons[i] + .2, lats[i] - .05), size=6)

pf.save_fig(sDir, 'ndbc_buoy_locations')