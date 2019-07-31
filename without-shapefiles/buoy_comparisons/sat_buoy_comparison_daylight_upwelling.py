#!/usr/bin/env python
"""
Created by Lori Garzio on 4/29/2019
@brief comparisons of buoy data with: 1) coldest pixel composite satellite SST data, 2) RTG data, and 3) SPoRT
(buoy average daylight hours only) for upwelling events only
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


def plot_buoy_full(axis, x, y, buoy):
    axis.plot(x, y, '.', markerfacecolor='grey', markeredgecolor='grey', markersize=1, label='Buoy {} (daylight only)'.format(buoy))
    return axis


def plot_buoy_daily(axis, x, y, buoy):
    axis.plot(x, y, 'o', markerfacecolor='black', markeredgecolor='black',
              markersize=4, color='black', lw=.75, label='Daily Daylight Buoy Mean'.format(buoy))
    return axis


def plot_rtg(axis, x, y, rmse, n):
    axis.plot(x, y, 'o', markerfacecolor='green', markeredgecolor='green', markersize=4,
              label='RTG (RMSE={}, n={})'.format(rmse, n))
    return axis


def plot_sport(axis, x, y, rmse, n):
    axis.plot(x, y, '^', markerfacecolor='red', markeredgecolor='red', markersize=4,
              label='SPoRT (RMSE={}, n={})'.format(rmse, n))
    return axis


def plot_satdata(axis, x, y, rmse, n):
    axis.plot(x, y, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=4,
              label='ColdPix (RMSE={}, n={})'.format(rmse, n))
    return axis


def main(buoys, avgrad, models, sDir):
    bpudatadir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/'
    #dir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/daily_avhrr/composites/'
    #dir = '/home/coolgroup/bpu/wrf/data/daily_avhrr/composites/'  # boardwalk

    # daylight hours limits for each month
    H0_lst = [14, 14, 13, 13, 12, 12, 12, 12, 13, 13, 14, 14]
    H1_lst = [20, 20, 20, 22, 22, 23, 23, 23, 21, 20, 20, 20]

    sheaders = ['buoy', 'year-month', 'mean_buoy', 'sd_buoy', 'mean_satellite', 'sd_satellite', 'RMSE', 'n',
                'mean_diff', 'sd_diff', 'q1_diff', 'median_diff', 'q3_diff', 'mean_abs_diff', 'sd_abs_diff',
                'q1_abs_diff', 'median_abs_diff', 'q3_abs_diff', 'diff (sat-buoy)']

    for model in models:
        print(model)
        if len(buoys) == 3:
            save_dir_all = os.path.join(sDir, '{}_upwelling'.format(model))
        else:
            save_dir_all = os.path.join(sDir, model)
        cf.create_dir(save_dir_all)
        summary = []
        # for bulk stats
        all_data = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
        monthly_data = {}
        for buoy in buoys:
            print(buoy)
            #upwelling events only
            times = [datetime(2016, 7, 4), datetime(2016, 7, 5), datetime(2016, 7, 6), datetime(2016, 7, 8),
                     datetime(2016, 7, 9), datetime(2016, 7, 10), datetime(2016, 7, 11), datetime(2016, 7, 12),
                     datetime(2016, 7, 19), datetime(2016, 7, 20), datetime(2016, 7, 21), datetime(2016, 7, 22),
                     datetime(2016, 7, 23), datetime(2016, 7, 24), datetime(2016, 7, 26), datetime(2016, 7, 27),
                     datetime(2016, 7, 28), datetime(2016, 7, 29), datetime(2016, 7, 30),
                     datetime(2016, 8, 3), datetime(2016, 8, 4), datetime(2016, 8, 5), datetime(2016, 8, 16),
                     datetime(2016, 8, 17), datetime(2016, 8, 18), datetime(2016, 8, 21), datetime(2016, 8, 22),
                     datetime(2016, 8, 23), datetime(2016, 8, 24), datetime(2016, 8, 26), datetime(2016, 8, 27),
                     datetime(2016, 8, 28)]

            #times = [datetime(2016, 7, 4), datetime(2016, 7, 5), datetime(2016, 7, 6), datetime(2016, 7, 8)]

            all_years = np.unique([x.year for x in times])
            #all_years = np.append(all_years, 9999)  # 9999 buoy year is for 'real-time' data (past 45 days)

            # get buoy SST data
            buoy_dict = cf.get_buoy_data(buoy, all_years, times[0], times[-1])

            buoy_full = pd.DataFrame(data={'time': buoy_dict['t'], 'buoy_sst': buoy_dict['sst']})
            buoy_full.drop_duplicates(inplace=True)
            buoy_full = buoy_full.dropna()
            buoy_full['month'] = buoy_full['time'].dt.month
            buoy_full['hour'] = buoy_full['time'].dt.hour
            buoy_full_daylight = pd.DataFrame(columns=['time', 'buoy_sst', 'month', 'hour'])
            for m in np.unique(buoy_full['month']):
                H0 = H0_lst[m - 1]
                H1 = H1_lst[m - 1]
                fdf = buoy_full.loc[(buoy_full['month'] == m) & (buoy_full['hour'] >= H0) & (buoy_full['hour'] <= H1)]
                buoy_full_daylight = buoy_full_daylight.append(fdf, ignore_index=True)
            buoy_daylight_daily = buoy_full_daylight.resample('d', on='time').mean().dropna(how='all').reset_index()  # resample daily

            if len(buoy_full) > 1:
                buoylon = buoy_dict['lon']
                buoylat = buoy_dict['lat']

                # get SST data "at" buoy
                sat_data = {'t': np.array([], dtype='datetime64[ns]'), 'sst': np.array([])}
                for tm in times:
                    fmtm = np.datetime64(datetime.strftime(tm, '%Y-%m-%d'))
                    dd = datetime.strftime(tm, '%Y%m%d')
                    if model == 'coldestpix':
                        sat_file = glob.glob('{}{}{}/avhrr_coldest-pixel_{}.nc'.format(bpudatadir,
                                                                                       'daily_avhrr/composites/',
                                                                                       str(tm.year), dd))
                        if len(sat_file) == 1:
                            sat_data['t'] = np.append(sat_data['t'], fmtm)
                            svalue = cf.append_satellite_sst_data(sat_file[0], buoylat, buoylon, avgrad,
                                                                  'daily_avhrr', 'sst')
                            sat_data['sst'] = np.append(sat_data['sst'], svalue)
                    elif model == 'sport':
                        sp_file = glob.glob(bpudatadir + 'sport_nc/' + dd + '*.nc')
                        if len(sp_file) == 1:
                            try:
                                svalue = cf.append_satellite_sst_data(sp_file[0], buoylat, buoylon, avgrad, 'sport',
                                                                      'TMP_P0_L1_GLL0')
                                sat_data['sst'] = np.append(sat_data['sst'], svalue)
                                sat_data['t'] = np.append(sat_data['t'], fmtm)
                            except:
                                print('Issue reading from {}'.format(sp_file[0]))
                        else:
                            print('{} files found for SPoRT at time {}'.format(str(len(sp_file)),
                                                                               tm.strftime('%Y-%m-%d')))
                    elif model == 'rtg':
                        rtg_files = []
                        rtg_dir = '{}{}/{}/'.format(bpudatadir, 'rtg_nc', str(tm.year))
                        for file in os.listdir(rtg_dir):
                            if file.startswith('rtg_sst_grb') and file.endswith('{}.nc'.format(dd)):
                                rtg_files.append(os.path.join(rtg_dir, file))
                        if len(rtg_files) == 1:
                            svalue = cf.append_satellite_sst_data(rtg_files[0], buoylat, buoylon, 'closest', 'rtg',
                                                                  'TMP_173_SFC')
                            sat_data['sst'] = np.append(sat_data['sst'], svalue)
                            sat_data['t'] = np.append(sat_data['t'], fmtm)
                        else:
                            print('{} files found for RTG at time {}'.format(str(len(rtg_files)),
                                                                             tm.strftime('%Y-%m-%d')))

                sat_df = pd.DataFrame(data={'time': sat_data['t'], 'sat_sst': sat_data['sst']})
                sat_df = sat_df.dropna()

                if len(sat_df) > 0:
                    # merge the buoy and satellite/model dataframes only where there are data for both
                    df = pd.merge(buoy_daylight_daily, sat_df, on='time')
                    df = df.drop_duplicates(subset=['time', 'buoy_sst', 'sat_sst'])

                    if len(df) > 0:
                        # add column for plotting the median and satellite data at hour 12
                        #df['plt_time'] = df['time'] + timedelta(hours=np.float(df['hour'][0]))
                        df['plt_time'] = df['time'] + timedelta(hours=17)
                        buoy_data = np.array(df['buoy_sst'])
                        sat_data = np.array(df['sat_sst'])
                        [mbuoy, msat, sdbuoy, sdsat, diff, rmse, n] = cf.statistics(buoy_data, sat_data)

                        # add monthly stats to summary
                        diffx = [round(x, 2) for x in diff]
                        summary.append(
                            [buoy, 'upwelling_events', mbuoy, sdbuoy, msat, sdsat, rmse, n, np.nanmean(diff), np.std(diff),
                             np.percentile(diff, 25), np.percentile(diff, 50), np.percentile(diff, 75),
                             np.nanmean(abs(diff)), np.std(abs(diff)), np.percentile(abs(diff), 25),
                             np.percentile(abs(diff), 50), np.percentile(abs(diff), 75), diffx])

                        # add stats to bulk summary, only if the monthly sample size is >3
                        if len(df) > 3:
                            all_data['bdata'] = np.append(all_data['bdata'], buoy_data)
                            all_data['satdata'] = np.append(all_data['satdata'], sat_data)
                            if buoy not in all_data['buoys']:
                                all_data['buoys'].append(buoy)

                            # try:
                            #     monthly_data[month]
                            # except KeyError:
                            #     monthly_data[month] = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
                            # monthly_data[month]['bdata'] = np.append(monthly_data[month]['bdata'], buoy_data)
                            # monthly_data[month]['satdata'] = np.append(monthly_data[month]['satdata'], sat_data)
                            #
                            # if buoy not in monthly_data[month]['buoys']:
                            #     monthly_data[month]['buoys'].append(buoy)

                        buoy_save_dir = os.path.join(save_dir_all, buoy)
                        cf.create_dir(buoy_save_dir)
                        sname = '{}_sst_comparison_{}_{}'.format(buoy, 'upwelling_events', model)
                        fig, ax = plt.subplots()
                        plt.grid()
                        ax = plot_buoy_full(ax, buoy_full_daylight['time'], buoy_full_daylight['buoy_sst'], buoy)
                        ax = plot_buoy_daily(ax, df['plt_time'], df['buoy_sst'], buoy)
                        if model == 'coldestpix':
                            ax = plot_satdata(ax, df['plt_time'], df['sat_sst'], rmse, n)
                        elif model == 'rtg':
                            ax = plot_rtg(ax, df['plt_time'], df['sat_sst'], rmse, n)
                        elif model == 'sport':
                            ax = plot_sport(ax, df['plt_time'], df['sat_sst'], rmse, n)
                        ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
                        pf.format_date_axis(ax, fig)
                        pf.y_axis_disable_offset(ax)
                        ax.legend(loc='best', fontsize=5.5)
                        pf.save_fig(buoy_save_dir, sname)

        sdf = pd.DataFrame(summary, columns=sheaders)
        sdf.to_csv('{}/{}_buoy_comparison.csv'.format(save_dir_all, model), index=False)

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
        statsdf.to_csv('{}/{}_buoy_comparison_overallstats.csv'.format(save_dir_all, model), index=False)


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    # start = '6-1-2015'
    # end = '5-31-2016'
    start = '1-1-2018'
    end = '12-31-2018'
    # buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
    #          '44017', '44018', '44020', '44025', '44027', '44065']
    #buoys = ['44008', '44009', '44014', '44017', '44025', '44065']  # Mid-Atlantic buoys
    buoys = ['44009', '44017', '44065']  # buoys in upwelling zone
    #buoys = ['44065']
    avgrad = 'closestwithin5'
    models = ['coldestpix', 'rtg']  # ['coldestpix', 'sport', 'rtg']
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/20190503/upwelling_events/'
    #sDir = '/home/lgarzio/rucool/satellite/sst_buoy_comp'  # boardwalk
    main(buoys, avgrad, models, sDir)
