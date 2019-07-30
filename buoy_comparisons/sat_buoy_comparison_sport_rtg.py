#!/usr/bin/env python
"""
Created on 7/8/2019
@author Lori Garzio
@brief monthly comparison of sport and RTG data with buoy data
@usage
"""


import matplotlib.pyplot as plt
import glob
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
import functions.common as cf
import functions.plotting as pf


def combine_datasets(sat_data, buoy_full, all_data, buoy, monthly_data, month, summary, samplesize):
    sat_df = pd.DataFrame(data={'time': sat_data['t'], 'sat_sst': sat_data['sst']})
    sat_df = sat_df.dropna()

    if len(sat_df) > 0:
        # merge the buoy and satellite dataframes
        df = pd.merge(buoy_full, sat_df, on='time', how='outer')
        #df = df.loc[:, ~df.columns.duplicated()]  # drop duplicated columns
        df.dropna(axis=0, subset=['buoy_sst', 'sat_sst', 'time'], inplace=True)
        df.drop_duplicates(inplace=True)  # drop duplicated rows

        if len(df) > 0:
            bdata = np.array(df['buoy_sst'])
            sdata = np.array(df['sat_sst'])
            # add stats to summaries only if it meets the sample size threshold
            if len(sdata) > samplesize:
                [mbuoy, msat, sdbuoy, sdsat, diff, rmse, n] = cf.statistics(bdata, sdata)

                # add stats to bulk summary
                all_data['bdata'] = np.append(all_data['bdata'], bdata)
                all_data['satdata'] = np.append(all_data['satdata'], sdata)
                if buoy not in all_data['buoys']:
                    all_data['buoys'].append(buoy)

                try:
                    monthly_data[month]
                except KeyError:
                    monthly_data[month] = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
                monthly_data[month]['bdata'] = np.append(monthly_data[month]['bdata'], bdata)
                monthly_data[month]['satdata'] = np.append(monthly_data[month]['satdata'], sdata)

                if buoy not in monthly_data[month]['buoys']:
                    monthly_data[month]['buoys'].append(buoy)

                # add monthly stats to summary
                diffx = [round(x, 2) for x in diff]
                summary.append([buoy, month, mbuoy, sdbuoy, msat, sdsat, rmse, n,
                                np.nanmean(diff), np.std(diff), np.percentile(diff, 25), np.percentile(diff, 50),
                                np.percentile(diff, 75), diffx])

            else:
                rmse = None
                n = len(df)
        else:
            df = []
            rmse = None
            n = None
    else:
        df = []
        rmse = None
        n = None

    return df, rmse, n


def create_summary_output(summary, mod, all_data, monthly_data):
    headers = ['buoy', 'year-month', 'mean_buoy', 'sd_buoy', 'mean_sat', 'sd_sat', 'RMSE', 'n', 'bias (mean_diff)',
               'sd_diff', 'q1_diff', 'median_diff', 'q3_diff', 'diff (sat-buoy)']
    sdf = pd.DataFrame(summary, columns=headers)
    sdf.to_csv('{}/{}/{}_buoy_comparison.csv'.format(sDir, 'sport_rtg_comparison', mod),
               index=False)

    stats = []
    [__, __, __, __, diff, rmse, n] = cf.statistics(all_data['bdata'], all_data['satdata'])
    nan_ind = ~np.isnan(diff)
    diff = diff[nan_ind]
    stats.append(['overall', np.nanmean(diff), np.std(diff), np.min(diff), np.percentile(diff, 25),
                  np.percentile(diff, 50), np.percentile(diff, 75), np.max(diff), rmse, n, all_data['buoys']])

    for key in list(monthly_data.keys()):
        [__, __, __, __, diff, rmse, n] = cf.statistics(monthly_data[key]['bdata'], monthly_data[key]['satdata'])
        nan_ind = ~np.isnan(diff)
        diff = diff[nan_ind]
        stats.append([key, np.nanmean(diff), np.std(diff), np.min(diff), np.percentile(diff, 25),
                      np.percentile(diff, 50), np.percentile(diff, 75), np.max(diff), rmse, n,
                      monthly_data[key]['buoys']])

    stats_headers = ['year-month', 'bias (mean_diff)', 'sd_diff', 'min_diff', 'q1_diff', 'median_diff', 'q3_diff',
                     'max_diff', 'RMSE', 'n', 'buoys']
    statsdf = pd.DataFrame(stats, columns=stats_headers)
    statsdf.sort_values('year-month', inplace=True)
    statsdf.to_csv('{}/{}/{}_buoy_overallstats.csv'.format(sDir, 'sport_rtg_comparison', mod),
                   index=False)


def plot_avhrr(axis, x, y, rmse, n):
    axis.plot(x, y, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=3.5,
              lw=.75, label='Daily CP (RMSE={}, n={}'.format(rmse, n))
    return axis


