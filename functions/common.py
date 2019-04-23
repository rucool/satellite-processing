#! /usr/bin/env python

from datetime import datetime, timedelta
import numbers
import numpy as np
import os
import xarray as xr
import requests
import re
import itertools
import geopandas as gpd


def append_satellite_sst_data(sat_nc_file, buoylat, buoylon, radius, method, sst_varname):
    value = ''
    satdata = xr.open_dataset(sat_nc_file, mask_and_scale=False)
    if method == 'sport':
        satlon = satdata['lon_0'].values - 360
        satlat = satdata['lat_0'].values
    elif method == 'rtg':
        satlon = satdata['lon_173'].values - 360
        satlat = satdata['lat_173'].values
    else:
        satlon = satdata['lon'].values
        satlat = satdata['lat'].values

    # select data near the buoy
    lon_ind = np.logical_and(satlon > buoylon - 2, satlon < buoylon + 2)
    lat_ind = np.logical_and(satlat > buoylat - 2, satlat < buoylat + 2)
    if (len(np.unique(lon_ind)) == 1 and np.unique(lon_ind)[0] == False) or (len(np.unique(lat_ind)) == 1 and np.unique(lat_ind)[0] == False):
        value = np.nan
    else:
        if method == 'daily_avhrr':
            satsst = np.squeeze(satdata[sst_varname][:, :, lat_ind, lon_ind])
            land_mask = satdata['mask'][lat_ind, lon_ind]  # exclude data over land
            satsst.values[land_mask.values == 1] = np.nan
            satsst.values[satsst == satdata[sst_varname]._FillValue] = np.nan  # turn fill values to nans
            lonx, laty = np.meshgrid(satlon[lon_ind], satlat[lat_ind])
        elif method == 'cold_sport':
            satsst = np.squeeze(satdata[sst_varname][:, lon_ind, lat_ind])
            satsst.values[satsst == satdata[sst_varname]._FillValue] = np.nan  # turn fill values to nans
            laty, lonx = np.meshgrid(satlat[lat_ind], satlon[lon_ind])
        elif method in ['sport', 'rtg']:
            satsst = np.squeeze(satdata[sst_varname][lat_ind, lon_ind])
            satsst.values[satsst == satdata[sst_varname]._FillValue] = np.nan  # turn fill values to nans
            satsst.values[satsst == -9999] = np.nan
            satsst.values = satsst.values - 273.15  # convert K to C
            lonx, laty = np.meshgrid(satlon[lon_ind], satlat[lat_ind])
        elif method == 'nrel':
            satsst = np.squeeze(satdata[sst_varname][lon_ind, lat_ind])
            satsst.values[satsst == satdata[sst_varname]._FillValue] = np.nan  # turn fill values to nans
            laty, lonx = np.meshgrid(satlat[lat_ind], satlon[lon_ind])
        elif method == 'avhrr':
            satsst = np.squeeze(satdata[sst_varname][:, lat_ind, lon_ind])
            # if the array is all fill values, return nan
            if (len(np.unique(satsst.values)) == 1 and np.unique(satsst.values)[0] == satdata[sst_varname]._FillValue):
                value = np.nan
            else:
                satsst.values[satsst == satdata[sst_varname]._FillValue] = np.nan  # turn fill values to nans
                lonx, laty = np.meshgrid(satlon[lon_ind], satlat[lat_ind])

        if value == '':  # if value hasn't been defined yet
            d = haversine_dist(buoylon, buoylat, lonx, laty)

            # define the distance envelope and find the closest data point(s)
            if isinstance(radius, numbers.Number):
                dist_satsst = satsst.values[d <= radius]
                if check_nans(dist_satsst) == 'valid':
                    value = np.nanmean(satsst.values[d <= radius])
                else:
                    value = np.nan

            elif radius == 'closest':
                dist_satsst = satsst.values[d == np.nanmin(d)]
                if check_nans(dist_satsst) == 'valid':
                    d[np.isnan(satsst.values)] = np.nan  # turn distance to nan if the value at that location is nan
                    value = np.nanmean(satsst.values[d == np.nanmin(d)])
                else:
                    value = np.nan

            elif 'closestwithin' in radius:
                dist = np.float(radius.split('closestwithin')[-1])
                dist_satsst = satsst.values[d <= dist]
                if check_nans(dist_satsst) == 'valid':
                    d[np.isnan(satsst.values)] = np.nan  # turn distance to nan if the value at that location is nan
                    value = np.nanmean(satsst.values[d == np.nanmin(d)])
                else:
                    value = np.nan

            else:
                print('Invalid SST averaging option provided.')

    satdata.close()
    return value


