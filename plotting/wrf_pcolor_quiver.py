#!/usr/bin/env python
"""
Create by Lori Garzio on 4/2/2019
@brief Create pcolor quiver maps of wind speeds for RU-WRF output and pcolor maps of wind power
"""

import numpy as np
import pandas as pd
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import xarray as xr
from oceans.ocfis import uv2spdir, spdir2uv
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cmocean.cm as cmo
import functions.common as cf
import functions.plotting as pf


def get_data(ncfilepath, height):
    nc = xr.open_dataset(ncfilepath, mask_and_scale=False)
    if height == 10:
        u = np.squeeze(nc['U10'])
        v = np.squeeze(nc['V10'])
        lat = nc['XLAT'].values
        lon = nc['XLONG'].values
    else:
        fnc = nc.sel(height=height)  # subset variables at specified height
        u = np.squeeze(fnc['U'])
        v = np.squeeze(fnc['V'])
        lat = fnc['XLAT'].values
        lon = fnc['XLONG'].values

    angle, speed = uv2spdir(u, v)
    us, vs = spdir2uv(np.ones_like(speed), angle, deg=True)

    return lat, lon, speed, us, vs, u, v


def plot_pcolor_power(save_file, figtitle, latdata, londata, wnd_power, lease_area, plan_area, blats, blons, diff_plot=None):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.subplots_adjust(right=0.87)
    plt.title(figtitle, fontsize=17)

    if diff_plot == 'diff_plot':
        h = ax.pcolor(londata, latdata, wnd_power, vmin=-8000, vmax=8000, cmap=cmo.curl)
        cblabel = 'Estimated 8MW Wind Power Difference (kW)'
    else:
        h = ax.pcolor(londata, latdata, wnd_power, cmap='OrRd')
        cblabel = 'Estimated 8MW Wind Power (kW)'
    plt.rcParams.update({'font.size': 14})

    ax = pf.add_map_features(ax)
    lease_area.plot(ax=ax, color='none', edgecolor='black')
    plan_area.plot(ax=ax, color='none', edgecolor='dimgray')

    # add buoy locations
    ax.scatter(blons, blats, facecolors='whitesmoke', edgecolors='black', linewidth='2', s=60)

    # add DOE LIDAR buoy location
    ax.scatter(-74.401, 39.314, facecolors='magenta', edgecolors='black', linewidth='2', s=60, label='DOE LIDAR')

    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)
    cb = plt.colorbar(h, cax=cax, label=cblabel)
    cb.ax.tick_params(labelsize=14)
    plt.savefig(save_file, dpi=300)
    plt.close('all')


def plot_pcolor_quiver(save_file, figtitle, latdata, londata, ws, us, vs, lease_area, plan_area, blats, blons, diff_plot=None):
    sub = 5
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    plt.title(figtitle, fontsize=17)

    if diff_plot == 'diff_plot':
        h = ax.pcolor(londata, latdata, ws, vmin=-3.0, vmax=3.0, cmap=cmo.balance)
        cblabel = 'Wind Speed Difference (m/s)'
    else:
        #h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=14.0, cmap='jet')
        h = ax.pcolor(londata, latdata, ws, vmin=4.0, vmax=16.0, cmap='jet')
        cblabel = 'Wind Speed (m/s)'

    plt.rcParams.update({'font.size': 14})
    ax.quiver(londata[::sub, ::sub], latdata[::sub, ::sub], us[::sub, ::sub], vs[::sub, ::sub], cmap='jet',
              scale=40, width=.0015, headlength=3)

    ax = pf.add_map_features(ax)

    lease_area.plot(ax=ax, color='none', edgecolor='black')
    plan_area.plot(ax=ax, color='none', edgecolor='dimgray')

    if diff_plot != 'diff_plot':
        CS = ax.contour(londata, latdata, ws, [0, 12.5], colors='whitesmoke', linewidths=2)
        ax.clabel(CS, inline=1, fontsize=10.5, fmt='%.1f')

    # add buoy locations
    ax.scatter(blons, blats, facecolors='whitesmoke', edgecolors='black', linewidth='2', s=60)

    # add DOE LIDAR buoy location
    ax.scatter(-74.401, 39.314, facecolors='magenta', edgecolors='black', linewidth='2', s=60, label='DOE LIDAR')

    # add colorbar
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)
    cb = plt.colorbar(h, cax=cax, label=cblabel)
    cb.ax.tick_params(labelsize=14)
    plt.savefig(save_file, dpi=300)
    plt.close('all')


