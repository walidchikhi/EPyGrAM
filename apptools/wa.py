#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Météo France (2014-)
# This software is governed by the CeCILL-C license under French law.
# http://www.cecill.info

from __future__ import print_function, absolute_import, unicode_literals, division
import six
import os
import sys
import argparse
import epygram
from epygram import epylog
from epygram.args_catalog import (add_arg_to_parser,
                                  files_management, fields_management,
                                  runtime_options, output_options)


def main():
    parser = argparse.ArgumentParser(description="An EPyGrAM tool for asking what's inside a resource.",
                                     epilog='End of help for: %(prog)s (EPyGrAM v' + epygram.__version__ + ')')

    add_arg_to_parser(parser, files_management['principal_file'])
    add_arg_to_parser(parser, output_options['get_field_details'])
    add_arg_to_parser(parser, fields_management['GRIB_what_mode'])
    add_arg_to_parser(parser, fields_management['GRIB_sort'])
    add_arg_to_parser(parser, fields_management['sort_fields'])
    add_arg_to_parser(parser, output_options['stdout'])
    add_arg_to_parser(parser, runtime_options['verbose'])

    args = parser.parse_args()

    epygram.init_env()
    epylog.setLevel('WARNING')
    if args.verbose:
        epylog.setLevel('INFO')

    resource = epygram.formats.resource(args.filename, openmode='r')
    if resource.format not in ('GRIB', 'FA', 'DDHLFA', 'LFA', 'LFI', 'TIFFMF'):
        epylog.warning(" ".join(["tool NOT TESTED with format",
                                 resource.format, "!"]))
    if args.stdout:
        out = sys.stdout
    else:
        out = open(resource.container.abspath + '.info', 'w')
    resource.what(out,
                  details=args.details,
                  sortfields=args.sortfields,
                  mode=args.mode)

if __name__ == '__main__':
    main()

