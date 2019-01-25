#!/usr/bin/env python
"""
Created on Jan 17 2019 by Lori Garzio
@brief This is a wrapper script that imports tools to plot comparisons of buoy and historical NREL data
@usage
sDir: location to save plots
avgrad: radius around the buoy from which to grab satellite data. options: x (average all data within radius x km of
the buoy), 'closest' (grabs the closest data point), 'closestwithinx' (get the closest non-nan measurement as long as
it is within x km of the buoy
start: list of start times. options: date, int (if int, looks at t1 back t0 days)
end: list of end times. options: date, int (if int, looks at t0 forward t1 days), 'today', 'yesterday'
"""

import datetime as dt
import pandas as pd
import scripts


sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
avgrad = 'closestwithin5'
series = 'monthly'

buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
         '44017', '44018', '44020', '44025', '44027', '44065']

start = '6-1-2015'   # 14  # '01-14-2019'
end = '5-31-2016'  # 'today'  # '01-16-2019'

if series == 'monthly':
    dt_start = dt.datetime.strptime(start, '%m-%d-%Y')
    dt_end = dt.datetime.strptime(end, '%m-%d-%Y')
    start_dates = [dt_start.strftime('%m-%d-%Y')]
    end_dates = []
    ts1 = dt_start
    while ts1 <= dt_end:
        ts2 = ts1 + dt.timedelta(days=1)
        if ts2.month != ts1.month:
            start_dates.append(ts2.strftime('%m-%d-%Y'))
            end_dates.append(ts1.strftime('%m-%d-%Y'))
        ts1 = ts2

    end_dates.append(dt_end.strftime('%m-%d-%Y'))

else:
    start_dates = [start]
    end_dates = [end]

headers = ['buoy', 'year-month', 'mean_buoy', 'sd_buoy', 'mean_nrel', 'sd_nrel', 'RMSE', 'n', 'diff (sat-buoy)']
summary = []
for b in buoys:
    print('\nBuoy: {}'.format(b))
    for startdt, enddt in zip(start_dates, end_dates):
        [mean_buoy, mean_nrel, sd_buoy, sd_nrel, diff, rmse, n] = scripts.sat_buoy_comparison_nrel.main(startdt, enddt,
                                                                                                        b, avgrad, sDir)
        if mean_buoy:
            year_month = ''.join((startdt.split('-')[-1], startdt.split('-')[0]))
            summary.append([b, year_month, mean_buoy, sd_buoy, mean_nrel, sd_nrel, rmse, n, diff])

sdf = pd.DataFrame(summary, columns=headers)
sdf.to_csv('{}/{}/NREL_buoy_comparison.csv'.format(sDir, 'NREL'), index=False)
