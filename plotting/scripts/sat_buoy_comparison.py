#!/usr/bin/env python
"""
@author Laura Nazarro
@modified by Lori Garzio on 1/16/2018
@brief compare buoy data with satellite SST data
"""

import matplotlib.pyplot as plt
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


def plot_avhrr(axis, x, y):
    axis.plot(x, y, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=4, color='blue', linestyle='-',
              lw=.75, label='Daily Coldest Pixel (AVHRR)')
    return axis


def plot_buoy_full(axis, fbuoy_df, buoy):
    axis.plot(fbuoy_df['time'], fbuoy_df['sst'], '.', markerfacecolor='grey', markeredgecolor='grey', markersize=1,
              label='Buoy {}'.format(buoy))
    return axis


def plot_buoy_daily(axis, dbuoy_df):
    axis.plot(dbuoy_df['time_plt'], dbuoy_df['sst'], 'o', markerfacecolor='black', markeredgecolor='black',
              markersize=4, color='black', linestyle='-', lw=.75, label='Daily Buoy Mean')
    return axis


def plot_sport(axis, x, y):
    axis.plot(x, y, '^', markerfacecolor='red', markeredgecolor='red', markersize=4, color='red', linestyle='-',
              lw=.75, label='SPoRT')
    return axis


def plot_wrf_input(axis, x, y):
    axis.plot(x, y, 'v', markerfacecolor='purple', markeredgecolor='purple', markersize=4, color='purple',
              linestyle='-', lw=.75, label='WRF Input SST (3 day)')
    return axis


