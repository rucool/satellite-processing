#!/usr/bin/env python
"""
Created on Jan 17 2019 by Lori Garzio
@brief This is a wrapper script that imports tools to plot comparisons of buoy and satellite SST data
@usage
sDir: location to save plots
avgrad: radius around the buoy from which to grab satellite data. options: x (average all data within radius x km of
the buoy), 'closest' (grabs the closest data point), 'closestiwithinx' (get the closest non-nan measurement as long as
it is within x km of the buoy
models: list of models to plot. options: WRFsport_avhrr = plot all three models along with buoy data, WRFonly = plot
WRF input only along with buoy data, WRFsport = plot WRF input and SPoRT models along with buoy data
buoys: list of buoys
start: list of start times. options: date, int (if int, looks at t1 back t0 days)
end: list of end times. options: date, int (if int, looks at t0 forward t1 days), 'today', 'yesterday'
"""

import scripts


sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
avgrad = 'closestwithin5'
models = ['WRFsport_avhrr', 'WRFonly', 'WRFsport']

buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
         '44017', '44018', '44020', '44025', '44027', '44065']

start = [14, '01-01-2019']  # '01-14-2019'
end = ['today', '01-14-2019']  # '01-16-2019'

for b in buoys:
    print('\nBuoy: {}'.format(b))
    for startdt, enddt in zip(start, end):
        scripts.sat_buoy_comparison.main(startdt, enddt, b, avgrad, sDir, models)
