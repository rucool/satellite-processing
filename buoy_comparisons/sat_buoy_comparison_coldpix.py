#!/usr/bin/env python
"""
Created by Lori Garzio on 4/29/2019
@brief compare buoy data with coldest pixel composite satellite SST data, by month
@usage
sDir: location to save plots
avgrad: radius around the buoy from which to grab satellite data. options: x (average all data within radius x km of
the buoy), 'closest' (grabs the closest data point), 'closestwithinx' (get the closest non-nan measurement as long as
it is within x km of the buoy
start: start time. options: date, int (if int, looks at t1 back t0 days)
end: end time. options: date, int (if int, looks at t0 forward t1 days), 'today', 'yesterday'
"""


import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
import glob
import functions.common as cf
import functions.plotting as pf


def plot_satdata(axis, x, y, rmse, n):
    axis.plot(x, y, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=4,
              label='ColdPix (RMSE={}, n={})'.format(rmse, n))
    return axis


def plot_buoy_full(axis, x, y, buoy):
    axis.plot(x, y, '.', markerfacecolor='grey', markeredgecolor='grey', markersize=1, label='Buoy {}'.format(buoy))
    return axis


def plot_buoy_daily(axis, x, y, buoy):
    axis.plot(x, y, 'o', markerfacecolor='black', markeredgecolor='black',
              markersize=4, color='black', lw=.75, label='Daily Buoy {} Median'.format(buoy))
    return axis


