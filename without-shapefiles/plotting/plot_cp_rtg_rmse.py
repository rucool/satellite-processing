#!/usr/bin/env python
"""
Create by Lori Garzio on 1/16/2019
@brief plot RMSE stats from different models compared to buoy measurements
@usage
"""


import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import datetime as dt
import numpy as np
import os
import functions.plotting as pf
pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console


sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/20190503/2018_analysis/'
rtgdf = pd.read_csv(os.path.join(sDir, 'rtg', 'rtg_buoy_comparison.csv'))
rtgstatsdf = pd.read_csv(os.path.join(sDir, 'rtg', 'rtg_buoy_comparison_overallstats.csv'))
cpdf = pd.read_csv(os.path.join(sDir, 'coldestpix', 'coldestpix_buoy_comparison.csv'))
cpstatsdf = pd.read_csv(os.path.join(sDir, 'coldestpix', 'coldestpix_buoy_comparison_overallstats.csv'))

ttl_size = 12
tick_size = 10.5
ylabel_size = 11
legend_fontsize = 8
sample_size = 3

# plot RMSEs with shaded regions for min and max RMSE
# RTG
rtgx = rtgstatsdf['year-month'][:-1].map(lambda t: dt.datetime.strptime(str(t), '%Y%m'))
rtgmonthly_rmse = rtgstatsdf['RMSE'][:-1]

monthly_data = {}
months = np.unique(rtgdf['year-month']).tolist()
for month in months:
    sdf_month = rtgdf[(rtgdf['year-month'] == month) & (rtgdf['n'] > sample_size)]
    if len(sdf_month) > 0:
        monthly_data[month] = dict(rmse_min=np.nanmin(sdf_month['RMSE']), rmse_max=np.nanmax(sdf_month['RMSE']))

rtgmdf = pd.DataFrame.from_dict(monthly_data, orient='index')
fig, ax = plt.subplots()
ax.plot(rtgx, rtgmonthly_rmse, '.', markersize=6, color='blue', linestyle='-', label='RTG')
ax.fill_between(np.array(rtgx), rtgmdf['rmse_min'], rtgmdf['rmse_max'], color='blue', alpha=.2, label='Buoy Range')

# Coldest Pixel
cpx = cpstatsdf['year-month'][:-1].map(lambda t: dt.datetime.strptime(str(t), '%Y%m'))
cpmonthly_rmse = cpstatsdf['RMSE'][:-1]

monthly_data = {}
months = np.unique(cpdf['year-month']).tolist()
for month in months:
    sdf_month = cpdf[(cpdf['year-month'] == month) & (cpdf['n'] > sample_size)]
    if len(sdf_month) > 0:
        monthly_data[month] = dict(rmse_min=np.nanmin(sdf_month['RMSE']), rmse_max=np.nanmax(sdf_month['RMSE']))

cpmdf = pd.DataFrame.from_dict(monthly_data, orient='index')
fig, ax = plt.subplots()
ax.plot(cpx, cpmonthly_rmse, '.', markersize=6, color='green', linestyle='-', label='Coldest Pixel')
ax.fill_between(np.array(cpx), cpmdf['rmse_min'], cpmdf['rmse_max'], color='green', alpha=.2, label='Buoy Range')

ax.set_ylabel('RMSE', fontsize=ylabel_size)
ax.legend(loc='best', fontsize=legend_fontsize)

pf.format_date_axis_month(ax, fig)
plt.ylim([0, 2.5])
plt.yticks(fontsize=tick_size)
plt.xticks(fontsize=tick_size)
sname = 'cprtg_buoy_monthly_rmse_plot_shade'
pf.save_fig(sDir, sname)






if model == 'AVHRR':
    plt.title('{} Passes vs. Buoy SST'.format(model), fontsize=ttl_size)
else:
    plt.title('{} vs. Buoy SST'.format(model), fontsize=ttl_size)
pf.format_date_axis_month(ax, fig)
plt.ylim([0, 2.5])
plt.yticks(fontsize=tick_size)
plt.xticks(fontsize=tick_size)
sname = '{}_buoy_monthly_rmse_plot_shade'.format(model)
pf.save_fig(sDir, sname)

# plot monthly SST difference between buoy and satellite
median_diff = statsdf['median_diff'][:-1]
q1 = statsdf['q1_diff'][:-1]
q3 = statsdf['q3_diff'][:-1]
fig, ax = plt.subplots()
ax.plot(x, median_diff, '.', markersize=6, color='black', linestyle='-', label='Median')
ax.fill_between(np.array(x), q1, q3, color='lightgray', label='Q1 to Q3')
ax.legend(loc='best', fontsize=legend_fontsize)
ax.axhline(linestyle='--', lw=1)

ax.set_ylabel('Median SST Difference', fontsize=ylabel_size)
if model == 'AVHRR':
    #ttl = '{} individual passes minus buoy SST:\nMedian Monthly Difference with Quartiles'.format(model)
    ttl = '{} Passes Minus Buoy SST'.format(model)
else:
    #ttl = '{} minus buoy SST (from model time period):\nMedian Monthly Difference with Quartiles'.format(model)
    ttl = '{} Minus Buoy SST'.format(model)
plt.title(ttl, fontsize=ttl_size)
pf.format_date_axis_month(ax, fig)
plt.ylim([-1.5, 1.5])
plt.yticks(fontsize=tick_size)
plt.xticks(fontsize=tick_size)
sname = '{}_buoy_monthly_median_difference'.format(model)
pf.save_fig(sDir, sname)