def plot_buoy_full(axis, x, y, buoy):
    axis.plot(x, y, '.', markerfacecolor='grey', markeredgecolor='grey', markersize=1, label='Buoy {}'.format(buoy))
    return axis


def plot_buoy_daily(axis, x, y):
    axis.plot(x, y, 'o', markerfacecolor='black', markeredgecolor='black',
              markersize=3.5, color='black', lw=.75, label='Daily Buoy Mean')
    return axis


def plot_rtg(axis, x, y, rmse, n):
    axis.plot(x, y, 'o', markerfacecolor='green', markeredgecolor='green', markersize=3.5,
              label='RTG (RMSE={}, n={})'.format(rmse, n))
    return axis


def plot_sport(axis, x, y, rmse, n):
    axis.plot(x, y, '^', markerfacecolor='red', markeredgecolor='red', markersize=3.5,
              label='SPoRT (RMSE={}, n={})'.format(rmse, n))
    return axis


def main(start, end, buoys, avgrad, sDir, group):
    #bpudatadir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/'
    bpudatadir = '/home/coolgroup/bpu/wrf/data/'  # boardwalk
    models = ['sport', 'rtg', 'avhrr']

    summary_sport = []
    summary_rtg = []
    summary_avhrr = []
    # for bulk stats
    all_data_sport = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
    all_data_rtg = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
    all_data_avhrr = dict(bdata=np.array([]), satdata=np.array([]), buoys=[])
    monthly_data_sport = {}
    monthly_data_rtg = {}
    monthly_data_avhrr = {}
    for buoy in buoys:
        print('\nBuoy {}'.format(buoy))
        # start_dates = [start]
        # end_dates = [end]
        # sample_size = 4

        if group == 'monthly':
            sample_size = 4
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
        elif group == 'season':
            sample_size = 14
            start_dates = ['12-1-2015', '3-1-2016', '6-1-2016', '9-1-2016']
            end_dates = ['2-29-2016', '5-31-2016', '8-31-2016', '11-30-2016']

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
            print('Year-month: {}'.format(month))

            all_years = np.unique(times.year)
            #all_years = np.append(all_years, 9999)  # 9999 buoy year is for 'real-time' data (past 45 days)

            # get buoy SST data
            buoy_dict = cf.get_buoy_data(buoy, all_years, t0, t1)

            buoy_full = pd.DataFrame(data={'time': buoy_dict['t'], 'buoy_sst': buoy_dict['sst']})
            buoy_full.drop_duplicates(inplace=True)
            buoy_full = buoy_full.dropna()
            buoy_daily = buoy_full.resample('d', on='time').mean().dropna(how='all').reset_index()  # resample daily

            # monthly analysis: must be at least 5 days of buoy data
            # seasonal analysis: must be at least 15 days of buoy data
            if len(buoy_daily) > sample_size:
                buoylon = buoy_dict['lon']
                buoylat = buoy_dict['lat']

                sat_data_sport = {'t': np.array([], dtype='datetime64[ns]'), 'sst': np.array([])}
                sat_data_rtg = {'t': np.array([], dtype='datetime64[ns]'), 'sst': np.array([])}
                sat_data_avhrr = {'t': np.array([], dtype='datetime64[ns]'), 'sst': np.array([])}
                for tm in times:
                    print(tm)
                    dd = datetime.strftime(tm, '%Y%m%d')
                    fmdt = np.datetime64(datetime.strptime(dd, '%Y%m%d'))

                    for model in models:
                        if model == 'sport':
                            # get SPoRT data
                            sp_file = glob.glob(bpudatadir + 'sport_nc/' + dd + '*.nc')
                            if len(sp_file) == 1:
                                try:
                                    svalue = cf.append_satellite_sst_data(sp_file[0], buoylat, buoylon, avgrad, 'sport',
                                                                          'TMP_P0_L1_GLL0')
                                    sat_data_sport['sst'] = np.append(sat_data_sport['sst'], svalue)
                                    sat_data_sport['t'] = np.append(sat_data_sport['t'], fmdt)
                                except:
                                    print('Issue reading from {}'.format(sp_file[0]))

                            else:
                                print('{} files found for SPoRT at time {}'.format(str(len(sp_file)), tm.strftime('%Y-%m-%d')))

                        if model == 'rtg':
                            # get RTG data
                            rtg_files = []
                            rtg_dir = '{}{}/{}/'.format(bpudatadir, 'rtg_nc', str(tm.year))
                            for file in os.listdir(rtg_dir):
                                if file.startswith('rtg_sst_grb') and file.endswith('{}.nc'.format(dd)):
                                    rtg_files.append(os.path.join(rtg_dir, file))
                            if len(rtg_files) == 1:
                                # take the closest grid cell to the buoy (RTG has full-coverage)
                                svalue = cf.append_satellite_sst_data(rtg_files[0], buoylat, buoylon, 'closest', 'rtg',
                                                                      'TMP_173_SFC')
                                sat_data_rtg['sst'] = np.append(sat_data_rtg['sst'], svalue)
                                sat_data_rtg['t'] = np.append(sat_data_rtg['t'], fmdt)

                            else:
                                print('{} files found for RTG at time {}'.format(str(len(rtg_files)), tm.strftime('%Y-%m-%d')))

                        if model == 'avhrr':
                            # daily AVHRR daily coldest pixel composite
                            satfile = '{}daily_avhrr/composites/{}/avhrr_coldest-pixel_{}.nc'.format(bpudatadir,
                                                                                                     tm.strftime('%Y'),
                                                                                                     tm.strftime(
                                                                                                         '%Y%m%d'))
                            try:
                                cvalue = cf.append_satellite_sst_data(satfile, buoylat, buoylon, avgrad, 'daily_avhrr',
                                                                      'sst')
                                sat_data_avhrr['sst'] = np.append(sat_data_avhrr['sst'], cvalue)
                                sat_data_avhrr['t'] = np.append(sat_data_avhrr['t'], fmdt)
                            except:
                                print('Issue reading from {}'.format(satfile))

                # merge SPoRT with buoy data
                [df_sport, rmse_sport, n_sport] = combine_datasets(sat_data_sport, buoy_daily, all_data_sport, buoy,
                                                                   monthly_data_sport, month, summary_sport, sample_size)

                # merge RTG with buoy data
                [df_rtg, rmse_rtg, n_rtg] = combine_datasets(sat_data_rtg, buoy_daily, all_data_rtg, buoy,
                                                             monthly_data_rtg, month, summary_rtg, sample_size)

                # merge daily coldest pixel AVHRR with buoy data
                [df_avhrr, rmse_avhrr, n_avhrr] = combine_datasets(sat_data_avhrr, buoy_daily, all_data_avhrr, buoy,
                                                             monthly_data_avhrr, month, summary_avhrr, sample_size)

                if len(df_sport) > 0 and len(df_rtg) > 0:
                    buoy_plot = pd.merge(df_sport, df_rtg, on=['time', 'buoy_sst'], how='outer')
                    buoy_plot.drop_duplicates(subset=['time', 'buoy_sst'], inplace=True, keep='last')
                elif len(df_sport) > 0:
                    buoy_plot = df_sport
                else:
                    buoy_plot = df_rtg

                save_dir = os.path.join(sDir, 'sport_rtg_comparison', buoy)
                cf.create_dir(save_dir)
                sname = '{}_sst_comparison_sport_rtg_{}'.format(buoy, month)
                fig, ax = plt.subplots()
                plt.grid()
                ax = plot_buoy_full(ax, buoy_full['time'], buoy_full['buoy_sst'], buoy)
                ax = plot_buoy_daily(ax, buoy_plot['time'] + timedelta(hours=12), buoy_plot['buoy_sst'])
                if len(df_sport) > 0:
                    ax = plot_sport(ax, df_sport['time'] + timedelta(hours=12), df_sport['sat_sst'], rmse_sport, n_sport)
                if len(df_rtg) > 0:
                    ax = plot_rtg(ax, df_rtg['time'] + timedelta(hours=12), df_rtg['sat_sst'], rmse_rtg, n_rtg)
                if len(df_avhrr) > 0:
                    ax = plot_avhrr(ax, df_avhrr['time'] + timedelta(hours=12), df_avhrr['sat_sst'], rmse_avhrr, n_avhrr)
                ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=8.5)
                plt.title('Buoy {}'.format(buoy), fontsize=9)
                pf.format_date_axis(ax, fig)
                pf.y_axis_disable_offset(ax)
                ax.legend(loc='best', fontsize=5.5)
                pf.save_fig(save_dir, sname)

    create_summary_output(summary_sport, 'sport', all_data_sport, monthly_data_sport)
    create_summary_output(summary_rtg, 'rtg', all_data_rtg, monthly_data_rtg)
    create_summary_output(summary_avhrr, 'avhrr', all_data_avhrr, monthly_data_avhrr)


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    start = '12-1-2015'
    end = '11-30-2016'
    # buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013',
    #          '44014', '44017', '44018', '44020', '44025', '44027', '44065']
    buoys = ['44008', '44009', '44014', '44017', '44020', '44025', '44065']  # Mid-Atlantic buoys
    # buoys = ['44009', '44017', '44025', '44065']  # New York Bight buoys
    # buoys = ['44009', '44017', '44065']  # buoys in upwelling zone
    avgrad = 'closestwithin5'
    #sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/20190729'
    sDir = '/home/lgarzio/rucool/satellite/sst_buoy_comp/20190729/monthly'  # boardwalk
    grouping = 'monthly'  # options: 'monthly' or 'season' if season - need to define in lines 156-157
    main(start, end, buoys, avgrad, sDir, grouping)
