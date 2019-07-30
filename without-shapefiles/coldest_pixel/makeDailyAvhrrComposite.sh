# convert AVHRR netcdf files
/home/coolgroup/bpu/wrf/code/sh/makeBpuCfNcFiles.sh -x /home/coolgroup/bpu/wrf/data/avhrr_nc/ /home/coolgroup/bpu/wrf/data/avhrr_nc/

# make yearly composite directory, if it doesn't exist
if [ ! -d "/home/coolgroup/bpu/wrf/data/daily_avhrr/composites/$(date +%Y)/" ]; then
    mkdir /home/coolgroup/bpu/wrf/data/daily_avhrr/composites/$(date +%Y)/
fi

# make yearly imagery directory, if it doesn't exist
if [ ! -d "/home/coolgroup/bpu/wrf/data/daily_avhrr/images/$(date +%Y)/" ]; then
    mkdir /home/coolgroup/bpu/wrf/data/daily_avhrr/images/$(date +%Y)/
fi

# set daylight hours limits (H0:00-H1:00, not including hour of H1)
H0=15
H1=20

# create composite
/home/nazzaro/miniconda3/envs/coldest_pixel/bin/python /home/coolgroup/bpu/wrf/code/python/DailyAvhrrColdestPixelComposite_DaylightWindow.py /home/coolgroup/bpu/wrf/data/daily_avhrr/templates/wrf_9km_template.nc /home/coolgroup/bpu/wrf/data/avhrr_nc/ /home/coolgroup/bpu/wrf/data/daily_avhrr/composites/$(date +%Y)/ today $H0 $H1

# create image
/home/nazzaro/miniconda3/envs/coldest_pixel/bin/python /home/coolgroup/bpu/wrf/code/python/PlotColdestPixel.py /home/coolgroup/bpu/wrf/data/daily_avhrr/composites/$(date +%Y)/avhrr_coldest-pixel_$(date +%Y%m%d).nc /home/coolgroup/bpu/wrf/data/daily_avhrr/images/$(date +%Y)/avhrr_coldest-pixel_$(date +%Y%m%d).png

# copy image to public directory
cp /home/coolgroup/bpu/wrf/data/daily_avhrr/images/$(date +%Y)/avhrr_coldest-pixel_$(date +%Y%m%d).png /www/home/nazzaro/public_html/sst/coldest_pixel/daily_avhrr_imgs/



