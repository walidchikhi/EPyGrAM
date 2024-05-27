#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Météo France (2014-)
# This software is governed by the CeCILL-C license under French law.
# http://www.cecill.info
"""
Contains the class that handle a Horizontal 2D field.
"""

from __future__ import print_function, absolute_import, unicode_literals, division

import numpy

import footprints

from epygram import epygramError
from epygram.geometries import H2DGeometry
from . import gimme_one_point
from .D3Field import D3Field
from .PointField import PointField

epylog = footprints.loggers.getLogger(__name__)


class H2DField(D3Field):
    """
    Horizontal 2-Dimensions field class.
    A field is defined by its identifier 'fid',
    its data, its geometry (gridpoint and optionally spectral),
    and its validity.

    The natural being of a field is gridpoint, so that:
    a field always has a gridpoint geometry, but it has a spectral geometry only
    in case it is spectral.
    """

    _collector = ('field',)
    _footprint = dict(
        attr=dict(
            structure=dict(
                values=set(['H2D'])),
            geometry=dict(
                type=H2DGeometry),
        )
    )

    def _check_operands(self, other):
        """
        Internal method to check compatibility of terms in operations on fields.
        """
        if isinstance(other, self.__class__):
            if self.spectral != other.spectral:
                raise epygramError("cannot operate a spectral field with a" +
                                   " non-spectral field.")
            if self.geometry.rectangular_grid:
                if self.geometry.dimensions['X'] != other.geometry.dimensions['X'] or\
                   self.geometry.dimensions['Y'] != other.geometry.dimensions['Y']:
                    raise epygramError("operations on fields cannot be done if" +
                                       " fields do not share their gridpoint" +
                                       " dimensions.")
            else:
                if self.geometry.dimensions != other.geometry.dimensions:
                    raise epygramError("operations on fields cannot be done if" +
                                       " fields do not share their gridpoint" +
                                       " dimensions.")
            if self.spectral_geometry != other.spectral_geometry:
                raise epygramError("operations on fields cannot be done if" +
                                   " fields do not share their spectral" +
                                   " geometry.")
        else:
            super(D3Field, self)._check_operands(other)

##############
# ABOUT DATA #
##############
    def getlevel(self, level=None, k=None):
        """Returns self. Useless but for compatibility reasons."""
        if k is None and level is None:
            raise epygramError("You must give k or level.")
        if k is not None and level is not None:
            raise epygramError("You cannot give, at the same time, k and level")
        if level is not None:
            if level not in self.geometry.vcoordinate.levels:
                raise epygramError("The requested level does not exist.")
        return self

    def extract_point(self, lon, lat,
                      interpolation='nearest',
                      external_distance=None):
        """
        Extract a point as a PointField.

        Cf. getvalue_ll() doc for other arguments.
        """
        value = [self.getvalue_ll(lon, lat, validity=self.validity[i],
                                  interpolation=interpolation,
                                  external_distance=external_distance)
                 for i in range(len(self.validity))]
        pt = gimme_one_point(lon, lat,
                             field_args={'validity':self.validity.deepcopy(),
                                         'fid':self.fid},
                             geometry_args={'vcoordinate':self.geometry.vcoordinate},
                             vertical_geometry_args=None)
        pt.setdata(value)
        return pt

    def extract_contour(self,level):
        """
        Return the intersection of the plan **level** and the H2Dfield: the result is a list of (lon,lat) point list.
        The length of the first list is the number of disjoint lines.
        This function relies on the contourpy library which is expected to be installed by the user.
        """
        try:
            from contourpy import contour_generator
        except ModuleNotFoundError:
            raise ModuleNotFoundError('To use *extract_contour* method, you must have `contourpy` installed: ' +
                                      'pip3 install --user contourpy')
        cont_gen=contour_generator(z=self.getdata()) 
        contour=cont_gen.lines(level)
        lines=[]
        for ijlist in contour:
            line=[]
            for i,j in ijlist:
                lon,lat=self.geometry.ij2ll(i,j)
                line.append((lon,lat))
            lines.append(line)
        return lines

###################
# PRE-APPLICATIVE #
###################
# (but useful and rather standard) !
# [so that, subject to continuation through updated versions,
#  including suggestions/developments by users...]

    def morph_with_points(self, points,
                          alpha=1.,
                          morphing='nearest',
                          increment=False,
                          **kwargs):
        """
        Perturb the field values with the values of a set of points.

        :param points: a list/fieldset of PointField.
        :param alpha: is the blending value, ranging from 0. to 1.:
          e.g. with 'nearest' morphing, the final value of the point is
          alpha*point.value + (1-alpha)*original_field.value
        :param morphing: is the way the point modify the field:\n
          - 'nearest': only the nearest point is modified
          - 'exp_decay': modifies the surrounding points with an isotrop
            exponential decay weighting
          - 'gaussian': modifies the surrounding points with an isotrop
            gaussian weighting. Its standard deviation *sigma* must then
            be passed as argument, in meters. Weightingassumed to be 0. from
            3*sigma.
        :param increment: if True, the final value of the point is
          original_field.value + point.value
        """
        assert isinstance(points, list)
        assert all([isinstance(p, PointField) for p in points])
        if len(self.validity) != 1:
            raise NotImplementedError('morph field with a time dimension.')

        for p in points:
            if morphing == 'nearest':
                lon = p.geometry.grid['longitudes'][0]
                lat = p.geometry.grid['latitudes'][0]
                i, j = self.geometry.ll2ij(lon, lat)
                i = int(i)
                j = int(j)
                if increment:
                    self._data[:, :, j, i] = self._data[:, :, j, i] + p.getdata()
                else:
                    self._data[:, :, j, i] = alpha * p.getdata() + (1. - alpha) * self._data[:, :, j, i]
            elif morphing == 'gaussian':
                sigma = kwargs['sigma']
                lon = p.geometry.grid['longitudes'][0]
                lat = p.geometry.grid['latitudes'][0]
                zero_radius = 3. * sigma
                selection_points_ij = self.geometry.nearest_points(lon, lat, request={'radius':zero_radius, 'shape':'circle'})
                selection_points_ll = self.geometry.ij2ll([sp[0] for sp in selection_points_ij], [sp[1] for sp in selection_points_ij])
                selection_points_ll = [(selection_points_ll[0][k], selection_points_ll[1][k]) for k in range(len(selection_points_ll[0]))]
                for sp in selection_points_ll:
                    distance = self.geometry.distance((lon, lat), sp)
                    if distance <= zero_radius:
                        (i, j) = selection_points_ij[selection_points_ll.index(sp)]
                        if increment:
                            local_alpha = numpy.exp(-distance ** 2. / (2. * sigma ** 2))
                            self._data[:, :, j, i] = self._data[:, :, j, i] + local_alpha * p.getdata()
                        else:
                            local_alpha = alpha * numpy.exp(-distance ** 2. / (2. * sigma ** 2))
                            self._data[:, :, j, i] = local_alpha * p.getdata() + (1. - local_alpha) * self._data[:, :, j, i]
            else:
                raise NotImplementedError("morphing: " + morphing + " :not yet.")
