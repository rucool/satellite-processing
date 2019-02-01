#!/usr/bin/env python
"""
@author Laura Nazarro
@modified by Lori Garzio on 1/16/2019
@brief compare buoy data with satellite SST data from the NREL case study, by month
"""

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import glob
import os
import functions.common as cf
import functions.plotting as pf


def format_dates(dt):
    if dt == 'today':
        dt = datetime.now()
    elif dt == 'yesterday':
        dt = datetime.now()-timedelta(days=1)
    else:
        dt = datetime.strptime(dt, "%m-%d-%Y")
    return dt


def initialize_empty_array(time_array):
    empty_array = np.empty(np.shape(time_array))
    empty_array[:] = np.nan
    return empty_array


def plot_avhrr(axis, x, y, rmse, n):
    axis.plot(x, y, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=4, color='blue', linestyle='-',
              lw=.75, label='AVHRR (RMSE={}, n={})'.format(rmse, n))
    return axis


def plot_buoy_full(axis, fbuoy_df, buoy):
    axis.plot(fbuoy_df['time'], fbuoy_df['sst'], '.', markerfacecolor='grey', markeredgecolor='grey', markersize=1,
              label='Buoy {}'.format(buoy))
    # bf_leg = mlines.Line2D([], [], marker='.', markerfacecolor='grey', markeredgecolor='grey', markersize=2,
    #                        color='none', label='Buoy {}'.format(buoy))
    return axis


def plot_buoy_daily(axis, dbuoy_df):
    axis.plot(dbuoy_df['time_plt'], dbuoy_df['buoy_sst_mean'], 'o', markerfacecolor='black', markeredgecolor='black',
              markersize=4, color='black', linestyle='-', lw=.75, label='Daily Buoy Mean')
    # bd_leg = mlines.Line2D([], [], marker='o', markerfacecolor='black', markeredgecolor='black', markersize=4,
    #                        color='black', label='Daily Buoy Mean')
    #                        #color='black', label=('Daily Buoy Mean' + '\n Mean: {} \n SD: {}'.format(mean, sd)))
    return axis


def plot_nrel(axis, x, y, rmse, n):
    axis.plot(x, y, 'v', markerfacecolor='purple', markeredgecolor='purple', markersize=4, color='purple',
              linestyle='-', lw=.75, label='NREL (RMSE={}, n={})'.format(rmse, n))
    # bd_leg = mlines.Line2D([], [], marker='v', markerfacecolor='purple', markeredgecolor='purple', markersize=4,
    #                        color='purple', label='NREL (RMSE={}, n={})'.format(rmse, n))
    #                        #color='purple', label=('NREL' + '\n Mean: {} \n SD: {}'.format(mean, sd)))
    return axis


def plot_sport(axis, x, y, rmse, n):
    axis.plot(x, y, '^', markerfacecolor='red', markeredgecolor='red', markersize=4, color='red', linestyle='-',
              lw=.75, label='SPoRT (RMSE={}, n={})'.format(rmse, n))
    return axis


