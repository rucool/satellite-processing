#!/usr/bin/env python
"""
@author Laura Nazarro
@modified by Lori Garzio on 1/16/2018
@brief compare buoy data with satellite SST data from the NREL case study
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


def plot_buoy_full(axis, fbuoy_df, buoy):
    axis.plot(fbuoy_df['time'], fbuoy_df['sst'], '.', markerfacecolor='grey', markeredgecolor='grey', markersize=1,
              label='Buoy {}'.format(buoy))
    return axis


def plot_buoy_daily(axis, dbuoy_df):
    axis.plot(dbuoy_df['time_plt'], dbuoy_df['sst'], 'o', markerfacecolor='black', markeredgecolor='black',
              markersize=4, color='black', linestyle='-', lw=.75, label='Daily Buoy Mean')
    return axis


def plot_nrel(axis, x, y):
    axis.plot(x, y, 'v', markerfacecolor='purple', markeredgecolor='purple', markersize=4, color='purple',
              linestyle='-', lw=.75, label='NREL')
    return axis


def main(t0, t1, buoy, avgrad, sDir):
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

    all_years = np.unique(times.year)
    #all_years = np.append(all_years, 9999)  # 9999 buoy year is for 'real-time' data (past 45 days)

    # get buoy SST data
    buoy_dict = cf.get_buoy_data(buoy, all_years, t0, t1)

    buoy_full = pd.DataFrame(data={'time': buoy_dict['t'], 'sst': buoy_dict['sst']})
    buoy_full.drop_duplicates(inplace=True)
    buoy_daily = buoy_full.resample('d', on='time').mean().dropna(how='all').reset_index()
    # change day to the next day at 00:00 for plotting
    buoy_daily['time_plt'] = buoy_daily['time'].map(lambda t: t + timedelta(days=1))
    if len(buoy_daily['time_plt']) == 0:
        buoy_status = 'all_nans'
    else:
        buoy_status = 'valid'

    buoylon = buoy_dict['lon']
    buoylat = buoy_dict['lat']

    # array for SST "at" buoy from the NREL case study (on server)
    nrelsst = initialize_empty_array(times)
    if buoy_status == 'valid':
        for t in times:
            # NREL case study
            nrel_dir = '{}composite_archive/NREL_case_study/'.format(bpudatadir)
            satfile = glob.glob(nrel_dir + '/procdate_' + t.strftime('%Y%m%d') + '*.nc')
            if len(satfile) == 1:
                try:
                    nrel_value = cf.append_satellite_sst_data(satfile[0], buoylat, buoylon, avgrad, 'nrel', 'sst')
                    nrelsst[times == t] = nrel_value
                except:
                    print('Issue reading from {}'.format(satfile))
            else:
                print('{} files found for NREL file at time {}'.format(str(len(satfile)), t.strftime('%Y-%m-%d')))

        # plot
        times_plt = times + timedelta(days=1)

        # if there is any data available for that time period, proceed with plotting
        if (buoy_status == 'valid') or (cf.check_nans(nrelsst) == 'valid'):

            save_dir = os.path.join(sDir, 'NREL', buoy)
            cf.create_dir(save_dir)

            # plot buoy raw and average along with NREL
            sname = '{}_sst_comparison_{}_{}'.format(buoy, t1.strftime('%Y%m'), 'NREL')
            sname_mean = '{}_{}'.format(sname, 'avg')
            fig, ax = plt.subplots()
            plt.grid()
            ax = plot_buoy_full(ax, buoy_full, buoy)
            ax = plot_buoy_daily(ax, buoy_daily)
            ax = plot_nrel(ax, times_plt, nrelsst)

            ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
            pf.format_date_axis(ax, fig)
            pf.y_axis_disable_offset(ax)
            ax.legend(loc='best', fontsize=5.5)
            pf.save_fig(save_dir, sname_mean)

            # plot just buoy raw and NREL
            fig, ax = plt.subplots()
            plt.grid()
            ax = plot_buoy_full(ax, buoy_full, buoy)
            ax = plot_nrel(ax, times_plt, nrelsst)

            ax.set_ylabel('Sea Surface Temperature (Celsius)', fontsize=9)
            pf.format_date_axis(ax, fig)
            pf.y_axis_disable_offset(ax)
            ax.legend(loc='best', fontsize=5.5)
            pf.save_fig(save_dir, sname)

        else:
            print('No data available from any source for buoy {}: from {} to {}'.format(buoy, t0.strftime('%Y-%m-%d'),
                                                                                        t1.strftime('%Y-%m-%d')))


if __name__ == '__main__':
    t0 = '5-30-2015'   # 5 or '01-14-2019'
    t1 = '6-30-2015'  # 5 or '01-16-2019'
    buoy = '44009'
    avgrad = 'closestwithin5'
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp'
    main(t0, t1, buoy, avgrad, sDir)