def boem_shapefiles(boem_rootdir):
    shape_file_lease = os.path.join(boem_rootdir, 'BOEM_Lease_Areas_10_24_2018.shp')
    shape_file_plan = os.path.join(boem_rootdir, 'BOEM_Wind_Planning_Areas_10_24_2018.shp')
    leasing_areas = gpd.read_file(shape_file_lease)
    leasing_areas = leasing_areas.to_crs(crs={'init': 'epsg:4326'})
    planning_areas = gpd.read_file(shape_file_plan)
    planning_areas = planning_areas.to_crs(crs={'init': 'epsg:4326'})

    return leasing_areas, planning_areas


def check_nans(data_array):
    if sum(np.isnan(data_array)) != len(data_array):
        status = 'valid'
    else:
        status = 'all_nans'

    return status


def create_dir(new_dir):
    # create new directory if it doesn't exist
    if not os.path.isdir(new_dir):
        try:
            os.makedirs(new_dir)
        except OSError:
            if os.path.exists(new_dir):
                pass
            else:
                raise


def format_dates(dt):
    if dt == 'today':
        dt = datetime.now()
    elif dt == 'yesterday':
        dt = datetime.now()-timedelta(days=1)
    else:
        dt = datetime.strptime(dt, "%m-%d-%Y")
    return dt


def get_buoy_locations(buoy_list):
    buoy_lats, buoy_lons = [], []
    for b in buoy_list:
        buoy_catalog = ['https://dods.ndbc.noaa.gov/thredds/catalog/data/stdmet/{}/catalog.html'.format(b)]
        buoy_datasets = get_nc_urls(buoy_catalog)
        bf = buoy_datasets[-1]  # get the lat and lon from the most recent file for that buoy
        buoy_ds = xr.open_dataset(bf, mask_and_scale=False)
        buoy_lats.append(buoy_ds['latitude'].values[0])
        buoy_lons.append(buoy_ds['longitude'].values[0])

    return buoy_lats, buoy_lons


def get_buoy_data(buoy_name, all_years, t0, t1):
    # get buoy SST for entire time range
    buoy_dict = {'t': np.array([], dtype='datetime64[ns]'), 'sst': np.array([]), 'sst_units': '',
                 'lon': '', 'lat': ''}
    for y in all_years:
        buoy_fname = 'h'.join((buoy_name, str(y)))
        buoydap = 'https://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/{}/{}{}'.format(buoy_name, buoy_fname, '.nc')
        try:
            ds = xr.open_dataset(buoydap, mask_and_scale=False)
            ds = ds.sel(time=slice(t0, t1 + timedelta(days=1)))
            if len(ds['time']) > 0:
                ds_sst = np.squeeze(ds['sea_surface_temperature'].values)
                ds_sst[ds_sst == ds['sea_surface_temperature']._FillValue] = np.nan  # convert fill values to nans
                buoy_dict['t'] = np.append(buoy_dict['t'], ds['time'].values)
                buoy_dict['sst'] = np.append(buoy_dict['sst'], ds_sst)
                buoy_dict['sst_units'] = ds['sea_surface_temperature'].units
                buoy_dict['lon'] = ds['longitude'].values[0]
                buoy_dict['lat'] = ds['latitude'].values[0]
        except OSError:
            print('File does not exist: {}'.format(buoydap))

    return buoy_dict


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


def haversine_dist(blon, blat, slon, slat):
    # return distance (km) from one lon/lat to another (or an entire set)
    R = 6373.0
    blon = blon*np.pi/180
    blat = blat*np.pi/180
    slon = slon*np.pi/180
    slat = slat*np.pi/180
    dlon = slon-blon
    dlat = slat-blat
    a = np.sin(dlat/2)**2+np.cos(blat)*np.cos(slat)*np.sin(dlon/2)**2
    c = 2*np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distance = R*c
    return distance


def range1(start, end):
    return range(start, end+1)


def statistics(observations, predictions):
    ind = (~np.isnan(observations)) & (~np.isnan(predictions))  # get rid of nans
    observations = observations[ind]
    predictions = predictions[ind]

    if len(observations) > 0:
        meano = round(np.mean(observations), 2)
        meanp = round(np.mean(predictions), 2)
        sdo = round(np.std(observations), 2)
        sdp = round(np.std(predictions), 2)

        # satellite minus buoy (predictions minus observations)
        diff = predictions - observations
        #diffx = [round(x, 2) for x in diff]
        rmse = round(np.sqrt(np.mean(diff ** 2)), 2)
        n = len(observations)
    else:
        meano = None
        meanp = None
        sdo = None
        sdp = None
        diff = None
        rmse = None
        n = 0

    return meano, meanp, sdo, sdp, diff, rmse, n
