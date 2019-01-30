#!/usr/bin/env python
"""
@author Laura Nazarro
@modified by Lori Garzio on 1/8/2019
@brief Create daily composite coldest pixel netCDF files for historical AVHRR satellite data (from 9/1/2013 to 9/19/2018)
"""

from netCDF4 import date2num, Dataset
import numpy as np
import time
import subprocess
import os
from datetime import datetime, timedelta
from mpl_toolkits.basemap import interp
import functions.common as cf

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# daylight hours limits for each month
H0_lst = [14, 14, 13, 13, 12, 12, 12, 12, 13, 13, 14, 14]
H1_lst = [20, 20, 20, 22, 22, 23, 23, 23, 21, 20, 20, 20]

#template_file = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/daily_avhrr/templates/wrf_9km_template.nc'
template_file = '/Users/lgarzio/Documents/rucool/satellite/coldest_pixel//wrf_9km_template.nc'
avhrr_dir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/'
out_dir = '/Users/lgarzio/Documents/rucool/satellite/coldest_pixel/daily_avhrr/composites'
start_date = datetime(2013, 9, 1)
end_date = datetime(2018, 9, 20)

for n in range(int((end_date - start_date).days)):
    d = start_date + timedelta(n)
    yr = d.year
    save_dir = os.path.join(out_dir, str(d.year))
    cf.create_dir(save_dir)
    dd = datetime.strftime(d, '%y%m%d')
    avhrr_files = []
    for file in os.listdir(avhrr_dir):
        if file.startswith(dd) and file.endswith('.CF.nc'):
            avhrr_files.append(os.path.join(avhrr_dir, file))
    print(avhrr_files)
    if len(avhrr_files) > 0:
        print('\nProcessing files: {}'.format(datetime.strftime(d, '%Y-%m-%d')))
        out_file = os.path.join(save_dir, 'avhrr_coldest-pixel_{}.nc'.format(datetime.strftime(d, '%Y%m%d')))

        # select pre-defined daylight hour limits for that month
        H0 = H0_lst[d.month - 1]
        H1 = H1_lst[d.month - 1]

        # copy the template file with the new file name
        subprocess.call("cp " + template_file + " " + out_file, shell=True)

        sst_file = Dataset(out_file, "a")
        lon = sst_file.variables['lon']
        lat = sst_file.variables['lat']

        lonx, laty = np.meshgrid(lon[:], lat[:])

        pass_info = ''
        minT = np.empty(np.shape(lonx))
        minT[:] = np.nan

        for avhrr in avhrr_files:
            print("processing", avhrr)
            passH = avhrr[-18:-16]
            passM = avhrr[-16:-14]
            passS = avhrr[-12:-10]

            if int(passH) >= H0 and int(passH) < H1:
                pass_info = pass_info + "NOAA-" + passS + " " + passH + ":" + passM + "GMT, "
                avhrr_data = Dataset(avhrr, "r+")
                avhrrlon = avhrr_data.variables['lon']
                avhrrlat = avhrr_data.variables['lat']
                # turns it into a 2D matrix (gets rid of the time dimension)
                avhrrsst = np.squeeze(avhrr_data.variables['mcsst'])
                avhrrsst_data = avhrrsst[:]
                avhrrsst_data[avhrrsst_data == -999] = np.nan
                try:
                    # if some lons are masked
                    if True in avhrrlon[:].mask:
                        avhrrsst_data = avhrrsst_data[:, ~avhrrlon[:].mask]
                        avhrrlon = avhrrlon[~avhrrlon[:].mask]
                except:
                    pass
                try:
                    # if some lats are masked
                    if True in avhrrlat[:].mask:
                        avhrrsst_data = avhrrsst_data[~avhrrlat[:].mask, :]
                        avhrrlat = avhrrlat[~avhrrlat[:].mask]
                except:
                    pass

                # reverse the data array if the lat values are descending
                if avhrrlat[0] > avhrrlat[-1]:
                    avhrrlat[:] = avhrrlat[::-1]
                    avhrrsst_data = avhrrsst_data[::-1, :]
                # reverse the data array if the lon values are descending
                if avhrrlon[0] > avhrrlon[-1]:
                    avhrrlon[:] = avhrrlon[::-1]
                    avhrrsst_data = avhrrsst_data[:, ::-1]

                regrid_sst = interp(avhrrsst_data[:], avhrrlon[:], avhrrlat[:], lonx, laty)
                regrid_sst[lonx > np.max(avhrrlon[:])] = np.nan
                regrid_sst[lonx < np.min(avhrrlon[:])] = np.nan
                regrid_sst[laty > np.max(avhrrlat[:])] = np.nan
                regrid_sst[laty < np.min(avhrrlat[:])] = np.nan
                minT = np.fmin(minT, regrid_sst)
                avhrr_data.close()

        # add time
        out_time = sst_file.variables['time']
        out_time[0] = date2num(d, units=out_time.units, calendar=out_time.calendar)
        # add sst
        out_sst = sst_file.variables['sst']
        minT[np.isnan(minT)] = -999
        out_sst[0, 0, :, :] = minT
        # add start time
        out_start = sst_file.variables['composite_start_time']
        out_start[:] = H0
        # add end time
        out_end = sst_file.variables['composite_end_time']
        out_end[:] = H1
        # add included passes
        out_passes = sst_file.variables['included_passes']
        out_passes[0] = pass_info[:-2]

        # add date and time info to metadata
        sst_file.date_created = time.strftime("%B-%d-%Y GMT", time.gmtime())
        sst_file.time_coverage_start = d.strftime("%B-%d-%Y 00:00")
        sst_file.time_coverage_end = d.strftime("%B-%d-%Y 23:59")
        sst_file.date_modified = time.strftime("%B-%d-%Y GMT", time.gmtime())
        sst_file.history = ["Created " + time.strftime("%B-%d-%Y GMT", time.gmtime())]
        sst_file.contributor_name = sst_file.contributor_name + ', Lori Garzio'
        sst_file.contributor_role = sst_file.contributor_role + ', Data Manager'

        sst_file.close()
