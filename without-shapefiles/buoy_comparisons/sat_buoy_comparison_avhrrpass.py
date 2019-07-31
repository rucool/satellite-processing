#!/usr/bin/env python
"""
Created by Lori Garzio on 2/12/2019
@brief compare buoy data with individual daylight window passes of AVHRR satellite SST data, by month
@usage
sDir: location to save plots
avgrad: radius around the buoy from which to grab satellite data. options: x (average all data within radius x km of
the buoy), 'closest' (grabs the closest data point), 'closestwithinx' (get the closest non-nan measurement as long as
it is within x km of the buoy
start: start time. options: date, int (if int, looks at t1 back t0 days)
end: end time. options: date, int (if int, looks at t0 forward t1 days), 'today', 'yesterday'
"""


import matplotlib.pyplot as plt
import matplotlib.cm as cm
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
import functions.common as cf
import functions.plotting as pf


def plot_avhrr(axis, x, y, rmse, n):
    axis.plot(x, y, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=4,
              label='AVHRR (RMSE={}, n={})'.format(rmse, n))
    return axis


def plot_buoy_full(axis, x, y, buoy):
    axis.plot(x, y, '.', markerfacecolor='grey', markeredgecolor='grey', markersize=4, label='Buoy {}'.format(buoy))
    return axis


