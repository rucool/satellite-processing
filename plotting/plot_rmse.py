#!/usr/bin/env python
"""
Create by Lori Garzio on 1/16/2019
@brief plot RMSE stats from different models compared to buoy measurements
@usage
"""


import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime as dt
import functions.common as cf
import functions.plotting as pf
pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console


def plot_avhrr(axis, x, y):
    axis.plot(x, y, 's', markerfacecolor='blue', markeredgecolor='blue', markersize=4, color='blue', linestyle='-',
              lw=.75, label='Daily AVHRR')
    return axis


def plot_nrel(axis, x, y):
    axis.plot(x, y, 'v', markerfacecolor='purple', markeredgecolor='purple', markersize=4, color='purple',
              linestyle='-', lw=.75, label='NREL')
    return axis


def plot_sport(axis, x, y):
    axis.plot(x, y, '^', markerfacecolor='red', markeredgecolor='red', markersize=4, color='red', linestyle='-',
              lw=.75, label='SPoRT')
    return axis


def main(df, sDir, buoys):
    for buoy in buoys:
        dfb = df[df['buoy'] == int(buoy)]
        if len(dfb) > 0:
            fig, ax = plt.subplots()
            plt.grid()
            x = dfb['year-month'].map(lambda t: dt.datetime.strptime(str(t), '%Y%m'))
            ax = plot_avhrr(ax, x, dfb['RMSE_avhrr'])
            ax = plot_sport(ax, x, dfb['RMSE_sport'])
            ax = plot_nrel(ax, x, dfb['RMSE_nrel'])

            ax.set_ylabel('RMSE', fontsize=9)
            ax.legend(loc='best', fontsize=6.5)
            plt.title('Monthly RMSE compared to buoy {} measurements'.format(buoy), fontsize=9)
            pf.format_date_axis_month(ax, fig)
            sname = '{}_rmse'.format(buoy)
            pf.save_fig(sDir, sname)


if __name__ == '__main__':
    df = pd.read_csv('/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/NREL/NREL_buoy_comparison.csv')
    sDir = '/Users/lgarzio/Documents/rucool/satellite/sst_buoy_comp/NREL/RMSE_plots'
    buoys = ['41001', '41002', '41004', '41008', '41013', '44005', '44007', '44008', '44009', '44011', '44013', '44014',
             '44017', '44018', '44020', '44025', '44027', '44065']
    main(df, sDir, buoys)
