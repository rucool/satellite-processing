from sys import argv, exit
script, template_file = argv

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from netCDF4 import Dataset
import numpy as np
# import time
# import xarray as xr

minlat=31
maxlat=47.33
minlon=-83.25
maxlon=-56.9

murlink='http://basin.ceoe.udel.edu/thredds/dodsC/NASAMURSST.nc';
mur=Dataset(murlink,'r')
lon=mur.variables['lon']
lat=mur.variables['lat']
mask=mur.variables['mask']
times=mur.variables['time']
dims=mur.dimensions
mur_global_atts=mur.__dict__
lon_atts=lon.__dict__
lat_atts=lat.__dict__
mask_atts=mask.__dict__
times_atts=times.__dict__

lon_data=lon[:]
lat_data=lat[:]
mask_new=mask[-1,np.logical_and(lat_data>=minlat,lat_data<=maxlat),np.logical_and(lon_data>=minlon,lon_data<=maxlon)]
mur.close()

lon_new=lon_data[(lon_data>=minlon) & (lon_data<=maxlon)]
lat_new=lat_data[(lat_data>=minlat) & (lat_data<=maxlat)]
#mask_new=mask_data[[(lat_data>=minlat) & (lat_data<=maxlat)]]
#mask_new=mask_new[:,(lon_data>=minlon) & (lon_data<=maxlon)]
mask_new[mask_new>2]=1
mask_new=mask_new-1


temp=Dataset(template_file,"w",format="NETCDF4")

# define dimensions
lat_dim=temp.createDimension('lat',len(lat_new))
lon_dim=temp.createDimension('lon',len(lon_new))
time_dim=temp.createDimension('time',None)
z_dim=temp.createDimension('z',1)

# define variables
time_var=temp.createVariable('time','f8',('time',),zlib=True,least_significant_digit=0)
lon_var=temp.createVariable('lon','f4',('lon',))#,zlib=True,complevel=4)
lat_var=temp.createVariable('lat','f4',('lat',))#,zlib=True,complevel=4)
z_var=temp.createVariable('z','f4',('z',))#,zlib=True,complevel=4)
mask_var=temp.createVariable('mask','i1',('lat','lon',),zlib=True,complevel=4)
sst_var=temp.createVariable('sst','f4',('time','z','lat','lon',),fill_value=-999,zlib=True,complevel=4)
flag_var=temp.createVariable('sst_qc_flag','i4',('time','z','lat','lon',),fill_value=-1,zlib=True,complevel=4)
platform_var=temp.createVariable('platform',str,(),zlib=True,complevel=4)
start_var=temp.createVariable('composite_start_time','i1',('time',),fill_value=-1,zlib=True,complevel=4)
end_var=temp.createVariable('composite_end_time','i1',('time',),fill_value=-1,zlib=True,complevel=4)
passes_var=temp.createVariable('included_passes',str,('time',),fill_value='none',zlib=True,complevel=4)
sun_var=temp.createVariable('minimum_sun_angle','i1',('time',),fill_value=-99,zlib=True,complevel=4)

# global attributes (temp)
temp.ncei_template_version='NCEI_NetCDF_Grid_Template_v2.0'
temp.title='Daily Daylight-Hours AVHRR Coldest Pixel Composite'
temp.summary=['This product is a daily coldest pixel composite using NOAA-AVHRR ' +
    'satellite SST declouded based on reflectivity in the visible spectrum. ' +
    'This method of declouding is limited to daylight hours, but ' +
    'lets in cold water that often gets flagged as clouds based on other ' +
    'declouding algorithms, making this product a useful tool for ' +
    'identifying upwelling regions and storm cooling earlier than ' +
    'they are typically seen in other SST products.']
temp.keywords=mur_global_atts['keywords']
temp.keywords_vocabulary=mur_global_atts['keywords_vocabulary']
temp.Conventions='CF-1.6, ACDD-1.3'
temp.naming_authority='edu.rutgers.marine'
temp.history=''
temp.source='NOAA-AVHRR'
temp.processing_level=['declouded based on visible reflectivity and ' +
    'composited (coldest-pixel) over 24 hours (daylight only)']
temp.comment=["Timestamps with data provided in 'composite_start_time' " +
    "and 'composite_end_time' define daylight hours as all data within that " +
    "time window. Timestamps with data provided in 'minimum_sun_angle' " +
    "defined daylight on a pixel-by-pixel basis dependent on the sun angle " +
    "at that point and time. Data is regridded to a subset of the " +
    "MUR SST grid."]
temp.acknowledgment="This product supported by the Board of Public Utilities."
temp.standard_name_vocabulary='CF Standard Name Table v52'
temp.date_created=''
temp.creator_name='Laura Nazzaro'
temp.creator_email='nazzaro@marine.rutgers.edu'
temp.creator_url='rucool.marine.rutgers.edu'
temp.institution='Rutgers University'
temp.ioos_regional_association='MARACOOS'
temp.project=''
temp.publisher_name='Laura Nazzaro'
temp.publisher_email='nazzaro@marine.rutgers.edu'
temp.publisher_url='rucool.marine.rutgers.edu'
temp.spatial_resolution=mur_global_atts['spatial_resolution']
temp.geospatial_lat_min=minlat
temp.geospatial_lat_max=maxlat
temp.geospatial_lat_resolution=mur_global_atts['geospatial_lat_resolution']
temp.geospatial_lat_units='degree_north'
temp.geospatial_lon_min=minlon
temp.geospatial_lon_max=maxlon
temp.geospatial_lon_resolution=mur_global_atts['geospatial_lon_resolution']
temp.geospatial_lon_units='degree_east'
temp.time_coverage_start=''
temp.time_coverage_end=''
temp.time_coverage_duration='1 day'
temp.time_coverage_resolution='1 day'
temp.sea_name='Mid-Atlantic Bight'
temp.contributor_name="Scott Glenn, Travis Miles, Michael Crowley, Joe Brodie, Laura Nazzaro"
temp.contributor_role="Principal Investigator, Principal Investigator, Satellite Operations, Director of Atmospheric Research, Data Manager"
temp.date_created=''
temp.date_modified=''
temp.cdm_data_type='Grid'
temp.metadata_link=''
temp.references=''