def main(start, end, buoys, avgrad, sDir):
    bpudatadir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/'
    headers = ['buoy', 'year-month', 'mean_buoy_nrel', 'sd_buoy_nrel', 'mean_nrel', 'sd_nrel', 'mean_buoy_avhrr',
               'sd_buoy_avhrr', 'mean_avhrr', 'sd_avhrr', 'mean_buoy_sport', 'sd_buoy_sport', 'mean_sport', 'sd_sport',
               'RMSE_nrel', 'RMSE_avhrr', 'RMSE_sport', 'n_nrel', 'n_avhrr', 'n_sport',
               'diff_nrel (sat-buoy)', 'diff_avhrr (sat-buoy)', 'diff_sport (sat-buoy)']
    summary = []
    dsummary = pd.DataFrame(columns=['buoy', 'time', 'buoy_sst_mean', 'dailyavhrr_sst', 'sport_sst', 'nrel_sst'])
    for buoy in buoys:
        print(buoy)

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
                t0 = format_dates(t0)

            if not isinstance(t1, int):  # if t1 is not integer, define date
                t1 = format_dates(t1)

            if isinstance(t0, int):  # if t0 is integer, redefine as t1-[t0 days]
                t0 = t1-timedelta(days=t0)

            if isinstance(t1, int):  # if t1 is integer, redefine as t0+[t1 days]
                t1 = t0+timedelta(days=t1)

            # the start date and end dates should be the day before the requested date, because the data from the
            # previous day are used for the model
            t0 = t0.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            t1 = t1.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

            # define array of times
            times = pd.to_datetime(np.arange(t0, t1+timedelta(days=1), timedelta(days=1)))

            all_years = np.unique(times.year)
            #all_years = np.append(all_years, 9999)  # 9999 buoy year is for 'real-time' data (past 45 days)

            # get buoy SST data
            buoy_dict = cf.get_buoy_data(buoy, all_years, t0, t1)

            buoy_full = pd.DataFrame(data={'time': buoy_dict['t'], 'sst': buoy_dict['sst']})
            buoy_full.drop_duplicates(inplace=True)
            buoy_daily = buoy_full.resample('d', on='time').mean().dropna(how='all').reset_index()
            buoy_daily.rename(columns={'sst': 'buoy_sst_mean'}, inplace=True)
            # change day to the next day at 00:00 for plotting
            buoy_daily['time_plt'] = buoy_daily['time'].map(lambda t: t + timedelta(days=1))
            if len(buoy_daily['time_plt']) == 0:
                buoy_status = 'all_nans'
            else:
                buoy_status = 'valid'

            buoylon = buoy_dict['lon']
            buoylat = buoy_dict['lat']

            # array for SST "at" buoy from daily AVHRR-only coldest pixel composite
            coldsst = initialize_empty_array(times)

            # array for SST "at" buoy from SPoRT (on server)
            sportsst = initialize_empty_array(times)

            # array for SST "at" buoy from the NREL case study (on server)
            nrelsst = initialize_empty_array(times)
            if buoy_status == 'valid':
                for t in times:
                    # daily AVHRR coldest pixel composite
                    ldir = '/Users/lgarzio/Documents/rucool/satellite/coldest_pixel/'
                    # satfile = '{}daily_avhrr/composites/{}/avhrr_coldest-pixel_{}.nc'.format(bpudatadir, t.strftime('%Y'),
                    #                                                                          t.strftime('%Y%m%d'))
                    satfile = '{}daily_avhrr/composites/{}/avhrr_coldest-pixel_{}.nc'.format(ldir,
                                                                                             t.strftime('%Y'),
                                                                                             t.strftime('%Y%m%d'))
                    try:
                        cvalue = cf.append_satellite_sst_data(satfile, buoylat, buoylon, avgrad, 'daily_avhrr', 'sst')
                        coldsst[times == t] = cvalue
                    except:
                        print('Issue reading from {}'.format(satfile))

                    # SPoRT only
                    sp_file = glob.glob(bpudatadir + 'sport_nc/' + t.strftime('%Y%m%d') + '*.nc')
                    if len(sp_file) == 1:
                        try:
                            svalue = cf.append_satellite_sst_data(sp_file[0], buoylat, buoylon, avgrad, 'sport',
                                                                  'TMP_P0_L1_GLL0')
                            sportsst[times == t] = svalue
                        except:
                            print('Issue reading from {}'.format(sp_file[0]))

                    else:
                        print('{} files found for SPoRT at time {}'.format(str(len(sp_file)), t.strftime('%Y-%m-%d')))

                    # NREL case study
                    nrel_dir = '{}composite_archive/NREL_case_study/'.format(bpudatadir)
                    nrel_file = glob.glob(nrel_dir + '/procdate_' + t.strftime('%Y%m%d') + '*.nc')
                    if len(nrel_file) == 1:
                        try:
                            nrel_value = cf.append_satellite_sst_data(nrel_file[0], buoylat, buoylon, avgrad, 'nrel', 'sst')
                            nrelsst[times == t] = nrel_value
                        except:
                            print('Issue reading from {}'.format(nrel_file))
                    else:
                        print('{} files found for NREL file at time {}'.format(str(len(nrel_file)), t.strftime('%Y-%m-%d')))

                # plot
                times_plt = times + timedelta(days=1)

                # if there is any data available for that time period, proceed with plotting
                if (buoy_status == 'valid') or (cf.check_nans(nrelsst) == 'valid'):

                    save_dir = os.path.join(sDir, 'NREL', buoy)
                    cf.create_dir(save_dir)

                    # calculate stats

                    # create dataframe only when there are data available from both methods (inner join and drop nans)
                    sat_df = pd.DataFrame({'time': times, 'dailyavhrr_sst': coldsst, 'sport_sst': sportsst, 'nrel_sst': nrelsst})
                    df = pd.merge(buoy_daily, sat_df, on='time', how='inner')
                    df.dropna(axis=0, subset=['buoy_sst_mean', 'nrel_sst'], inplace=True)
                    if len(df) > 0:
                        buoy_data = np.array(df['buoy_sst_mean'])
                        nrel_data = np.array(df['nrel_sst'])
                        avhrr_data = np.array(df['dailyavhrr_sst'])
                        sport_data = np.array(df['sport_sst'])

                        [mbuoy_nrel, mnrel, sdbuoy_nrel, sd_nrel, diff_nrel, rmse_nrel, n_nrel] = cf.statistics(buoy_data,
                                                                                                                nrel_data)
                        [mbuoy_av, mav, sdbuoy_av, sd_av, diff_av, rmse_av, n_av] = cf.statistics(buoy_data, avhrr_data)
                        [mbuoy_sp, msp, sdbuoy_sp, sd_sp, diff_sp, rmse_sp, n_sp] = cf.statistics(buoy_data, sport_data)

                        # add monthly stats to summary
                        summary.append(
                            [buoy, t0.strftime('%Y%m'), mbuoy_nrel, sdbuoy_nrel, mnrel, sd_nrel,
                             mbuoy_av, sdbuoy_av, mav, sd_av, mbuoy_sp, sdbuoy_sp,
                             msp, sd_sp, rmse_nrel, rmse_av, rmse_sp, n_nrel, n_av, n_sp, diff_nrel, diff_av, diff_sp])

                        # add daily data to summary
                        df.drop(axis=1, columns='time_plt', inplace=True)
                        df['buoy'] = [buoy] * len(df)
                        dsummary = dsummary.append(df, sort=False)

                        # plot buoy raw and average along with NREL
                        sname = '{}_sst_comparison_{}_{}'.format(buoy, t1.strftime('%Y%m'), 'NREL')
                        fig, ax = plt.subplots()
                        plt.grid()
                        ax = plot_buoy_full(ax, buoy_full, buoy)
                        ax = plot_buoy_daily(ax, buoy_daily)
                        ax = plot_avhrr(ax, times_plt, coldsst, rmse_av, n_av)
                        ax = plot_sport(ax, times_plt, sportsst, rmse_sp, n_sp)
                        ax = plot_nrel(ax, times_plt, nrelsst, rmse_nrel, n_nrel)

                        ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
                        pf.format_date_axis(ax, fig)
                        pf.y_axis_disable_offset(ax)
                        ax.legend(loc='best', fontsize=5.5)
                        # rmse_leg = mlines.Line2D([], [], markerfacecolor='none', markeredgecolor='none', markersize=1,
                        #                          color='none', label=('RMSE: {} (n={})'.format(rmse_nrel, n_nrel)))
                        # ax.legend(handles=[bf_leg, bd_leg, nrel_leg], loc='best', fontsize=5.5)

                        pf.save_fig(save_dir, sname)

                else:
                    print('No data available from any source for buoy {}: from {} to {}'.format(buoy, t0.strftime('%Y-%m-%d'),
                                                                                                t1.strftime('%Y-%m-%d')))
    sdf = pd.DataFrame(summary, columns=headers)
    sdf.to_csv('{}/{}/NREL_buoy_comparison.csv'.format(sDir, 'NREL'), index=False)

    dsummary.to_csv('{}/{}/NREL_buoy_daily_sst.csv'.format(sDir, 'NREL'), index=False)


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    start = '6-1-2015'
    end = '5-31-2016'
    buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
             '44017', '44018', '44020', '44025', '44027', '44065']
    avgrad = 'closestwithin5'
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
    main(start, end, buoys, avgrad, sDir)
