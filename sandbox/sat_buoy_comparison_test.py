
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from netCDF4 import date2num, Dataset, num2date
import numbers
import glob

#buoy='44009'
buoy='44007'
#t0=14
#t1='today'
t0 = '01-14-2019'
t1 = '01-16-2019'
avgrad='closestwithin25'
imgname='/Users/nazzaro/Desktop/sst_buoy_comp_test2_DELETE.png'

bpudatadir='/Volumes/boardwalk/coolgroup/bpu/wrf/data/'

# regular avhrr, mur, aqua, viirs, aqua filled, viirs filled, godae, goes, rtg
# espresso/doppio

try:
    avgrad=int(avgrad)
except: pass

# see if t0 is an integer indicating number of days to go back from t1
try:
    t0=int(t0)
except: pass
# see if t1 is an integer indicating number of days to go forward from t0
try:
    t1=int(t1)
except: pass

# if t0 is not integer, define date
if not isinstance(t0,int):
    if t0=='today':
        t0=datetime.now()
    elif t0=='yesterday':
        t0=datetime.now()-timedelta(days=1)
    else:
        t0=datetime.strptime(t0,"%m-%d-%Y")
# if t1 is not integer, define date
if not isinstance(t1,int):
    if t1=='today':
        t1=datetime.now()
    elif t1=='yesterday':
        t1=datetime.now()-timedelta(days=1)
    else:
        t1=datetime.strptime(t1,"%m-%d-%Y")

# if t0 is integer, redefine as t1-[t0 days]
if isinstance(t0,int):
    t0=t1-timedelta(days=t0)
# if t1 is integer, redefine as t0+[t1 days]
if isinstance(t1,int):
    t1=t0+timedelta(days=t1)

t0=t0.replace(hour=0,minute=0,second=0,microsecond=0)
t1=t1.replace(hour=0,minute=0,second=0,microsecond=0)

# define equation to get distance (km) from one lon/lat to another (or an entire set)
def haversine_dist(blon,blat,slon,slat):
    R = 6373.0
    blon=blon*np.pi/180
    blat=blat*np.pi/180
    slon=slon*np.pi/180
    slat=slat*np.pi/180
    dlon=slon-blon
    dlat=slat-blat
    a=np.sin(dlat/2)**2+np.cos(blat)*np.cos(slat)*np.sin(dlon/2)**2
    c=2*np.arctan2(np.sqrt(a),np.sqrt(1-a))
    distance=R*c
    return distance

# define array of times
times=pd.to_datetime(np.arange(t0,t1+timedelta(days=1),timedelta(days=1)))

all_years=np.unique(times.year)
all_years=np.append(all_years,9999)

# get buoy SST for entire time range
buoytime=[]
buoysst=[]
buoylon=[]
buoylat=[]
for y in all_years:
    buoydap='https://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/'+buoy+'/'+buoy+'h'+str(y)+'.nc'
    try:
        buoydata=Dataset(buoydap,'r+')
        buoydata = Dataset(buoydap)
        if buoylon==[] or buoylat==[]:
            buoylon=buoydata.variables['longitude'][:]
            buoylat=buoydata.variables['latitude'][:]
        time_temp=num2date(buoydata.variables['time'][:],buoydata.variables['time'].units)
        sst_temp=np.squeeze(buoydata.variables['sea_surface_temperature'][:])
        sst_temp[sst_temp==buoydata.variables['sea_surface_temperature']._FillValue]=np.nan
        if len(buoytime)>0:
            sst_temp=sst_temp[time_temp>max(buoytime)]
            time_temp=time_temp[time_temp>max(buoytime)]
        buoysst=np.append(buoysst,sst_temp[np.logical_and(time_temp>=t0,time_temp<t1+timedelta(days=1))])
        buoytime=np.append(buoytime,time_temp[np.logical_and(time_temp>=t0,time_temp<t1+timedelta(days=1))])
        buoydata.close()
    except:
        print('Issue reading from '+buoydap)


buoysst[buoysst==999]=np.nan
if buoytime==[]:
    buoytime=times
    buoysst=np.nan
