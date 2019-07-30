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


def main(sdf, statsdf, sDir, model):
    ttl_size = 12
    tick_size = 10.5
    ylabel_size = 11
    legend_fontsize = 8
    sample_size = 3
    # plot monthly RMSEs for each buoy and overall
    buoys = np.unique(sdf['buoy']).tolist()
    n_buoys = len(buoys)
    print('\n {} buoys'.format(n_buoys))
    colors = cm.rainbow(np.linspace(0, 1, len(buoys)))
    fig, ax = plt.subplots()
    fig.subplots_adjust(right=0.84)
    plt.grid()
    for i in range(len(buoys)):
        sdfb = sdf[(sdf['buoy'] == buoys[i]) & (sdf['n'] > sample_size)]
        if len(sdfb) > 0:
            c = colors[i]
            x = sdfb['year-month'].map(lambda t: dt.datetime.strptime(str(t), '%Y%m'))
            ax.plot(x, sdfb['RMSE'], '.', markersize=3, color=c, linestyle='-', lw=.75, label=str(buoys[i]))

    x = statsdf['year-month'][:-1].map(lambda t: dt.datetime.strptime(str(t), '%Y%m'))
    monthly_rmse = statsdf['RMSE'][:-1]
    ax.plot(x, monthly_rmse, '.', markersize=7, color='black', linestyle='-', lw=2, label='Overall')

    ax.set_ylabel('RMSE', fontsize=ylabel_size)
    ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., fontsize=legend_fontsize)
    if model == 'AVHRR':
        plt.title('{} Passes vs. Buoy SST'.format(model), fontsize=ttl_size)
    else:
        plt.title('{} vs. Buoy SST'.format(model), fontsize=ttl_size)
    pf.format_date_axis_month(ax, fig)
    plt.ylim([0, 2.5])
    plt.yticks(fontsize=tick_size)
    plt.xticks(fontsize=tick_size)
    sname = '{}_buoy_monthly_rmse_plot_lines'.format(model)
    pf.save_fig(sDir, sname)

    # plot RMSEs with shaded regions for min and max RMSE
    monthly_data = {}
    months = np.unique(sdf['year-month']).tolist()
    for month in months:
        sdf_month = sdf[(sdf['year-month'] == month) & (sdf['n'] > sample_size)]
        if len(sdf_month) > 0:
            monthly_data[month] = dict(rmse_min=np.nanmin(sdf_month['RMSE']), rmse_max=np.nanmax(sdf_month['RMSE']))

    mdf = pd.DataFrame.from_dict(monthly_data, orient='index')
    fig, ax = plt.subplots()
    ax.plot(x, monthly_rmse, '.', markersize=6, color='black', linestyle='-', label='Overall')
    ax.fill_between(np.array(x), mdf['rmse_min'], mdf['rmse_max'], color='lightgray', label='Buoy Range')

    ax.set_ylabel('RMSE', fontsize=ylabel_size)
    ax.legend(loc='best', fontsize=legend_fontsize)
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
    bias = statsdf['bias (mean_diff)'][:-1]
    q1 = statsdf['q1_diff'][:-1]
    q3 = statsdf['q3_diff'][:-1]
    fig, ax = plt.subplots()
    ax.plot(x, bias, '.', markersize=6, color='black', linestyle='-', label='Bias')
    ax.fill_between(np.array(x), q1, q3, color='lightgray', label='Q1 to Q3')
    ax.legend(loc='best', fontsize=legend_fontsize)
    ax.axhline(linestyle='--', lw=1)

    ax.set_ylabel('Bias', fontsize=ylabel_size)
    if model == 'AVHRR':
        #ttl = '{} individual passes minus buoy SST:\nMedian Monthly Difference with Quartiles'.format(model)
        ttl = '{} Passes Minus Buoy SST'.format(model)
    else:
        #ttl = '{} minus buoy SST (from model time period):\nMedian Monthly Difference with Quartiles'.format(model)
        ttl = '{} Minus Buoy SST'.format(model)
    plt.title(ttl, fontsize=ttl_size)
    pf.format_date_axis_month(ax, fig)
    plt.ylim([-1, 1])
    plt.yticks(fontsize=tick_size)
    plt.xticks(fontsize=tick_size)
    sname = '{}_buoy_monthly_bias'.format(model)
    pf.save_fig(sDir, sname)


if __name__ == '__main__':
    # sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/20190503/NREL/AVHRR_individual_passes'
    # sdf = pd.read_csv(os.path.join(sDir, 'AVHRR_buoy_comparison.csv'))
    # statsdf = pd.read_csv(os.path.join(sDir, 'AVHRR_buoy_comparison_overallstats.csv'))
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/20190708/2015-2016/seasons/NYBbuoys/sport_rtg_comparison'
    sdf = pd.read_csv(os.path.join(sDir, 'rtg_buoy_comparison.csv'))
    statsdf = pd.read_csv(os.path.join(sDir, 'rtg_buoy_overallstats.csv'))
    model = 'RTG'  # 'AVHRR' 'SPoRT' 'RTG' 'ColdPix'
    main(sdf, statsdf, sDir, model)