# time attributes (time_var)
time_var.long_name=times_atts['long_name']
time_var.standard_name='time'
time_var.units=times_atts['units']
time_var.calendar='gregorian'
time_var.axis='T'
time_var.comment='timestamp is end time of 24h composite'

# lon attributes (lon_var)
lon_var.long_name=lon_atts['long_name']
lon_var.standard_name='longitude'
lon_var.units='degree_east'
lon_var.axis='X'
lon_var.valid_min=lon_atts['valid_min']
lon_var.valid_max=lon_atts['valid_max']
lon_var.comment='subset of the MUR SST grid'

# lat attributes (lat_var)
lat_var.long_name=lat_atts['long_name']
lat_var.standard_name='latitude'
lat_var.units='degree_north'
lat_var.axis='Y'
lat_var.valid_min=lat_atts['valid_min']
lat_var.valid_max=lat_atts['valid_max']
lat_var.comment='subset of the MUR SST grid'

# z attributes(z_var)
z_var.long_name='depth of measurement'
z_var.standard_name='depth'
z_var.units='m'
z_var.axis='Z'
z_var.positive='down'
z_var.comment='all measurements are at surface'

# mask attributes (mask_var)
mask_var.long_name='sea/land mask'
mask_var.standard_name='land_binary_mask'
mask_var.flag_values=np.array(range(2))
mask_var.flag_meanings='0=water, 1=land'
mask_var.coordinates='lon lat'
mask_var.comment=["subset of MUR SST mask; " +
    "MUR's open-sea, open-lake, open-sea with ice in the grid, " +
    "and open-lake with ice in the grid are all combined " +
    "here as 'water'."]

# sst attributes (sst_var)
sst_var.long_name='coldest pixel composite sea surface temperature'
sst_var.short_name='sst'
sst_var.standard_name='sea_surface_temperature'
sst_var.units='degrees Celsius'
sst_var.coordinates='lon lat z time'
sst_var.source='NOAA-AVHRR'
sst_var.platform='platform'
sst_var.comment=['daily coldest-pixel composite of SST from NOAA-' +
    'AVHRR satellites declouded based on visible reflectivity']
sst_var.ancillary_variables='included_passes, sst_qc_flag'

# flag attributes (flag_var)
flag_var.standard_name='sea_surface_temperature_status_flag'
flag_var.long_name='sea surface temperature quality control flag'
flag_var.flag_masks=''
flag_var.flag_meanings=''
flag_var.comment='placeholder for future quality control measures'

# platform attributes (platform_var)
platform_var.long_name='NOAA-AVHRR satellites'
platform_var.comments=["specific satellites used in each composite are " +
    "listed in 'included_passes' variable"]

# start timing attributes (start_var)
start_var.long_name='earliest pass timestamp allowed in composite'
start_var.units='hours'
start_var.comment=["timestamp GMT; " +
    "if timestamp given, composite is based on " +
    "defined time window for included passes; if -999, included " +
    "data is based on sun angle (see 'minimum_sun_angle')"]
start_var.ancillary_variables='composite_end_time, included_passes'

# end timing attributes (end_var)
end_var.long_name='latest pass timestamp allowed in composite'
end_var.units='hours'
end_var.comment=["timestamp GMT; " +
    "if timestamp given, composite is based on " +
    "defined time window for included passes; if -999, included " +
    "data is based on sun angle (see 'minimum_sun_angle')"]
end_var.ancillary_variables='composite_start_time, included_passes'

# pass information attributes (passes_var)
passes_var.long_name='list of AVHRR passes included in composite'
passes_var.comment=["list of all satellite passes (satellite name and pass time) " +
    "with any data included in composite (if based on time window - see " +
    "'composite_start_time' and 'composite_end_time', entire pass is included; " +
    "if based on sun angle - see 'minimum_sun_angle', only part of each " +
    "pass may be included"]
passes_var.ancillary_variables='composite_start_time, composite_end_time, minimum_sun_angle'

# sun angle attributes (sun_var)
sun_var.long_name='minimum sun angle required to include a data point in composite'
sun_var.units='degrees'
sun_var.comment=["if provided, all data points, regardless of time of day, " +
    "are included in composite if sun angle at a given pixel is grater than " +
    "given number; if -999, included data is based on defined time window " +
    "for satellite passes (see 'composite_start_time' and 'composite_end_time')"]


# write variables
# fill in time later
lon_var[:]=lon_new
lat_var[:]=lat_new
z_var[:]=0
mask_var[:,:]=mask_new
# sst filled with nans
# flag filled with nans
platform_var[0]='NOAA-AVHRR'
# start time filled with nans
# end time filled with nans
# fill in pass list later
# minimum sun angle filled with nans


temp.close()
exit()