buoy_full=pd.DataFrame(data={'time': buoytime, 'sst': buoysst})
buoy_daily=pd.DataFrame(data={'time': times, 'sst':np.nan})
buoy_daily=buoy_daily.set_index('time')
buoy_daily_sub=buoy_full.resample('d',on='time').mean().dropna(how='all')
buoy_daily.update(buoy_daily_sub)

# get SST "at" buoy from daily AVHRR-only coldest pixel composite
coldsst=np.empty(np.shape(times))
coldsst[:]=np.nan
for t in times:
    satfile=bpudatadir+'daily_avhrr/composites/'+t.strftime('%Y')+'/'+'avhrr_coldest-pixel_'+t.strftime("%Y%m%d")+'.nc'
    try:
        satdata=Dataset(satfile,'r+')
        satlon=satdata.variables['lon'][:]
        satlat=satdata.variables['lat'][:]
        satsst=np.squeeze(satdata.variables['sst'][:,:,np.logical_and(satlat>buoylat-2,satlat<buoylat+2),np.logical_and(satlon>buoylon-2,satlon<buoylon+2)])
        satsst[satsst==satdata.variables['sst']._FillValue]=np.nan
        lonx,laty=np.meshgrid(satlon[np.logical_and(satlon>buoylon-2,satlon<buoylon+2)],satlat[np.logical_and(satlat>buoylat-2,satlat<buoylat+2)])
        d=haversine_dist(buoylon,buoylat,lonx,laty)
        if isinstance(avgrad,numbers.Number):
            if not all(satsst[d<=avgrad].mask):
                coldsst[times==t]=np.nanmean(satsst[d<=avgrad])
        elif avgrad=='closest':
            if not all(satsst[d == np.nanmin(d)].mask):
                coldsst[times==t]=np.nanmean(satsst[d==np.nanmin(d)])
        elif avgrad[0:len('closestwithin')]=='closestwithin':
            if not all(satsst[d<=np.float(avgrad[len('closestwithin'):])].mask):
                d[satsst.mask]=np.nan
                coldsst[times==t]=np.nanmean(satsst[d==np.nanmin(d)])
        else:
            print('Invalid SST averaging option provided.')
        satdata.close()
    except:
        print('Issue reading from '+satfile)

# get SST "at" buoy from 3-day AVHRR + SPoRT coldest pixel composite
coldsportsst=np.empty(np.shape(times))
coldsportsst[:]=np.nan
for t in times:
    if t>=datetime.strptime("01-01-2017","%m-%d-%Y"):
        sat_pre=bpudatadir+'composites/procdate_'
    else:
        sat_pre=bpudatadir+'composites/archive_no_time_field/sport_'
    satfile=glob.glob(sat_pre+t.strftime("%Y%m%d")+"*.nc")
    if len(satfile)!=1:
        print(str(len(satfile))+' files found for SPoRT+AVHRR at time '+t.strftime('%Y-%m-%d'))
        continue
    try:
        satdata=Dataset(satfile[0],'r+')
        satlon=satdata.variables['lon'][:]
        satlat=satdata.variables['lat'][:]
        satsst=np.squeeze(satdata.variables['sst'][:,np.logical_and(satlon>buoylon-2,satlon<buoylon+2),np.logical_and(satlat>buoylat-2,satlat<buoylat+2)])
        satsst[satsst==satdata.variables['sst']._FillValue]=np.nan
        laty,lonx=np.meshgrid(satlat[np.logical_and(satlat>buoylat-2,satlat<buoylat+2)],satlon[np.logical_and(satlon>buoylon-2,satlon<buoylon+2)])
        d=haversine_dist(buoylon,buoylat,lonx,laty)
        if isinstance(avgrad,numbers.Number):
            if not all(satsst[d<=avgrad].mask):
                coldsportsst[times==t]=np.nanmean(satsst[d<=avgrad])
        elif avgrad=='closest':
            if not all(satsst[d == np.nanmin(d)].mask):
                coldsportsst[times==t]=np.nanmean(satsst[d==np.nanmin(d)])
        elif avgrad[0:len('closestwithin')]=='closestwithin':
            if not all(satsst[d <= np.float(avgrad[len('closestwithin'):])].mask):
                d[satsst.mask]=np.nan
                coldsportsst[times==t]=np.nanmean(satsst[d==np.nanmin(d)])
        else:
            print('Invalid SST averaging option provided.')
        satdata.close()
    except:
        print('Issue reading from '+satfile[0])