def main(start, end, buoys, avgrad, sDir):
    cp_dir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/daily_avhrr/composites/'
    #cp_dir = '/home/coolgroup/bpu/wrf/data/daily_avhrr/composites/'  # boardwalk
    # daylight hours limits for each month
    # H0_lst = [14, 14, 13, 13, 12, 12, 12, 12, 13, 13, 14, 14]
    # H1_lst = [20, 20, 20, 22, 22, 23, 23, 23, 21, 20, 20, 20]

    sheaders = ['buoy', 'year-month', 'mean_buoy', 'sd_buoy', 'mean_satellite', 'sd_satellite', 'RMSE', 'n',
                'mean_diff', 'sd_diff', 'q1_diff', 'median_diff', 'q3_diff', 'mean_abs_diff', 'sd_abs_diff',
                'q1_abs_diff', 'median_abs_diff', 'q3_abs_diff', 'diff (sat-buoy)']
    summary = []
    # for bulk stats
    all_data = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
    monthly_data = {}
    for buoy in buoys:
        print(buoy)

        # start_dates = [start]  # for debugging
        # end_dates = [end]  # for debugging

        dt_start = datetime.strptime(start, '%m-%d-%Y')
        dt_end = datetime.strptime(end, '%m-%d-%Y')
        start_dates = [dt_start.strftime('%m-%d-%Y')]
        end_dates = []
        ts1 = dt_start
        while ts1 <= dt_end:
            ts2 = ts1 + timedelta(days=1)
            if ts2.month != ts1.month:
                start_dates.append(ts2.strftime('%m-%d-%Y'))
                end_dates.append(ts1.strftime('%m-%d-%Y'))
            ts1 = ts2

        end_dates.append(dt_end.strftime('%m-%d-%Y'))

        for t0, t1 in zip(start_dates, end_dates):
            if not isinstance(t0, int):  # if t0 is not integer, define date
                t0 = cf.format_dates(t0)

            if not isinstance(t1, int):  # if t1 is not integer, define date
                t1 = cf.format_dates(t1)

            if isinstance(t0, int):  # if t0 is integer, redefine as t1-[t0 days]
                t0 = t1-timedelta(days=t0)

            if isinstance(t1, int):  # if t1 is integer, redefine as t0+[t1 days]
                t1 = t0+timedelta(days=t1)

            # define array of times
            times = pd.to_datetime(np.arange(t0, t1+timedelta(days=1), timedelta(days=1)))
            month = t0.strftime('%Y%m')

            all_years = np.unique(times.year)
            #all_years = np.append(all_years, 9999)  # 9999 buoy year is for 'real-time' data (past 45 days)

            # get buoy SST data
            buoy_dict = cf.get_buoy_data(buoy, all_years, t0, t1)

            buoy_full = pd.DataFrame(data={'time': buoy_dict['t'], 'buoy_sst': buoy_dict['sst']})
            buoy_full.drop_duplicates(inplace=True)
            buoy_full = buoy_full.dropna()
            buoy_daily = buoy_full.resample('d', on='time').median().dropna(how='all').reset_index()  # resample daily

            if len(buoy_daily) > 1:
                buoylon = buoy_dict['lon']
                buoylat = buoy_dict['lat']

                # get SST data "at" buoy
                cp_data = {'t': np.array([], dtype='datetime64[ns]'), 'sst': np.array([])}
                for tm in times:
                    dd = datetime.strftime(tm, '%Y%m%d')
                    cp_file = glob.glob('{}{}/avhrr_coldest-pixel_{}.nc'.format(cp_dir, str(tm.year), dd))
                    if len(cp_file) == 1:
                        cp_data['t'] = np.append(cp_data['t'], np.datetime64(tm))
                        svalue = cf.append_satellite_sst_data(cp_file[0], buoylat, buoylon, avgrad, 'daily_avhrr', 'sst')
                        cp_data['sst'] = np.append(cp_data['sst'], svalue)

                cp_df = pd.DataFrame(data={'time': cp_data['t'], 'sat_sst': cp_data['sst']})
                cp_df = cp_df.dropna()

                if len(cp_df) > 0:
                    # merge the buoy and satellite dataframes only where there are data for both
                    df = pd.merge(buoy_daily, cp_df, on='time')
                    df.sort_values('time', inplace=True)
                    df = df.reset_index(drop=True)

                    if len(df) > 0:
                        buoy_data = np.array(df['buoy_sst'])
                        sat_data = np.array(df['sat_sst'])
                        [mbuoy, msat, sdbuoy, sdsat, diff, rmse, n] = cf.statistics(buoy_data, sat_data)

                        # add stats to bulk summary
                        all_data['bdata'] = np.append(all_data['bdata'], buoy_data)
                        all_data['satdata'] = np.append(all_data['satdata'], sat_data)
                        if buoy not in all_data['buoys']:
                            all_data['buoys'].append(buoy)

                        try:
                            monthly_data[month]
                        except KeyError:
                            monthly_data[month] = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
                        monthly_data[month]['bdata'] = np.append(monthly_data[month]['bdata'], buoy_data)
                        monthly_data[month]['satdata'] = np.append(monthly_data[month]['satdata'], sat_data)

                        if buoy not in monthly_data[month]['buoys']:
                            monthly_data[month]['buoys'].append(buoy)

                        # add monthly stats to summary
                        diffx = [round(x, 2) for x in diff]
                        summary.append(
                            [buoy, month, mbuoy, sdbuoy, msat, sdsat, rmse, n, np.nanmean(diff), np.std(diff),
                             np.percentile(diff, 25), np.percentile(diff, 50), np.percentile(diff, 75),
                             np.nanmean(abs(diff)), np.std(abs(diff)), np.percentile(abs(diff), 25),
                             np.percentile(abs(diff), 50), np.percentile(abs(diff), 75), diffx])

                        save_dir = os.path.join(sDir, 'coldestpix', buoy)
                        cf.create_dir(save_dir)
                        sname = '{}_sst_comparison_{}_coldpix'.format(buoy, t1.strftime('%Y%m'))
                        fig, ax = plt.subplots()
                        plt.grid()
                        ax = plot_buoy_full(ax, buoy_full['time'], buoy_full['buoy_sst'], buoy)
                        ax = plot_buoy_daily(ax, df['time'], df['buoy_sst'], buoy)
                        ax = plot_satdata(ax, df['time'], df['sat_sst'], rmse, n)
                        ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
                        pf.format_date_axis(ax, fig)
                        pf.y_axis_disable_offset(ax)
                        ax.legend(loc='best', fontsize=5.5)
                        pf.save_fig(save_dir, sname)

    sdf = pd.DataFrame(summary, columns=sheaders)
    sdf.to_csv('{}/{}/coldpix_buoy_comparison.csv'.format(sDir, 'coldestpix'), index=False)

    stats = []
    [__, __, __, __, diff, rmse, n] = cf.statistics(all_data['bdata'], all_data['satdata'])
    nan_ind = ~np.isnan(diff)
    diff = diff[nan_ind]
    stats.append(['overall', np.nanmean(diff), np.std(diff), np.min(diff), np.percentile(diff, 25),
                  np.percentile(diff, 50), np.percentile(diff, 75), np.max(diff),
                  np.nanmean(abs(diff)), np.std(abs(diff)), np.percentile(abs(diff), 25),
                  np.percentile(abs(diff), 50), np.percentile(abs(diff), 75), rmse, n, all_data['buoys']])

    for key in list(monthly_data.keys()):
        [__, __, __, __, diff, rmse, n] = cf.statistics(monthly_data[key]['bdata'], monthly_data[key]['satdata'])
        nan_ind = ~np.isnan(diff)
        diff = diff[nan_ind]
        stats.append([key, np.nanmean(diff), np.std(diff), np.min(diff), np.percentile(diff, 25),
                      np.percentile(diff, 50), np.percentile(diff, 75), np.max(diff),
                      np.nanmean(abs(diff)), np.std(abs(diff)), np.percentile(abs(diff), 25),
                      np.percentile(abs(diff), 50), np.percentile(abs(diff), 75), rmse, n, monthly_data[key]['buoys']])

    stats_headers = ['year-month', 'mean_diff', 'sd_diff', 'min_diff', 'q1_diff', 'median_diff', 'q3_diff', 'max_diff',
                     'mean_abs_diff',
                     'sd_abs_diff', 'q1_abs_diff', 'median_abs_diff', 'q3_abs_diff', 'RMSE', 'n', 'buoys']
    statsdf = pd.DataFrame(stats, columns=stats_headers)
    statsdf.sort_values('year-month', inplace=True)
    statsdf.to_csv('{}/{}/coldpix_buoy_comparison_overallstats.csv'.format(sDir, 'coldestpix'), index=False)


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    start = '6-1-2015'
    end = '5-31-2016'
    buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
             '44017', '44018', '44020', '44025', '44027', '44065']
    #buoys = ['44009', '44017', '44065']  # buoys in upwelling zone
    avgrad = 'closestwithin5'
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
    #sDir = '/home/lgarzio/rucool/satellite/sst_buoy_comp'  # boardwalk
    main(start, end, buoys, avgrad, sDir)
