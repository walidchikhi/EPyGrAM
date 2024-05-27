#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Météo France (2014-)
# This software is governed by the CeCILL-C license under French law.
# http://www.cecill.info

from __future__ import print_function, absolute_import, unicode_literals, division
from six.moves import input
import os
import sys
import argparse
import epygram
from epygram import epylog
from epygram.geometries import domain_making as dm
from epygram.args_catalog import (add_arg_to_parser,
                                  domain_maker_options,
                                  runtime_options,
                                  graphical_options)


def main():
    parser = argparse.ArgumentParser(description='An interactive EPyGrAM tool for defining a LAM domain, visualize it, and generate the needed namelist blocks.',
                                     epilog='End of help for: %(prog)s (EPyGrAM v' + epygram.__version__ + ')')

    add_arg_to_parser(parser, domain_maker_options['mode'])
    add_arg_to_parser(parser, domain_maker_options['no_display'])
    add_arg_to_parser(parser, domain_maker_options['maximize_CI_in_E'])
    add_arg_to_parser(parser, domain_maker_options['truncation'])
    add_arg_to_parser(parser, domain_maker_options['orography_subtruncation'])
    add_arg_to_parser(parser, runtime_options['verbose'])
    add_arg_to_parser(parser, graphical_options['french_departments'])
    add_arg_to_parser(parser, graphical_options['background'], default=True)

    args = parser.parse_args()

    epygram.init_env()
    epylog.setLevel('WARNING')
    if args.verbose:
        epylog.setLevel('INFO')

    run_domain_maker(args.mode,
                     display=not args.no_display,
                     maximize_CI_in_E=args.maximize_CI_in_E,
                     french_depts=args.depts,
                     background=args.background,
                     truncation=args.truncation,
                     orography_subtruncation=args.orography_subtruncation)


def run_domain_maker(mode, display=True, maximize_CI_in_E=False, french_depts=False, background=True, truncation='linear', orography_subtruncation='quadratic'):
    print("################")
    print("# DOMAIN MAKER #")
    print("################")
    if not epygram.util.mpl_interactive_backend():
        out = 'domain_maker.out.' + epygram.config.default_graphical_output
    else:
        out = None
    if mode == 'center_dims':
        defaults = {'Iwidth': None,
                    'tilting': 0.0,
                    'resolution': '',
                    'center_lon': '',
                    'center_lat': '',
                    'Xpoints_CI': '',
                    'Ypoints_CI': ''}

        retry = True
        while retry:
            (geometry, defaults) = dm.ask.ask_and_build_geometry(defaults, maximize_CI_in_E)
            print("Compute domain...")
            print(dm.output.summary(geometry))
            if display:
                plot_lonlat_included = input("Plot a lon/lat domain over model domain ? [n]: ")
                if plot_lonlat_included in ('y', 'Y', 'yes'):
                    plot_lonlat_included = True
                else:
                    plot_lonlat_included = False
                if plot_lonlat_included:
                    proposed = dm.build.compute_lonlat_included(geometry)
                    print("Min/Max longitudes & latitudes of the lon/lat domain (defaults to that proposed above):")
                    ll_boundaries = dm.ask.ask_lonlat(proposed)
                else:
                    ll_boundaries = None
                print("Plot domain...")
                dm.output.plot_geometry(geometry,
                                        lonlat_included=ll_boundaries,
                                        out=out,
                                        departments=french_depts,
                                        background=background,
                                        plotlib='cartopy')
            retry = input("Do you want to modify something ? [n] ")
            if retry in ('yes', 'y', 'Y'):
                retry = True
            else:
                retry = False

    elif mode == 'lonlat_included':
        defaults = {'Iwidth': None,
                    'lonmax': '',
                    'lonmin': '',
                    'latmax': '',
                    'latmin': '',
                    'resolution': ''}

        retry = True
        while retry:
            (geometry, defaults) = dm.ask.ask_lonlat_and_build_geometry(defaults, maximize_CI_in_E)
            print(dm.output.summary(geometry))
            if display:
                print("Plot domain...")
                dm.output.plot_geometry(geometry,
                                        lonlat_included=defaults,
                                        out=out,
                                        departments=french_depts,
                                        background=background,
                                        plotlib='cartopy')
            retry = input("Do you want to modify something ? [n] ")
            if retry in ('yes', 'y', 'Y'):
                retry = True
            else:
                retry = False
    else:
        raise ValueError("invalid value for 'mode' argument")

    dm.output.write_geometry_as_namelists(geometry, allinone=True, truncation=truncation, orography_subtruncation=orography_subtruncation)


if __name__ == '__main__':
    main()

