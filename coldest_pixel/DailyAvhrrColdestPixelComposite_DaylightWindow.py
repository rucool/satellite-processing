from sys import argv, exit
script, template_file, avhrr_dir, out_dir, proc_date, H0, H1 = argv

# suppress warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from netCDF4 import date2num, Dataset
import numpy as np
import time
import subprocess
import os
import glob
from datetime import datetime, timedelta
from mpl_toolkits.basemap import interp


# convert H0 and H1 to numbers
H0=int(H0)
H1=int(H1)

# convert time input to datetime
if proc_date=='today':
    proc_date=datetime.now()
elif proc_date=='yesterday':
    proc_date=datetime.now()-timedelta(days=1)
else:
    proc_date=datetime.strptime(proc_date,"%m-%d-%Y")

# change time to end of day
proc_date=proc_date.replace(hour=23,minute=59,second=0,microsecond=0)

# make sure AVHRR data directory ends in /
if avhrr_dir[-1]!='/':
    avhrr_dir=[avhrr_dir+'/'][0]

# define file name data will be sent to
out_file=os.path.join(out_dir,'avhrr_coldest-pixel_'+proc_date.strftime("%Y%m%d")+'.nc')

# copy template file to out_file
subprocess.call(["cp "+template_file+" "+out_file][0],shell=True)

# open empty file and read in grid
sst_file=Dataset(out_file,"a")
lon=sst_file.variables['lon']
lat=sst_file.variables['lat']

# get 2D lon/lat grids from 1D arrays
lonx,laty=np.meshgrid(lon[:],lat[:])

# list files in AVHRR directory for the processing date
avhrr_files=glob.glob(avhrr_dir+proc_date.strftime("%y%m%d")+'*.CF.nc')

# initialize pass info (individual pass satellite IDs and times) and composite temp variables
pass_info=""
minT=np.empty(np.shape(lonx))
minT[:]=np.nan

for avhrr in avhrr_files:
    print("processing",avhrr)
    passH=avhrr[-18:-16] #hour
    passM=avhrr[-16:-14] #minute
    passS=avhrr[-12:-10] #satelliteID (ie NOAA-19)

    # check if the pass is within the daylight window defined by H0 and H1
    # add pass to composite if it is
    if int(passH)>=H0 and int(passH)<H1:
        pass_info=pass_info + "NOAA-" + passS + " " + passH + ":" + passM + "GMT, "

        # open AVHRR single-pass netcdf file and read grid
        avhrr_data=Dataset(avhrr,"r")
        avhrrlon=avhrr_data.variables['lon'][:]
        avhrrlat=avhrr_data.variables['lat'][:]
        # squeeze SST to remove time dimension and get 2D matrix
        avhrrsst=np.squeeze(avhrr_data.variables['mcsst'])
        avhrrsst_data=avhrrsst[:]
        avhrrsst_data[avhrrsst_data==-999]=np.nan
        try:
            # if any lons are masked, remove them
            if True in avhrrlon[:].mask:
                avhrrsst_data=avhrrsst_data[:,~avhrrlon[:].mask]
                avhrrlon=avhrrlon[~avhrrlon[:].mask]
        except:
            pass
        try:
            # if any lats are masked, remove them
            if True in avhrrlat[:].mask:
                avhrrsst_data=avhrrsst_data[~avhrrlat[:].mask,:]
                avhrrlat=avhrrlat[~avhrrlat[:].mask]
        except:
            pass
        # reverse data array if lat values are descending
        if avhrrlat[0]>avhrrlat[-1]:
            avhrrlat[:]=avhrrlat[::-1]
            avhrrsst_data=avhrrsst_data[::-1,:]
        # reverse data array if lon values are descending
        if avhrrlon[0]>avhrrlon[-1]:
            avhrrlon[:]=avhrrlon[::-1]
            avhrrsst_data=avhrrsst_data[:,::-1]

        # regrid AVHRR pass SST to the output composite grid
        regrid_sst=interp(avhrrsst_data[:],avhrrlon[:],avhrrlat[:],lonx,laty)
        # remove any data artifacts on the new grid that are outside the domain of the AVHRR grid
        regrid_sst[lonx>np.max(avhrrlon[:])]=np.nan
        regrid_sst[lonx<np.min(avhrrlon[:])]=np.nan
        regrid_sst[laty>np.max(avhrrlat[:])]=np.nan
        regrid_sst[laty<np.min(avhrrlat[:])]=np.nan

        # replace any data points in composite grid with data from current
        # AVHRR pass, as long as corresponding data points in the composite
        # are 1) nans or 2) warmer than the new data
        minT=np.fmin(minT,regrid_sst)

        # close AVHRR file
        avhrr_data.close()
        
# add time
out_time=sst_file.variables['time']
out_time[0]=date2num(proc_date,units=out_time.units,calendar=out_time.calendar)
# add sst
out_sst=sst_file.variables['sst']
minT[np.isnan(minT)]=-999
out_sst[0,0,:,:]=minT
# add start time (beginning daylight hour)
out_start=sst_file.variables['composite_start_time']
out_start[:]=H0
# add end time (ending daylight hour)
out_end=sst_file.variables['composite_end_time']
out_end[:]=H1
# add included passes info
out_passes=sst_file.variables['included_passes']
out_passes[0]=pass_info[:-2]

# add date and time info to metadata
sst_file.date_created=time.strftime("%B-%d-%Y %H:%M GMT",time.gmtime())
sst_file.time_coverage_start=proc_date.strftime("%B-%d-%Y 00:00")
sst_file.time_coverage_end=proc_date.strftime("%B-%d-%Y 23:59") # end of day, not end of daylight window
sst_file.date_modified=time.strftime("%B-%d-%Y %H:%M GMT",time.gmtime())
sst_file.history=["Created " + time.strftime("%B-%d-%Y %H:%M GMT",time.gmtime())]

# close composite file, print that process is complete it, and exit Python
sst_file.close()
print(proc_date.strftime("%Y%m%d"),"finished.")
exit()
