#!/usr/bin/env python
"""
Created on 7/29/2019
@author Lori Garzio
@brief plot buoy sst daily ranges
@usage
"""


import matplotlib.pyplot as plt
import matplotlib.cm as cm
import datetime as dt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import os
import functions.common as cf
import functions.plotting as pf

register_matplotlib_converters()


def main(t0, t1, buoys, sDir, group):
    buoy_df = pd.DataFrame()
    summary = []
    headers = ['year-month', 'mean_range', 'sd_range', 'percentile5', 'percentile95', 'n', 'buoys']
    for buoy in buoys:
        print('\nBuoy {}'.format(buoy))

        # define array of times
        times = pd.to_datetime(np.arange(t0, t1+dt.timedelta(days=1), dt.timedelta(days=1)))

        all_years = np.unique(times.year)
        #all_years = np.append(all_years, 9999)  # 9999 buoy year is for 'real-time' data (past 45 days)

        # get buoy SST data
        buoy_dict = cf.get_buoy_data(buoy, all_years, t0, t1)

        buoy_full = pd.DataFrame(data={'time': buoy_dict['t'], 'buoy_sst': buoy_dict['sst']})
        buoy_full.drop_duplicates(inplace=True)
        buoy_full = buoy_full.dropna()
        #buoy_daily = buoy_full.resample('d', on='time').mean().dropna(how='all').reset_index()  # resample daily
        buoy_daily = buoy_full.resample('d', on='time').apply({'buoy_sst': [np.nanmean, np.nanmin, np.nanmax, np.nanstd]})
        buoy_daily.columns = buoy_daily.columns.droplevel(0)  # drop extra column headers
        buoy_daily = buoy_daily.reset_index()
        buoy_daily['buoy'] = np.repeat(buoy, len(buoy_daily))  # add buoy as a column
        if buoy == '44020':  # get rid of outliers for buoy 44020 in Nov 2016
            buoy_daily = buoy_daily.loc[(buoy_daily['time'] < '11-16-2016') | (buoy_daily['time'] > '11-30-2016')]
        buoy_df = buoy_df.append(buoy_daily)

    buoy_df['range'] = buoy_df['nanmax'] - buoy_df['nanmin']  # add daily buoy range to dataframe
    fig1, ax1 = plt.subplots()  # overall plot
    colors = cm.rainbow(np.linspace(0, 1, len(buoys)))
    for i in range(len(buoys)):
        bdf = buoy_df.loc[buoy_df['buoy'] == buoys[i]]
        ax1.plot(bdf['time'], bdf['range'], '-o', c=colors[i], markersize=1, linewidth=.75, label=buoys[i])
    ax1.grid()
    pf.format_date_axis(ax1, fig1)
    ax1.legend(loc='best', fontsize=7)
    ax1.set_ylabel('Daily SST Range (degrees C)', fontsize=9)
    plt.title('Daily SST Range: Mid-Atlantic Buoys', fontsize=9)
    save_file = os.path.join(sDir, 'buoy_range_overall')
    fig1.savefig(str(save_file), dpi=150)

    if group == 'monthly':
        dt_start = t0
        dt_end = t1
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
    elif group == 'season':
        start_dates = ['12-1-2015', '3-1-2016', '6-1-2016', '9-1-2016']
        end_dates = ['2-29-2016', '5-31-2016', '8-31-2016', '11-30-2016']

    for sd, ed in zip(start_dates, end_dates):
        fig2, ax2 = plt.subplots()  # monthly or seasonal plot
        month = sd.split('-')[-1] + sd.split('-')[0]
        print('Year-month: {}'.format(month))
        bdf_month = buoy_df.loc[(buoy_df['time'] >= sd) & (buoy_df['time'] <= ed)]
        if len(bdf_month) > 0:
            summary.append([month, round(np.nanmean(bdf_month['range']), 2), round(np.nanstd(bdf_month['range']), 2),
                            round(np.percentile(bdf_month['range'], 5), 2), round(np.percentile(bdf_month['range'], 95), 2),
                            len(bdf_month), np.unique(bdf_month['buoy']).tolist()])
            for i in range(len(buoys)):
                bdfm = bdf_month.loc[bdf_month['buoy'] == buoys[i]]
                ax2.plot(bdfm['time'], bdfm['range'], '-o', c=colors[i], markersize=1, linewidth=.75,
                         label=buoys[i])
            ax2.grid()
            # get y-limits of the overall plot and set all the monthly/seasonal plots to the same limits
            ax2.set_ylim(ax1.get_ylim())
            pf.format_date_axis(ax2, fig2)
            ax2.legend(loc='best', fontsize=7)
            ax2.set_ylabel('Daily SST Range (degrees C)', fontsize=9)
            plt.title('Daily SST Range: Mid-Atlantic Buoys', fontsize=9)
            save_file = os.path.join(sDir, 'buoy_range_{}'.format(month))
            fig2.savefig(str(save_file), dpi=150)

    sdf = pd.DataFrame(summary, columns=headers)
    sdf.to_csv('{}/buoy_range_summary.csv'.format(sDir), index=False)

    fig, ax = plt.subplots()
    ym_list = sdf['year-month'].tolist()
    x = [dt.datetime.strptime(ym, '%Y%m') for ym in ym_list]
    ax.plot(x, sdf['mean_range'], '-o', markersize=2.5, linewidth=1)
    ax.fill_between(x, sdf['percentile5'], sdf['percentile95'], color='lightgray', label='95th percentile')
    ax.set_ylabel('Average SST Daily Range (degrees C)', fontsize=9)
    plt.title('Monthly Average of Daily SST Range (95th percentile shaded)\nMid-Atlantic Buoys', fontsize=9)
    pf.format_date_axis_month(ax, fig)
    save_file = os.path.join(sDir, 'buoy_range_summary')
    fig.savefig(str(save_file), dpi=150)


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    start = dt.datetime(2015, 12, 1, 0, 0)
    end = dt.datetime(2016, 11, 30, 0, 0)
    # buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013',
    #          '44014', '44017', '44018', '44020', '44025', '44027', '44065']
    buoys = ['44008', '44009', '44014', '44017', '44025', '44065']  # Mid-Atlantic buoys
    # buoys = ['44009', '44017', '44025', '44065']  # New York Bight buoys
    # buoys = ['44009', '44017', '44065']  # buoys in upwelling zone
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/20190729/buoy_sst_range'
    #sDir = '/home/lgarzio/rucool/satellite/sst_buoy_comp/20190708/NYBbuoys'  # boardwalk
    grouping = 'monthly'  # options: 'monthly' or 'season' if season - need to define in lines 156-157
    main(start, end, buoys, sDir, grouping)