# get SST "at" buoy from SPoRT (on server)
sportsst=np.empty(np.shape(times))
sportsst[:]=np.nan
for t in times:
    satfile=glob.glob(bpudatadir+'sport_nc/'+t.strftime("%Y%m%d")+"*.nc")
    if len(satfile)!=1:
        print(str(len(satfile))+' files found for SPoRT at time '+t.strftime('%Y-%m-%d'))
        continue
    try:
        satdata=Dataset(satfile[0],'r+')
        satlon=satdata.variables['lon_0'][:]-360
        satlat=satdata.variables['lat_0'][:]
        satsst=np.squeeze(satdata.variables['TMP_P0_L1_GLL0'][np.logical_and(satlat>buoylat-2,satlat<buoylat+2),np.logical_and(satlon>buoylon-2,satlon<buoylon+2)])
        satsst[satsst==satdata.variables['TMP_P0_L1_GLL0']._FillValue]=np.nan
        satsst[satsst==-9999]=np.nan
        satsst=satsst-273.15
        lonx,laty=np.meshgrid(satlon[np.logical_and(satlon>buoylon-2,satlon<buoylon+2)],satlat[np.logical_and(satlat>buoylat-2,satlat<buoylat+2)])
        d=haversine_dist(buoylon,buoylat,lonx,laty)
        if isinstance(avgrad,numbers.Number):
            if not all(satsst[d <= avgrad].mask):
                sportsst[times==t]=np.nanmean(satsst[d<=avgrad])
        elif avgrad=='closest':
            if not all(satsst[d==np.nanmin(d)].mask):
                sportsst[times==t]=np.nanmean(satsst[d==np.nanmin(d)])
        elif avgrad[0:len('closestwithin')]=='closestwithin':
            if not all(satsst[d <= np.float(avgrad[len('closestwithin'):])].mask):
                d[satsst.mask]=np.nan
                sportsst[times==t]=np.nanmean(satsst[d==np.nanmin(d)])
        else:
            print('Invalid SST averaging option provided.')
        satdata.close()
    except:
        print('Issue reading from '+satfile[0])

def format_date_axis(axis, figure):
    df = mdates.DateFormatter('%Y-%m-%d')
    axis.xaxis.set_major_formatter(df)
    figure.autofmt_xdate()

def y_axis_disable_offset(axis):
    # format y-axis to disable offset
    y_formatter = ticker.ScalarFormatter(useOffset=False)
    axis.yaxis.set_major_formatter(y_formatter)

if imgname!='none':
    fig,ax=plt.subplots()
    plt.grid()
    ax.plot(buoy_full['time'], buoy_full['sst'], '.', markerfacecolor='grey', markeredgecolor='grey', markersize=1)
    ax.plot(times, buoy_daily['sst'], 'o', markerfacecolor='black', markeredgecolor='black', markersize=5, color='black', linestyle='-', lw=.75)
    ax.plot(times, coldsst, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=5, color='blue', linestyle='-', lw=.75)
    ax.plot(times, coldsportsst, 'v', markerfacecolor='purple', markeredgecolor='purple', markersize=5, color='purple', linestyle='-', lw=.75)
    ax.plot(times, sportsst, '^', markerfacecolor='red', markeredgecolor='red', markersize=5, color='red', linestyle='-', lw=.75)
    ax.set_ylabel('Temperature (Celsius)', fontsize=9)
    format_date_axis(ax,fig)
    y_axis_disable_offset(ax)
    ax.legend(['Buoy '+buoy,'Daily Buoy','Daily Coldest Pixel','Coldest Pixel (SPoRT)','SPoRT'], loc='best', fontsize=6)
    plt.savefig(imgname, dpi=300)
