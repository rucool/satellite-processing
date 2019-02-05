#! /usr/bin/env python

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import os


def format_date_axis(axis, figure):
    df = mdates.DateFormatter('%Y-%m-%d')
    axis.xaxis.set_major_formatter(df)
    figure.autofmt_xdate()


def format_date_axis_month(axis, figure):
    df = mdates.DateFormatter('%Y-%m')
    axis.xaxis.set_major_formatter(df)
    figure.autofmt_xdate()


def save_fig(save_dir, file_name, res=300):
    # save figure to a directory with a resolution of 300 DPI
    save_file = os.path.join(save_dir, file_name)
    plt.savefig(str(save_file), dpi=res)
    plt.close()


def y_axis_disable_offset(axis):
    # format y-axis to disable offset
    y_formatter = ticker.ScalarFormatter(useOffset=False)
    axis.yaxis.set_major_formatter(y_formatter)