def main(sDir, time_range, ht, buoys, ru_wrf_v, plt_power):
    if ru_wrf_v == 4:
        #rootdir = '/Volumes/boardwalk/coolgroup/ru-wrf/testv4/case_studies/20150803/3km/processed/'  # WRF v4.0
        rootdir = '/Volumes/boardwalk/coolgroup/ru-wrf/testv4/case_studies/20160724/3km/processed/'  # WRF v4.0
        main_ttl = 'RU-WRF Winds 4.0:'
    else:
        #rootdir = '/Volumes/boardwalk/coolgroup/ru-wrf/case_studies/20150803/3km/processed/'
        rootdir = '/Volumes/boardwalk/coolgroup/ru-wrf/case_studies/20160724/3km/processed/'
        main_ttl = 'RU-WRF Winds 3.9:'

    if plt_power == 'yes':
        power_curve = pd.read_csv('/Users/lgarzio/Documents/rucool/satellite/wrf_power_curve/wrf_lw8mw_power.csv')
        if ru_wrf_v == 4:
            power_main_ttl = 'RU-WRF Wind Power 4.0:'
        else:
            power_main_ttl = 'RU-WRF Wind Power 3.9:'

    cpdir = os.path.join(rootdir, 'coldestpixel')
    rtgdir = os.path.join(rootdir, 'rtg')

    #boem_rootdir = '/home/coolgroup/bpu/mapdata/shapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018'
    boem_rootdir = '/Users/lgarzio/Documents/rucool/satellite/BOEMshapefiles/BOEM_Renewable_Energy_Areas_Shapefiles_10_24_2018'
    leasing_areas, planning_areas = cf.boem_shapefiles(boem_rootdir)

    cf.create_dir(sDir)

    buoy_lats, buoy_lons = cf.get_buoy_locations(buoys)

    for r in time_range:
        fend = '*H{}.nc'.format('%03d' % r)

        # Coldest pixel
        cpf = glob.glob(cpdir + '/wrfproc_3km' + fend)
        fname = cpf[0].split('/')[-1]
        print('Plotting {}'.format(fname))

        cp_lat, cp_lon, cp_speed, cp_us, cp_vs, cp_u, cp_v = get_data(cpf[0], ht)

        cptitle = '{} {}m, Coldest Pixel SST'.format(main_ttl, str(ht))
        title2 = '{} {}{}'.format(datetime.strftime(datetime.strptime(fname.split('_')[2], '%Y%m%d'), '%Y-%m-%d'),
                                  fname.split('_')[-1][2:4], 'Z')
        cpfigtitle = '{}\n{}'.format(cptitle, title2)
        cpfigname = 'coldestpixel{}m_{}'.format(str(ht), fname.split('.')[0])
        cpsfile = os.path.join(sDir, cpfigname)
        plot_pcolor_quiver(cpsfile, cpfigtitle, cp_lat, cp_lon, cp_speed, cp_us, cp_vs, leasing_areas, planning_areas,
                           buoy_lats, buoy_lons)

        if plt_power == 'yes':
            cp_wind_power = np.interp(cp_speed, power_curve['Wind Speed'], power_curve['Power'])
            cp_powerfigname = 'coldestpixel_power{}m_{}'.format(str(ht), fname.split('.')[0])
            cp_power_sname = os.path.join(sDir, cp_powerfigname)
            cp_powerttl = '{} {}m, Coldest Pixel SST'.format(power_main_ttl, str(ht))
            cp_p_ttl = '{}\n{}'.format(cp_powerttl, title2)
            plot_pcolor_power(cp_power_sname, cp_p_ttl, cp_lat, cp_lon, cp_wind_power, leasing_areas, planning_areas,
                              buoy_lats, buoy_lons)

        # RTG
        rtgf = glob.glob(rtgdir + '/wrfproc_3km' + fend)
        rtg_lat, rtg_lon, rtg_speed, rtg_us, rtg_vs, rtg_u, rtg_v = get_data(rtgf[0], ht)

        rtgtitle = '{} {}m, RTG SST'.format(main_ttl, str(ht))
        rtgfigtitle = '{}\n{}'.format(rtgtitle, title2)
        rtgfigname = 'rtg{}m_{}'.format(str(ht), fname.split('.')[0])
        rtgsfile = os.path.join(sDir, rtgfigname)
        plot_pcolor_quiver(rtgsfile, rtgfigtitle, rtg_lat, rtg_lon, rtg_speed, rtg_us, rtg_vs, leasing_areas,
                           planning_areas, buoy_lats, buoy_lons)

        if plt_power == 'yes':
            rtg_wind_power = np.interp(rtg_speed, power_curve['Wind Speed'], power_curve['Power'])
            rtg_powerfigname = 'rtg_power{}m_{}'.format(str(ht), fname.split('.')[0])
            rtg_power_sname = os.path.join(sDir, rtg_powerfigname)
            rtg_powerttl = '{} {}m, RTG SST'.format(power_main_ttl, str(ht))
            rtg_p_ttl = '{}\n{}'.format(rtg_powerttl, title2)
            plot_pcolor_power(rtg_power_sname, rtg_p_ttl, rtg_lat, rtg_lon, rtg_wind_power, leasing_areas,
                              planning_areas, buoy_lats, buoy_lons)

        # wind speed difference
        diff_u = cp_u - rtg_u
        diff_v = cp_v - rtg_v

        diff_angle, __ = uv2spdir(diff_u, diff_v)
        diff_speed = cp_speed - rtg_speed
        diff_us, diff_vs = spdir2uv(np.ones_like(diff_speed), diff_angle, deg=True)

        # exclude outliers > 5 SD
        if np.nanmax(abs(diff_speed)) > 1:
            stdev = np.nanstd(diff_speed)
            dmax = np.nanmean(diff_speed) + 5 * stdev
            diff_speed[diff_speed > dmax] = np.nan

        difftitle = '{} {}m, Difference (ColdPix - RTG)'.format(main_ttl, str(ht))
        difffigtitle = '{}\n{}'.format(difftitle, title2)
        difffigname = 'difference{}m_{}'.format(str(ht), fname.split('.')[0])
        diffsfile = os.path.join(sDir, difffigname)
        plot_pcolor_quiver(diffsfile, difffigtitle, rtg_lat, rtg_lon, diff_speed, diff_us, diff_vs, leasing_areas,
                           planning_areas, buoy_lats, buoy_lons, 'diff_plot')

        # power difference
        if plt_power == 'yes':
            diff_power = cp_wind_power - rtg_wind_power
            diff_power_title = '{} {}m, Difference (ColdPix - RTG)'.format(power_main_ttl, str(ht))
            difffig_powertitle = '{}\n{}'.format(diff_power_title, title2)
            diff_powerfigname = 'difference_power{}m_{}'.format(str(ht), fname.split('.')[0])
            diff_powersfile = os.path.join(sDir, diff_powerfigname)
            plot_pcolor_power(diff_powersfile, difffig_powertitle, rtg_lat, rtg_lon, diff_power, leasing_areas,
                              planning_areas, buoy_lats, buoy_lons, 'diff_plot')


if __name__ == '__main__':
    pd.set_option('display.width', 320, "display.max_columns", 10)  # for display in pycharm console
    save_dir = '/Users/lgarzio/Documents/rucool/satellite/20160724_upwelling_analysis/wrf3.9_windspeed_power_120m'
    hour_time_range = cf.range1(00, 30)
    wndsp_height = 120  # wind speed height
    ndbc_buoys = ['44009', '44025', '44065']
    ru_wrf_version = 3  # options: 3, 4
    plot_power = 'yes'  # options: 'yes', 'no'
    main(save_dir, hour_time_range, wndsp_height, ndbc_buoys, ru_wrf_version, plot_power)
