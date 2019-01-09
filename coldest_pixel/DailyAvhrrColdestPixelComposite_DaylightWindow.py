from sys import argv, exit
script, template_file, avhrr_dir, out_dir, proc_date, H0, H1 = argv

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from netCDF4 import date2num, Dataset
import numpy as np
import time
import subprocess
import glob
from datetime import datetime, timedelta
from mpl_toolkits.basemap import interp


#H0=14
#H1=20
H0=int(H0)
H1=int(H1)

if proc_date=='today':
    proc_date=datetime.now()
elif proc_date=='yesterday':
    proc_date=datetime.now()-timedelta(days=1)
else:
    proc_date=datetime.strptime(proc_date,"%m-%d-%Y")

proc_date=proc_date.replace(hour=23,minute=59,second=0,microsecond=0)

if out_dir[-1]!='/':
    out_dir=[out_dir+'/'][0]
if avhrr_dir[-1]!='/':
    avhrr_dir=[avhrr_dir+'/'][0]

out_file=[out_dir+'avhrr_coldest-pixel_'+proc_date.strftime("%Y%m%d")+".nc"][0]

subprocess.call(["cp "+template_file+" "+out_file][0],shell=True)

sst_file=Dataset(out_file,"a")
lon=sst_file.variables['lon']
lat=sst_file.variables['lat']

lonx,laty=np.meshgrid(lon[:],lat[:])

avhrr_files=glob.glob([avhrr_dir+proc_date.strftime("%y%m%d")+"*.CF.nc"][0])

pass_info=""
minT=np.empty(np.shape(lonx))
minT[:]=np.nan

for avhrr in avhrr_files:
    print("processing",avhrr)
    passH=avhrr[-18:-16]
    passM=avhrr[-16:-14]
    passS=avhrr[-12:-10]
    
    if int(passH)>=H0 and int(passH)<H1:
        pass_info=pass_info + "NOAA-" + passS + " " + passH + ":" + passM + "GMT, "
        avhrr_data=Dataset(avhrr,"r+")
        avhrrlon=avhrr_data.variables['lon']
        avhrrlat=avhrr_data.variables['lat']
        avhrrsst=np.squeeze(avhrr_data.variables['mcsst'])
        avhrrsst_data=avhrrsst[:]
        avhrrsst_data[avhrrsst_data==-999]=np.nan
        try:
            avhrrsst_data=avhrrsst_data[:,~avhrrlon[:].mask]
            avhrrlon=avhrrlon[~avhrrlon[:].mask]
        except:
            pass
        try:
            avhrrsst_data=avhrrsst_data[~avhrrlat[:].mask,:]
            avhrrlat=avhrrlat[~avhrrlat[:].mask]
        except:
            pass
        if avhrrlat[0]>avhrrlat[-1]:
            avhrrlat[:]=avhrrlat[::-1]
            avhrrsst_data=avhrrsst_data[::-1,:]
        if avhrrlon[0]>avhrrlon[-1]:
            avhrrlon[:]=avhrrlon[::-1]
            avhrrsst_data=avhrrsst_data[:,::-1]
        regrid_sst=interp(avhrrsst_data[:],avhrrlon[:],avhrrlat[:],lonx,laty)
        regrid_sst[lonx>np.max(avhrrlon[:])]=np.nan
        regrid_sst[lonx<np.min(avhrrlon[:])]=np.nan
        regrid_sst[laty>np.max(avhrrlat[:])]=np.nan
        regrid_sst[laty<np.min(avhrrlat[:])]=np.nan
        minT=np.fmin(minT,regrid_sst)
        avhrr_data.close()
        
# add time
out_time=sst_file.variables['time']
out_time[0]=date2num(proc_date,units=out_time.units,calendar=out_time.calendar)
# add sst
out_sst=sst_file.variables['sst']
minT[np.isnan(minT)]=-999
out_sst[0,0,:,:]=minT
# add start time
out_start=sst_file.variables['composite_start_time']
out_start[:]=H0
# add end time
out_end=sst_file.variables['composite_end_time']
out_end[:]=H1
# add included passes
out_passes=sst_file.variables['included_passes']
out_passes[0]=pass_info

# add date and time info to metadata
sst_file.date_created=time.strftime("%B-%d-%Y GMT",time.gmtime())
sst_file.time_coverage_start=proc_date.strftime("%B-%d-%Y 00:00")
sst_file.time_coverage_end=proc_date.strftime("%B-%d-%Y 23:59")
sst_file.date_modified=time.strftime("%B-%d-%Y GMT",time.gmtime())
sst_file.history=["Created " + time.strftime("%B-%d-%Y GMT",time.gmtime())]

sst_file.close()
print(proc_date.strftime("%Y%m%d"),"finished.")
exit()