def main(start, end, buoys, avgrad, sDir):
    avhrr_dir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/avhrr_nc/'
    #avhrr_dir = '/home/coolgroup/bpu/wrf/data/avhrr_nc/'  # boardwalk
    # daylight hours limits for each month
    H0_lst = [14, 14, 13, 13, 12, 12, 12, 12, 13, 13, 14, 14]
    H1_lst = [20, 20, 20, 22, 22, 23, 23, 23, 21, 20, 20, 20]

    if len(buoys) == 3:
        save_dir_all = os.path.join(sDir, 'AVHRR_individual_passes_upwelling')
    else:
        save_dir_all = os.path.join(sDir, 'AVHRR_individual_passes')
    cf.create_dir(save_dir_all)

    sheaders = ['buoy', 'year-month', 'mean_buoy', 'sd_buoy', 'mean_avhrr', 'sd_avhrr', 'RMSE', 'n',
                'mean_diff', 'sd_diff', 'q1_diff', 'median_diff', 'q3_diff', 'mean_abs_diff', 'sd_abs_diff',
                'q1_abs_diff', 'median_abs_diff', 'q3_abs_diff', 'diff (sat-buoy)']
    summary = []
    # for bulk stats
    all_data = dict(bdata=np.array([]), avhrrdata=np.array([]), buoys=[])
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

            if len(buoy_full) > 1:
                buoylon = buoy_dict['lon']
                buoylat = buoy_dict['lat']

                # get SST data "at" buoy from each daytime-window AVHRR pass
                avhrr_data = {'t': np.array([], dtype='datetime64[ns]'), 'sst': np.array([])}
                for tm in times:
                    dd = datetime.strftime(tm, '%y%m%d')
                    #print(dd)
                    avhrr_files = []
                    for file in os.listdir(avhrr_dir):
                        if file.startswith(dd) and file.endswith('.CF.nc'):
                            avhrr_files.append(os.path.join(avhrr_dir, file))
                    if len(avhrr_files) > 0:
                        # select pre-defined daylight hour limits for that month
                        H0 = H0_lst[tm.month - 1]
                        H1 = H1_lst[tm.month - 1]
                        for avhrr in avhrr_files:
                            passH = avhrr[-18:-16]  # hour
                            passM = avhrr[-16:-14]  # minute
                            dt = 'T'.join((dd, (passH + passM)))
                            if H0 <= int(passH) < H1:
                                fmdt = np.datetime64(datetime.strptime(dt, '%y%m%dT%H%M'))
                                avhrr_data['t'] = np.append(avhrr_data['t'], fmdt)
                                data = cf.append_satellite_sst_data(avhrr, buoylat, buoylon, avgrad, 'avhrr', 'mcsst')
                                avhrr_data['sst'] = np.append(avhrr_data['sst'], data)

                avhrr_df = pd.DataFrame(data={'time': avhrr_data['t'], 'avhrr_sst': avhrr_data['sst']})
                avhrr_df = avhrr_df.dropna()

                if len(avhrr_df) > 0:
                    # merge the buoy and avhrr dataframes
                    df = pd.merge(buoy_full, avhrr_df, on='time', how='outer')
                    df.sort_values('time', inplace=True)
                    df = df.reset_index(drop=True)

                    # select the buoy data that comes before and after the timestamp of the avhrr data
                    headers = ['time', 'buoy_sst', 'avhrr_sst']
                    final_data = []
                    for i, row in df.iterrows():
                        if not np.isnan(row['avhrr_sst']):
                            # take the satellite time and sst data, along with the buoy_sst at exactly the same
                            # time (if possible)
                            if not np.isnan(row['buoy_sst']):
                                final_data.append([row['time'], row['buoy_sst'], row['avhrr_sst']])
                            else:
                                if i == 0:
                                    # take the buoy data at the next timestamp if you're at the very beginning
                                    final_data.append([row['time'], df.iloc[i + 1]['buoy_sst'], row['avhrr_sst']])
                                elif i == len(df) - 1:
                                    # take the buoy data at the previous timestamp if you're at the very end
                                    final_data.append([row['time'], df.iloc[i - 1]['buoy_sst'], row['avhrr_sst']])
                                else:
                                    # take the average of the buoy data at the two surrounding timestamps if you're in
                                    # the middle of the df
                                    buoy_mean = np.nanmean([df.iloc[i - 1]['buoy_sst'], df.iloc[i + 1]['buoy_sst']])
                                    final_data.append([row['time'], buoy_mean, row['avhrr_sst']])

                    fdf = pd.DataFrame(final_data, columns=headers)
                    fdf.dropna(axis=0, subset=['buoy_sst', 'avhrr_sst'], inplace=True)
                    if len(fdf) > 0:
                        buoy_data = np.array(fdf['buoy_sst'])
                        sat_data = np.array(fdf['avhrr_sst'])
                        [mbuoy, mavhrr, sdbuoy, sdavhrr, diff, rmse, n] = cf.statistics(buoy_data, sat_data)

                        # add monthly stats to summary
                        diffx = [round(x, 2) for x in diff]
                        summary.append(
                            [buoy, month, mbuoy, sdbuoy, mavhrr, sdavhrr, rmse, n, np.nanmean(diff), np.std(diff),
                             np.percentile(diff, 25), np.percentile(diff, 50), np.percentile(diff, 75),
                             np.nanmean(abs(diff)), np.std(abs(diff)), np.percentile(abs(diff), 25),
                             np.percentile(abs(diff), 50), np.percentile(abs(diff), 75), diffx])

                        # add stats to bulk summary, only if the monthly sample size is >3
                        if len(fdf) > 3:
                            all_data['bdata'] = np.append(all_data['bdata'], buoy_data)
                            all_data['avhrrdata'] = np.append(all_data['avhrrdata'], sat_data)
                            if buoy not in all_data['buoys']:
                                all_data['buoys'].append(buoy)

                            try:
                                monthly_data[month]
                            except KeyError:
                                monthly_data[month] = dict(bdata=np.array([]), avhrrdata=np.array([]), buoys=[])
                            monthly_data[month]['bdata'] = np.append(monthly_data[month]['bdata'], buoy_data)
                            monthly_data[month]['avhrrdata'] = np.append(monthly_data[month]['avhrrdata'], sat_data)

                            if buoy not in monthly_data[month]['buoys']:
                                monthly_data[month]['buoys'].append(buoy)

                        save_dir = os.path.join(save_dir_all, buoy)
                        cf.create_dir(save_dir)
                        sname = '{}_sst_comparison_{}_AVHRR'.format(buoy, t1.strftime('%Y%m'))
                        fig, ax = plt.subplots()
                        plt.grid()
                        ax = plot_buoy_full(ax, fdf['time'], fdf['buoy_sst'], buoy)
                        ax = plot_avhrr(ax, fdf['time'], fdf['avhrr_sst'], rmse, n)
                        ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
                        pf.format_date_axis(ax, fig)
                        pf.y_axis_disable_offset(ax)
                        ax.legend(loc='best', fontsize=5.5)
                        pf.save_fig(save_dir, sname)

    sdf = pd.DataFrame(summary, columns=sheaders)
    sdf.to_csv('{}/AVHRR_buoy_comparison.csv'.format(save_dir_all), index=False)

    stats = []
    [__, __, __, __, diff, rmse, n] = cf.statistics(all_data['bdata'], all_data['avhrrdata'])
    nan_ind = ~np.isnan(diff)
    diff = diff[nan_ind]
    stats.append(['overall', np.nanmean(diff), np.std(diff), np.min(diff), np.percentile(diff, 25),
                  np.percentile(diff, 50), np.percentile(diff, 75), np.max(diff),
                  np.nanmean(abs(diff)), np.std(abs(diff)), np.percentile(abs(diff), 25),
                  np.percentile(abs(diff), 50), np.percentile(abs(diff), 75), rmse, n, all_data['buoys']])

    for key in list(monthly_data.keys()):
        [__, __, __, __, diff, rmse, n] = cf.statistics(monthly_data[key]['bdata'], monthly_data[key]['avhrrdata'])
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
    statsdf.to_csv('{}/AVHRR_buoy_comparison_overallstats.csv'.format(save_dir_all), index=False)


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    start = '6-1-2015'
    end = '5-31-2016'
    # start = '1-1-2018'
    # end = '12-31-2018'
    buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
             '44017', '44018', '44020', '44025', '44027', '44065']
    #buoys = ['44008', '44009', '44014', '44017', '44025', '44065']  # Mid-Atlantic buoys
    #buoys = ['44009', '44017', '44065']  # buoys in upwelling zone
    avgrad = 'closestwithin5'
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/20190501/NREL_timeperiod_n3/'
    #sDir = '/home/lgarzio/rucool/satellite/sst_buoy_comp'  # boardwalk
    main(start, end, buoys, avgrad, sDir)