def main(t0, t1, buoy, avgrad, sDir, models):
    bpudatadir = '/Volumes/boardwalk/coolgroup/bpu/wrf/data/'

    if not isinstance(t0, int):  # if t0 is not integer, define date
        t0 = format_dates(t0)

    if not isinstance(t1, int):  # if t1 is not integer, define date
        t1 = format_dates(t1)

    if isinstance(t0, int):  # if t0 is integer, redefine as t1-[t0 days]
        t0 = t1-timedelta(days=t0)

    if isinstance(t1, int):  # if t1 is integer, redefine as t0+[t1 days]
        t1 = t0+timedelta(days=t1)

    t0 = t0.replace(hour=0, minute=0, second=0, microsecond=0)
    t1 = t1.replace(hour=0, minute=0, second=0, microsecond=0)

    # define array of times
    times = pd.to_datetime(np.arange(t0, t1+timedelta(days=1), timedelta(days=1)))

    all_years = np.unique(times.year)  ###########  make this an input option ######################
    all_years = np.append(all_years, 9999)  # 9999 buoy year is for 'real-time' data (past 45 days)

    # get buoy SST data
    buoy_dict = cf.get_buoy_data(buoy, all_years, t0, t1)

    buoy_full = pd.DataFrame(data={'time': buoy_dict['t'], 'sst': buoy_dict['sst']})
    buoy_full.drop_duplicates(inplace=True)  # buoy file 9999 contains the same data found in other files
    buoy_daily = buoy_full.resample('d', on='time').mean().dropna(how='all').reset_index()
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

    # array for SST "at" buoy from 3-day AVHRR + SPoRT coldest pixel composite (WRF input)
    coldsportsst = initialize_empty_array(times)

    # array for SST "at" buoy from SPoRT (on server)
    sportsst = initialize_empty_array(times)

    if type(buoylon) == np.float32 and type(buoylat) == np.float32:
        for t in times:
            # daily AVHRR coldest pixel composite
            satfile = '{}daily_avhrr/composites/{}/avhrr_coldest-pixel_{}.nc'.format(bpudatadir, t.strftime('%Y'),
                                                                                     t.strftime('%Y%m%d'))
            try:
                cvalue = cf.append_satellite_sst_data(satfile, buoylat, buoylon, avgrad, 'daily_avhrr', 'sst')
                coldsst[times == t] = cvalue
            except:
                print('Issue reading from {}'.format(satfile))

            #  3-day AVHRR + SPoRT coldest pixel composite (WRF input)
            if t >= datetime.strptime('01-01-2017', '%m-%d-%Y'):
                sat_pre = bpudatadir + 'composites/procdate_'
            else:
                sat_pre = bpudatadir + 'composites/archive_no_time_field/sport_'
            spcomp_file = glob.glob(sat_pre + t.strftime('%Y%m%d') + '*.nc')
            if len(spcomp_file) == 1:
                try:
                    csvalue = cf.append_satellite_sst_data(spcomp_file[0], buoylat, buoylon, avgrad, 'cold_sport', 'sst')
                    coldsportsst[times == t] = csvalue
                except:
                    print('Issue reading from {}'.format(spcomp_file[0]))

            else:
                print('{} files found for SPoRT+AVHRR at time {}'.format(str(len(spcomp_file)), t.strftime('%Y-%m-%d')))

            # SPoRT only
            sp_file = glob.glob(bpudatadir + 'sport_nc/' + t.strftime('%Y%m%d') + '*.nc')
            if len(sp_file) == 1:
                try:
                    svalue = cf.append_satellite_sst_data(sp_file[0], buoylat, buoylon, avgrad, 'sport', 'TMP_P0_L1_GLL0')
                    sportsst[times == t] = svalue
                except:
                    print('Issue reading from {}'.format(sp_file[0]))

            else:
                print('{} files found for SPoRT at time {}'.format(str(len(sp_file)), t.strftime('%Y-%m-%d')))

    # plot
    times_plt = times + timedelta(days=1)

    # if there is any data available for that time period, proceed with plotting
    if (buoy_status == 'valid') or (cf.check_nans(coldsst) == 'valid') or (cf.check_nans(sportsst) == 'valid') or \
            (cf.check_nans(coldsportsst) == 'valid'):

        save_dir = os.path.join(sDir, t1.strftime('%Y%m%d'))
        cf.create_dir(save_dir)

        for model in models:
            sname = '{}_sst_comparison_{}_{}-{}'.format(buoy, model, t0.strftime('%Y%m%d'), t1.strftime('%Y%m%d'))
            if model == 'WRFsport_avhrr':
                fig, ax = plt.subplots()
                plt.grid()
                ax = plot_buoy_full(ax, buoy_full, buoy)
                ax = plot_buoy_daily(ax, buoy_daily)
                ax = plot_avhrr(ax, times_plt, coldsst)
                ax = plot_sport(ax, times_plt, sportsst)
                ax = plot_wrf_input(ax, times_plt, coldsportsst)

                ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
                pf.format_date_axis(ax, fig)
                pf.y_axis_disable_offset(ax)
                ax.legend(loc='best', fontsize=5.5)
                pf.save_fig(save_dir, sname)

            elif model == 'WRFonly':
                if cf.check_nans(coldsportsst) == 'valid':  # if the dataset isn't all nans
                    fig, ax = plt.subplots()
                    plt.grid()
                    ax = plot_buoy_full(ax, buoy_full, buoy)
                    ax = plot_wrf_input(ax, times_plt, coldsportsst)

                    ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
                    pf.format_date_axis(ax, fig)
                    pf.y_axis_disable_offset(ax)
                    ax.legend(loc='best', fontsize=5.5)
                    pf.save_fig(save_dir, sname)

            elif model == 'WRFsport':
                fig, ax = plt.subplots()
                plt.grid()
                ax = plot_buoy_full(ax, buoy_full, buoy)
                ax = plot_sport(ax, times_plt, sportsst)
                ax = plot_wrf_input(ax, times_plt, coldsportsst)

                ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
                pf.format_date_axis(ax, fig)
                pf.y_axis_disable_offset(ax)
                ax.legend(loc='best', fontsize=5.5)
                pf.save_fig(save_dir, sname)

    else:
        print('No data available from any source for buoy {}: from {} to {}'.format(buoy, t0.strftime('%Y-%m-%d'),
                                                                                    t1.strftime('%Y-%m-%d')))


if __name__ == '__main__':
    t0 = 14   # '01-14-2019'
    t1 = 'today'  # '01-16-2019'
    buoy = '44007'
    avgrad = 'closestwithin5'
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
    models = ['WRFsport_avhrr']  # ['WRFsport_avhrr', 'WRFonly', 'WRFsport']
    main(t0, t1, buoy, avgrad, sDir, models)
