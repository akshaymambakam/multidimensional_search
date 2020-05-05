# -*- coding: utf-8 -*-
# Copyright (c) 2018 J.I. Requeno et al
#
# This file is part of the ParetoLib software tool and governed by the
# 'GNU License v3'. Please see the LICENSE file that should have been
# included as part of this software.
"""SeqSearch.

This module implements the sequential version of the learning
algorithms described in [1] for searching the Pareto front.

[1] Learning Monotone Partitions of Partially-Ordered Domains,
Nicolas Basset, Oded Maler, J.I Requeno, in
doc/article.pdf.
"""

import os
import time
import tempfile
import itertools
# import resource

from sortedcontainers import SortedListWithKey, SortedSet

import ParetoLib.Search as RootSearch

from ParetoLib.Search.CommonSearch import EPS, DELTA, STEPS, determine_intersection, binary_search, intersection_empty, intersection_empty_constrained, intersection_binary_search, intersection_expansion_search, discrete_binary_search
from ParetoLib.Search.ResultSet import ResultSet

from ParetoLib.Oracle.Oracle import Oracle
from ParetoLib.Geometry.Rectangle import Rectangle, interirect, irect, idwc, iuwc, comp, incomp, incomp_segment
from ParetoLib.Geometry.Rectangle import incomp_segmentpos, incomp_segmentNegRemoveDown, incomp_segmentNegRemoveUp
from ParetoLib.Geometry.Lattice import Lattice


# Multidimensional search
# The search returns a set of Rectangles in Yup, Ylow and Border
def multidim_search(xspace,
                    oracle,
                    epsilon=EPS,
                    delta=DELTA,
                    max_step=STEPS,
                    blocking=False,
                    sleep=0.0,
                    opt_level=2,
                    logging=True):
    # type: (Rectangle, Oracle, float, float, int, bool, float, int, bool) -> ResultSet
    md_search = [multidim_search_opt_0,
                 multidim_search_opt_1,
                 multidim_search_opt_2,
                 multidim_search_opt_3]

    RootSearch.logger.info('Starting multidimensional search')
    start = time.time()
    rs = md_search[opt_level](xspace,
                              oracle,
                              epsilon=epsilon,
                              delta=delta,
                              max_step=max_step,
                              blocking=blocking,
                              sleep=sleep,
                              logging=logging)
    end = time.time()
    time0 = end - start
    RootSearch.logger.info('Time multidim search: ' + str(time0))
    print 'Time multidim search (pareto front): ' + str(time0)

    return rs

# Multidimensional search
# The search returns a rectangle containing a solution and a Border
def multidim_intersection_search(xspace, list_constraints,
                    oracle1,oracle2,
                    epsilon=EPS,
                    delta=DELTA,
                    max_step=STEPS,
                    blocking=False,
                    sleep=0.0,
                    opt_level=0,
                    logging=True):
    # type: (Rectangle, Oracle, float, float, int, bool, float, int, bool) -> ParResultSet
    md_search = [multidim_intersection_search_opt_0, multidim_intersection_search_opt_1, multidim_intersection_search_opt_2]
    RootSearch.logger.info('Starting multidimensional search')
    start = time.time()
    intersect_result = md_search[opt_level](xspace, list_constraints,
                              oracle1, oracle2,
                              epsilon=epsilon,
                              delta=delta,
                              max_step=max_step,
                              blocking=blocking,
                              sleep=sleep,
                              logging=logging)
    end = time.time()
    time0 = end - start
    RootSearch.logger.info('Time multidim search: ' + str(time0))
    print 'Time multidim search (intersection): ' + str(time0)

    return intersect_result

##############################
# opt_3 = Equivalent to opt_2 but using a Lattice for detecting dominated cubes in the boundary
# opt_2 = Equivalent to opt_1 but involving less computations
# opt_1 = Maximum optimisation
# opt_0 = No optimisation
##############################

########################################################################################################################
def multidim_search_opt_3(xspace,
                          oracle,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle, float, float, float, bool, float, bool) -> ResultSet

    # xspace is a particular case of maximal rectangle
    # xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    # border = SortedListWithKey(key=Rectangle.volume)
    border = SortedSet([], key=Rectangle.volume)
    border.add(xspace)

    lattice_border_ylow = Lattice(dim=xspace.dim(), key=lambda x: x.min_corner)
    lattice_border_yup = Lattice(dim=xspace.dim(), key=lambda x: x.max_corner)

    lattice_border_ylow.add(xspace)
    lattice_border_yup.add(xspace)

    ylow = []
    yup = []

    # x_minimal = points from 'x' that are strictly incomparable (Pareto optimal)
    ylow_minimal = []
    yup_minimal = []

    # oracle function
    f = oracle.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info(
        'Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder, BinSearch, nBorder dominated by Ylow, nBorder dominated by Yup')
    while (vol_border >= delta) and (step <= max_step) and (len(border) > 0):
        step = step + 1
        # if RootSearch.logger.isEnabledFor(RootSearch.logger.DEBUG):
        #    RootSearch.logger.debug('border: {0}'.format(border))
        # l.sort(key=Rectangle.volume)

        xrectangle = border.pop()

        lattice_border_ylow.remove(xrectangle)
        lattice_border_yup.remove(xrectangle)

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        # y, segment
        # y = search(xrectangle.diag(), f, epsilon)
        y, steps_binsearch = binary_search(xrectangle.diag(), f, error)
        RootSearch.logger.debug('y: {0}'.format(y))
        # discovered_segments.append(y)

        # b0 = Rectangle(xrectangle.min_corner, y.low)
        # b1 = Rectangle(y.high, xrectangle.max_corner)
        #
        # ylow.append(b0)
        # yup.append(b1)
        #
        # vol_ylow += b0.volume()
        # vol_yup += b1.volume()

        ################################
        # Every Border rectangle that dominates B0 is included in Ylow
        b0_extended = Rectangle(xspace.min_corner, y.low)
        # border_overlapping_b0 = [rect for rect in border if rect.overlaps(b0_extended)]
        # border_overlapping_b0 = [rect for rect in border_overlapping_b0 if rect.overlaps(b0_extended)]
        ylow_rectangle = Rectangle(y.low, y.low)
        border_overlapping_b0 = lattice_border_ylow.less_equal(ylow_rectangle)
        # border_intersecting_b0 = [b0_extended.intersection(rect) for rect in border_overlapping_b0]

        ## border_nondominatedby_b0 = [rect - b0_extended for rect in border_overlapping_b0]
        # border_nondominatedby_b0 = []
        # for rect in border_overlapping_b0:
        #     border_nondominatedby_b0 += list(rect - b0_extended)

        list_idwc = (idwc(b0_extended, rect) for rect in border_overlapping_b0)
        border_nondominatedby_b0 = set(itertools.chain.from_iterable(list_idwc))
        # border_nondominatedby_b0 = Rectangle.fusion_rectangles(border_nondominatedby_b0)

        # if 'rect' is completely dominated by b0_extended (i.e., rect is strictly inside b0_extended), then
        # set(rect - b0_extended) == {rect}
        # Therefore, 'rect' must be removed from 'non dominated' borders

        border |= border_nondominatedby_b0
        border -= border_overlapping_b0

        lattice_border_ylow.add_list(border_nondominatedby_b0)
        lattice_border_ylow.remove_list(border_overlapping_b0)

        lattice_border_yup.add_list(border_nondominatedby_b0)
        lattice_border_yup.remove_list(border_overlapping_b0)

        # Every Border rectangle that is dominated by B1 is included in Yup
        b1_extended = Rectangle(y.high, xspace.max_corner)
        # border_overlapping_b1 = [rect for rect in border if rect.overlaps(b1_extended)]
        # border_overlapping_b1 = [rect for rect in border_overlapping_b1 if rect.overlaps(b1_extended)]
        yup_rectangle = Rectangle(y.high, y.high)
        border_overlapping_b1 = lattice_border_yup.greater_equal(yup_rectangle)
        # border_intersecting_b1 = [b1_extended.intersection(rect) for rect in border_overlapping_b1]

        ## border_nondominatedby_b1 = [rect - b1_extended for rect in border_overlapping_b1]
        # border_nondominatedby_b1 = []
        # for rect in border_overlapping_b1:
        #     border_nondominatedby_b1 += list(rect - b1_extended)

        list_iuwc = (iuwc(b1_extended, rect) for rect in border_overlapping_b1)
        border_nondominatedby_b1 = set(itertools.chain.from_iterable(list_iuwc))
        # border_nondominatedby_b1 = Rectangle.fusion_rectangles(border_nondominatedby_b1)

        # if 'rect' is completely dominated by b1_extended (i.e., rect is strictly inside b1_extended), then
        # set(rect - b1_extended) == {rect}
        # Therefore, 'rect' must be removed from 'non dominated' borders

        border |= border_nondominatedby_b1
        border -= border_overlapping_b1

        lattice_border_ylow.add_list(border_nondominatedby_b1)
        lattice_border_ylow.remove_list(border_overlapping_b1)

        lattice_border_yup.add_list(border_nondominatedby_b1)
        lattice_border_yup.remove_list(border_overlapping_b1)

        db0 = Rectangle.difference_rectangles(b0_extended, ylow_minimal)
        db1 = Rectangle.difference_rectangles(b1_extended, yup_minimal)

        vol_db0 = sum(b0.volume() for b0 in db0)
        vol_db1 = sum(b1.volume() for b1 in db1)

        # rs = ResultSet([], border_intersecting_b0 + [b0], border_intersecting_b1 + [b1], Rectangle())
        # vol_db0 = rs.volume_ylow() - rs.overlapping_volume_ylow()
        # vol_db1 = rs.volume_yup() - rs.overlapping_volume_yup()

        vol_ylow += vol_db0
        vol_yup += vol_db1

        ylow.extend(db0)
        yup.extend(db1)

        ylow_minimal.append(b0_extended)
        yup_minimal.append(b1_extended)

        RootSearch.logger.debug('b0: {0}'.format(db0))
        RootSearch.logger.debug('b1: {0}'.format(db1))

        RootSearch.logger.debug('ylow: {0}'.format(ylow))
        RootSearch.logger.debug('yup: {0}'.format(yup))

        ################################
        # Every rectangle in 'i' is incomparable for current B0 and for all B0 included in Ylow
        # Every rectangle in 'i' is incomparable for current B1 and for all B1 included in Yup
        ################################

        yrectangle = Rectangle(y.low, y.high)
        i = irect(incomparable, yrectangle, xrectangle)
        # i = pirect(incomparable, yrectangle, xrectangle)
        # l.extend(i)

        border |= i
        RootSearch.logger.debug('irect: {0}'.format(i))

        lattice_border_ylow.add_list(i)
        lattice_border_yup.add_list(i)

        # Remove boxes in the boundary with volume 0
        boxes_null_vol = border[:border.bisect_key_left(0.0)]
        border -= boxes_null_vol
        lattice_border_ylow.remove_list(boxes_null_vol)
        lattice_border_yup.remove_list(boxes_null_vol)

        vol_border = vol_total - vol_yup - vol_ylow

        RootSearch.logger.info('{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, {10}'
                               .format(step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border),
                                       steps_binsearch,
                                       len(border_overlapping_b0), len(border_overlapping_b1)))
        if sleep > 0.0:
            rs = ResultSet(border, ylow, yup, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, ylow, yup, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    return ResultSet(border, ylow, yup, xspace)


def multidim_search_opt_2(xspace,
                          oracle,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle, float, float, float, bool, float, bool) -> ResultSet

    # xspace is a particular case of maximal rectangle
    # xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    # border = SortedListWithKey(key=Rectangle.volume)
    border = SortedSet([], key=Rectangle.volume)
    border.add(xspace)

    ylow = []
    yup = []

    # x_minimal = points from 'x' that are strictly incomparable (Pareto optimal)
    ylow_minimal = []
    yup_minimal = []

    # oracle function
    f = oracle.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info(
        'Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder, BinSearch, nBorder dominated by Ylow, nBorder dominated by Yup')
    while (vol_border >= delta) and (step <= max_step) and (len(border) > 0):
        step = step + 1
        # if RootSearch.logger.isEnabledFor(RootSearch.logger.DEBUG):
        #    RootSearch.logger.debug('border: {0}'.format(border))
        # l.sort(key=Rectangle.volume)

        xrectangle = border.pop()

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        # y, segment
        # y = search(xrectangle.diag(), f, epsilon)
        y, steps_binsearch = discrete_binary_search(xrectangle.diag(), f, error)
        RootSearch.logger.debug('y: {0}'.format(y))
        # discovered_segments.append(y)

        # b0 = Rectangle(xrectangle.min_corner, y.low)
        # b1 = Rectangle(y.high, xrectangle.max_corner)
        #
        # ylow.append(b0)
        # yup.append(b1)
        #
        # vol_ylow += b0.volume()
        # vol_yup += b1.volume()

        ################################
        # Every Border rectangle that dominates B0 is included in Ylow
        b0_extended = Rectangle(xspace.min_corner, y.low)
        border_overlapping_b0 = [rect for rect in border if rect.overlaps(b0_extended)]
        # border_intersecting_b0 = [b0_extended.intersection(rect) for rect in border_overlapping_b0]

        ## border_nondominatedby_b0 = [rect - b0_extended for rect in border_overlapping_b0]
        # border_nondominatedby_b0 = []
        # for rect in border_overlapping_b0:
        #     border_nondominatedby_b0 += list(rect - b0_extended)

        list_idwc = (idwc(b0_extended, rect) for rect in border_overlapping_b0)
        border_nondominatedby_b0 = set(itertools.chain.from_iterable(list_idwc))
        # border_nondominatedby_b0 = Rectangle.fusion_rectangles(border_nondominatedby_b0)

        # if 'rect' is completely dominated by b0_extended (i.e., rect is strictly inside b0_extended), then
        # set(rect - b0_extended) == {rect}
        # Therefore, 'rect' must be removed from 'non dominated' borders

        border |= border_nondominatedby_b0
        border -= border_overlapping_b0

        # Every Border rectangle that is dominated by B1 is included in Yup
        b1_extended = Rectangle(y.high, xspace.max_corner)
        border_overlapping_b1 = [rect for rect in border if rect.overlaps(b1_extended)]
        # border_intersecting_b1 = [b1_extended.intersection(rect) for rect in border_overlapping_b1]

        ## border_nondominatedby_b1 = [rect - b1_extended for rect in border_overlapping_b1]
        # border_nondominatedby_b1 = []
        # for rect in border_overlapping_b1:
        #     border_nondominatedby_b1 += list(rect - b1_extended)

        list_iuwc = (iuwc(b1_extended, rect) for rect in border_overlapping_b1)
        border_nondominatedby_b1 = set(itertools.chain.from_iterable(list_iuwc))
        # border_nondominatedby_b1 = Rectangle.fusion_rectangles(border_nondominatedby_b1)

        # if 'rect' is completely dominated by b1_extended (i.e., rect is strictly inside b1_extended), then
        # set(rect - b1_extended) == {rect}
        # Therefore, 'rect' must be removed from 'non dominated' borders

        border |= border_nondominatedby_b1
        border -= border_overlapping_b1

        db0 = Rectangle.difference_rectangles(b0_extended, ylow_minimal)
        db1 = Rectangle.difference_rectangles(b1_extended, yup_minimal)

        vol_db0 = sum(b0.volume() for b0 in db0)
        vol_db1 = sum(b1.volume() for b1 in db1)

        # rs = ResultSet([], border_intersecting_b0 + [b0], border_intersecting_b1 + [b1], Rectangle())
        # vol_db0 = rs.volume_ylow() - rs.overlapping_volume_ylow()
        # vol_db1 = rs.volume_yup() - rs.overlapping_volume_yup()

        vol_ylow += vol_db0
        vol_yup += vol_db1

        ylow.extend(db0)
        yup.extend(db1)

        ylow_minimal.append(b0_extended)
        yup_minimal.append(b1_extended)

        RootSearch.logger.debug('b0: {0}'.format(db0))
        RootSearch.logger.debug('b1: {0}'.format(db1))

        RootSearch.logger.debug('ylow: {0}'.format(ylow))
        RootSearch.logger.debug('yup: {0}'.format(yup))

        ################################
        # Every rectangle in 'i' is incomparable for current B0 and for all B0 included in Ylow
        # Every rectangle in 'i' is incomparable for current B1 and for all B1 included in Yup
        ################################

        yrectangle = Rectangle(y.low, y.high)
        i = irect(incomparable, yrectangle, xrectangle)
        # i = pirect(incomparable, yrectangle, xrectangle)
        # l.extend(i)

        border |= i
        RootSearch.logger.debug('irect: {0}'.format(i))

        # Remove boxes in the boundary with volume 0
        border -= border[:border.bisect_key_left(0.0)]

        vol_border = vol_total - vol_yup - vol_ylow

        RootSearch.logger.info('{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, {10}'
                               .format(step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border),
                                       steps_binsearch,
                                       len(border_overlapping_b0), len(border_overlapping_b1)))
        if sleep > 0.0:
            rs = ResultSet(border, ylow, yup, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, ylow, yup, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    return ResultSet(border, ylow, yup, xspace)


def multidim_search_opt_1(xspace,
                          oracle,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle, float, float, float, bool, float, bool) -> ResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    # border = SortedListWithKey(key=Rectangle.volume)
    border = SortedSet([], key=Rectangle.volume)
    border.add(xspace)

    ylow = []
    yup = []

    # oracle function
    f = oracle.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info(
        'Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder, BinSearch, nBorder dominated by Ylow, nBorder dominated by Yup')
    while (vol_border >= delta) and (step <= max_step) and (len(border) > 0):
        step = step + 1
        # if RootSearch.logger.isEnabledFor(RootSearch.logger.DEBUG):
        #    RootSearch.logger.debug('border: {0}'.format(border))
        # l.sort(key=Rectangle.volume)

        xrectangle = border.pop()

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        # y, segment
        # y = search(xrectangle.diag(), f, epsilon)
        y, steps_binsearch = binary_search(xrectangle.diag(), f, error)
        RootSearch.logger.debug('y: {0}'.format(y))
        # discovered_segments.append(y)

        b0 = Rectangle(xrectangle.min_corner, y.low)
        b1 = Rectangle(y.high, xrectangle.max_corner)

        ylow.append(b0)
        yup.append(b1)

        vol_ylow += b0.volume()
        vol_yup += b1.volume()

        RootSearch.logger.debug('b0: {0}'.format(b0))
        RootSearch.logger.debug('b1: {0}'.format(b1))

        RootSearch.logger.debug('ylow: {0}'.format(ylow))
        RootSearch.logger.debug('yup: {0}'.format(yup))

        ################################
        # Every Border rectangle that dominates B0 is included in Ylow
        # Every Border rectangle that is dominated by B1 is included in Yup
        b0_extended = Rectangle(xspace.min_corner, y.low)
        b1_extended = Rectangle(y.high, xspace.max_corner)

        # Every cube in the boundary overlaps another cube in the boundary
        # When cubes from the boundary are moved to ylow or yup, they may still have a complementary cube
        # remaining in the boundary with a non-empty intersection.
        border_overlapping_ylow = [r for r in ylow if r.overlaps(b0_extended)]
        border_overlapping_yup = [r for r in yup if r.overlaps(b1_extended)]

        border_overlapping_b0 = [rect for rect in border if rect.overlaps(b0_extended)]
        # Warning: Be aware of the overlapping areas of the cubes in the border.
        # If we calculate the intersection of b0_extended with all the cubes in the frontier, and two cubes
        # 'a' and 'b' partially overlaps, then the volume of this overlapping portion will be counted twice
        # border_dominatedby_b0 = [rect.intersection(b0_extended) for rect in border_overlapping_b0]
        # Solution: Project the 'shadow' of the cubes in the border over b0_extended.
        border_dominatedby_b0_shadow = Rectangle.difference_rectangles(b0_extended, border_overlapping_b0)

        # The negative of this image returns a set of cubes in the boundary without overlapping.
        # border_dominatedby_b0 will be appended to ylow.
        # Remove the portion of the negative that overlaps any cube that is already appended to ylow
        border_dominatedby_b0 = Rectangle.difference_rectangles(b0_extended,
                                                                border_dominatedby_b0_shadow + border_overlapping_ylow)

        # border_nondominatedby_b0 = [rect - b0_extended for rect in border_overlapping_b0]

        border_nondominatedby_b0 = []
        for rect in border_overlapping_b0:
            border_nondominatedby_b0 += list(rect - b0_extended)

        # border_nondominatedby_b0 = set()
        # for rect in border_overlapping_b0:
        #    border_nondominatedby_b0 |= set(rect - b0_extended)
        # border_nondominatedby_b0 -= set(border_overlapping_b0)

        # if 'rect' is completely dominated by b0_extended (i.e., rect is strictly inside b0_extended), then
        # set(rect - b0_extended) == {rect}
        # Therefore, 'rect' must be removed from 'non dominated' borders

        # border -= border_overlapping_b0
        border |= border_nondominatedby_b0
        border -= border_overlapping_b0

        border_overlapping_b1 = [rect for rect in border if rect.overlaps(b1_extended)]
        # Warning: Be aware of the overlapping areas of the cubes in the border.
        # If we calculate the intersection of b1_extended with all the cubes in the frontier, and two cubes
        # 'a' and 'b' partially overlaps, then the volume of this overlapping portion will be considered twice
        # border_dominatedby_b1 = [rect.intersection(b1_extended) for rect in border_overlapping_b1]
        # Solution: Project the 'shadow' of the cubes in the border over b1_extended.
        border_dominatedby_b1_shadow = Rectangle.difference_rectangles(b1_extended, border_overlapping_b1)

        # The negative of this image returns a set of cubes in the boundary without overlapping.
        # border_dominatedby_b1 will be appended to yup.
        # Remove the portion of the negative that overlaps any cube that is already appended to yup
        border_dominatedby_b1 = Rectangle.difference_rectangles(b1_extended,
                                                                border_dominatedby_b1_shadow + border_overlapping_yup)

        # border_nondominatedby_b1 = [rect - b1_extended for rect in border_overlapping_b1]

        border_nondominatedby_b1 = []
        for rect in border_overlapping_b1:
            border_nondominatedby_b1 += list(rect - b1_extended)

        # border_nondominatedby_b1 = set()
        # for rect in border_overlapping_b1:
        #    border_nondominatedby_b1 |= set(rect - b1_extended)
        # border_nondominatedby_b1 -= set(border_overlapping_b1)

        # if 'rect' is completely dominated by b1_extended (i.e., rect is strictly inside b1_extended), then
        # set(rect - b1_extended) == {rect}
        # Therefore, 'rect' must be removed from 'non dominated' borders

        # border -= border_overlapping_b1
        border |= border_nondominatedby_b1
        border -= border_overlapping_b1

        ylow.extend(border_dominatedby_b0)
        yup.extend(border_dominatedby_b1)

        vol_ylow += sum(b0.volume() for b0 in border_dominatedby_b0)
        vol_yup += sum(b1.volume() for b1 in border_dominatedby_b1)

        ################################
        # Every rectangle in 'i' is incomparable for current B0 and for all B0 included in Ylow
        # Every rectangle in 'i' is incomparable for current B1 and for all B1 included in Yup
        ################################

        yrectangle = Rectangle(y.low, y.high)
        i = irect(incomparable, yrectangle, xrectangle)
        # i = pirect(incomparable, yrectangle, xrectangle)
        # l.extend(i)

        border |= i
        RootSearch.logger.debug('irect: {0}'.format(i))

        # Remove boxes in the boundary with volume 0
        border -= border[:border.bisect_key_left(0.0)]

        vol_border = vol_total - vol_yup - vol_ylow

        RootSearch.logger.info('{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, {10}'
                               .format(step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border),
                                       steps_binsearch,
                                       len(border_overlapping_b0), len(border_overlapping_b1)))
        if sleep > 0.0:
            rs = ResultSet(border, ylow, yup, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, ylow, yup, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    return ResultSet(border, ylow, yup, xspace)


# Opt_inf is not applicable: it does not improve the convergence of opt_0 because it cannot preemptively remove cubes.
# Cubes from the boundary are partially dominated by Pareto points in Ylow/Ylup, while opt_inf searches for
# cubes that are fully dominated.
def multidim_search_opt_inf(xspace,
                          oracle,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle, float, float, float, bool, float, bool) -> ResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    border = SortedListWithKey([], key=Rectangle.volume)
    # border = SortedSet(key=Rectangle.volume)
    border.add(xspace)

    ylow = []
    yup = []

    # oracle function
    f = oracle.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder, '
                           'BinSearch, volYlowOpt1, volYlowOpt2, volYupOpt1, volYupOpt2')
    while (vol_border >= delta) and (step <= max_step) and (len(border) > 0):
        step = step + 1
        # if RootSearch.logger.isEnabledFor(RootSearch.logger.DEBUG):
        #    RootSearch.logger.debug('border: {0}'.format(border))
        # l.sort(key=Rectangle.volume)

        xrectangle = border.pop()

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        # y, segment
        # y = search(xrectangle.diag(), f, epsilon)
        y, steps_binsearch = binary_search(xrectangle.diag(), f, error)
        RootSearch.logger.debug('y: {0}'.format(y))

        # b0 = Rectangle(xspace.min_corner, y.low)
        b0 = Rectangle(xrectangle.min_corner, y.low)
        ylow.append(b0)
        vol_ylow += b0.volume()

        RootSearch.logger.debug('b0: {0}'.format(b0))
        RootSearch.logger.debug('ylow: {0}'.format(ylow))

        # b1 = Rectangle(y.high, xspace.max_corner)
        b1 = Rectangle(y.high, xrectangle.max_corner)
        yup.append(b1)
        vol_yup += b1.volume()

        RootSearch.logger.debug('b1: {0}'.format(b1))
        RootSearch.logger.debug('yup: {0}'.format(yup))

        ################################
        # Every Border rectangle that dominates B0 is included in Ylow
        ylow_candidates = [rect for rect in border if rect.dominates_rect(b0)]
        ylow.extend(ylow_candidates)
        vol_ylow_opt_1 = sum(b0.volume() for b0 in ylow_candidates)
        vol_ylow += vol_ylow_opt_1
        for rect in ylow_candidates:
            border.remove(rect)

        # Every Border rectangle that is dominated by B1 is included in Yup
        yup_candidates = [rect for rect in border if rect.is_dominated_by_rect(b1)]
        yup.extend(yup_candidates)
        vol_yup_opt_1 = sum(b1.volume() for b1 in yup_candidates)
        vol_yup += vol_yup_opt_1
        for rect in yup_candidates:
            border.remove(rect)
        ################################

        yrectangle = Rectangle(y.low, y.high)
        i = irect(incomparable, yrectangle, xrectangle)
        # i = pirect(incomparable, yrectangle, xrectangle)
        # l.extend(i)

        ################################
        # Every Incomparable rectangle that dominates B0 is included in Ylow
        ylow_candidates = [inc for inc in i if any(inc.dominates_rect(b0) for b0 in ylow)]
        ylow.extend(ylow_candidates)
        vol_ylow_opt_2 = sum(b0.volume() for b0 in ylow_candidates)
        vol_ylow += vol_ylow_opt_2
        for rect in ylow_candidates:
            i.remove(rect)

        # Every Incomparable rectangle that is dominated by B1 is included in Yup
        yup_candidates = [inc for inc in i if any(inc.is_dominated_by_rect(b1) for b1 in yup)]
        yup.extend(yup_candidates)
        vol_yup_opt_2 = sum(b1.volume() for b1 in yup_candidates)
        vol_yup += vol_yup_opt_2
        for rect in yup_candidates:
            i.remove(rect)
        ################################

        border += i
        RootSearch.logger.debug('irect: {0}'.format(i))

        # Remove boxes in the boundary with volume 0
        # border = border[border.bisect_key_right(0.0):]
        del border[:border.bisect_key_left(0.0)]

        vol_border = vol_total - vol_yup - vol_ylow

        RootSearch.logger.info('{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, {10}, {11}, {12}'
                               .format(step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border),
                                       steps_binsearch,
                                       vol_ylow_opt_1, vol_ylow_opt_2, vol_yup_opt_1, vol_yup_opt_2))
        if sleep > 0.0:
            rs = ResultSet(border, ylow, yup, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, ylow, yup, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    return ResultSet(border, ylow, yup, xspace)


def multidim_search_opt_0(xspace,
                          oracle,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle, float, float, float, bool, float, bool) -> ResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    border = SortedListWithKey(key=Rectangle.volume)
    # border = SortedSet(key=Rectangle.volume)
    border.add(xspace)

    ylow = []
    yup = []

    # oracle function
    f = oracle.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder, BinSearch')
    while (vol_border >= delta) and (step <= max_step) and (len(border) > 0):
        step = step + 1
        # if RootSearch.logger.isEnabledFor(RootSearch.logger.DEBUG):
        #    RootSearch.logger.debug('border: {0}'.format(border))
        # l.sort(key=Rectangle.volume)

        xrectangle = border.pop()

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        # y, segment
        # y = search(xrectangle.diag(), f, epsilon)
        #print 'resource usage before in mb:', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        y, steps_binsearch = binary_search(xrectangle.diag(), f, error)
        #print 'resource usage after in mb:', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        RootSearch.logger.debug('y: {0}'.format(y))

        # b0 = Rectangle(xspace.min_corner, y.low)
        b0 = Rectangle(xrectangle.min_corner, y.low)
        ylow.append(b0)
        vol_ylow += b0.volume()

        RootSearch.logger.debug('b0: {0}'.format(b0))
        RootSearch.logger.debug('ylow: {0}'.format(ylow))

        # b1 = Rectangle(y.high, xspace.max_corner)
        b1 = Rectangle(y.high, xrectangle.max_corner)
        yup.append(b1)
        vol_yup += b1.volume()

        RootSearch.logger.debug('b1: {0}'.format(b1))
        RootSearch.logger.debug('yup: {0}'.format(yup))

        yrectangle = Rectangle(y.low, y.high)
        i = irect(incomparable, yrectangle, xrectangle)
        # i = pirect(incomparable, yrectangle, xrectangle)
        # l.extend(i)

        border += i
        RootSearch.logger.debug('irect: {0}'.format(i))

        # Remove boxes in the boundary with volume 0
        # border = border[border.bisect_key_right(0.0):]
        del border[:border.bisect_key_left(0.0)]

        vol_border = vol_total - vol_yup - vol_ylow

        RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}'.format(step, vol_ylow, vol_yup, vol_border, vol_total,
                                                                 len(ylow), len(yup), len(border),
                                                                 steps_binsearch))
        if sleep > 0.0:
            rs = ResultSet(border, ylow, yup, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, ylow, yup, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    print 'For pareto front construction algorithm:'
    print 'remaining volume:', vol_border
    print 'total volume:',     vol_total
    print 'precentage unexplored:', (float(vol_border)/vol_total)*100
    return ResultSet(border, ylow, yup, xspace)

def bound_box_with_constraints(box, list_constraints):
    max_bound = 1
    min_bound = 0
    flag_max = 0
    flag_min = 0
    for constraint in list_constraints:
        coeff_sum = 0.0
        const_sum = 0.0
        for i in range(len(box.min_corner)):
            coeff_sum += constraint[i]*(box.max_corner[i] - box.min_corner[i])
            const_sum -= constraint[i]*(box.min_corner[i])
        const_sum += constraint[-1]
        current_bound = const_sum/coeff_sum
        if(constraint[-1] < 0):
            if(flag_min):
                min_bound = max(min_bound, current_bound)
            else:
                min_bound = current_bound
                flag_min  = 1
        else:
            if(flag_max):
                max_bound = min(max_bound, current_bound)
            else:
                max_bound = current_bound
                flag_max  = 1           
    return min_bound, max_bound

def multidim_intersection_search_opt_0(xspace, list_constraints,
                          oracle1, oracle2,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle1, Oracle2, float, float, float, bool, float, bool) -> ResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    incomparable_segment = incomp_segment(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    border = SortedListWithKey(key=Rectangle.adjustedVolume)
    # border = SortedSet(key=Rectangle.volume)
    border.add(xspace)

    # oracle functions
    f1 = oracle1.membership()
    f2 = oracle2.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_xrest = 0
    vol_border = vol_total
    step = 0

    # intersection.
    intersect_box = []
    intersect_region = []

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder, BinSearch')
    while (vol_border >= vol_total*delta) and (step <= max_step) and (len(border) > 0):
        step = step + 1
        # if RootSearch.logger.isEnabledFor(RootSearch.logger.DEBUG):
        #    RootSearch.logger.debug('border: {0}'.format(border))
        # l.sort(key=Rectangle.volume)

        xrectangle = border.pop()

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        min_bound, max_bound = bound_box_with_constraints(xrectangle, list_constraints)
        flag = 0
        rect_diag = xrectangle.diag()
        if(max_bound < 0 or min_bound > 1 or min_bound > max_bound or min_bound + 0.00001 > max_bound):
            intersect_indicator = -3
            continue
        else:
            if min_bound < 0:
                min_bound = 0
            if max_bound > 1:
                max_bound = 1
            if min_bound > 0 or max_bound < 1:
                min_bound += 0.00001
                max_bound -= 0.00001
                end_min = tuple(i+(j-i)*min_bound for i,j in zip(xrectangle.min_corner, xrectangle.max_corner))
                end_max = tuple(i+(j-i)*max_bound for i,j in zip(xrectangle.min_corner, xrectangle.max_corner))
                mod_rectangle = Rectangle(end_min, end_max)
                rect_diag = mod_rectangle.diag()
                flag = 1
                yIn, yCover, intersect_indicator, steps_binsearch = intersection_expansion_search(rect_diag, f1, f2, error, False)
            else:
                yIn, yCover, intersect_indicator, steps_binsearch = intersection_expansion_search(rect_diag, f1, f2, error, False)
        y = yCover
        RootSearch.logger.debug('y: {0}'.format(y))

        if intersect_indicator >= 1:
            intersect_box = [Rectangle(yIn.low,yIn.high)]
            intersect_region = [xrectangle]
            break
        elif intersect_indicator == -3:
            if flag == 1: # (min_bound > 0 and max_bound < 1):
                yrectangle = Rectangle(rect_diag.low, rect_diag.high)
                i = interirect(incomparable_segment, yrectangle, xrectangle)
                lower_rect = Rectangle(xrectangle.min_corner, yrectangle.max_corner)
                upper_rect = Rectangle(yrectangle.min_corner, xrectangle.max_corner)
                vol_xrest += lower_rect.volume() + upper_rect.volume() - yrectangle.volume()
            else:
                vol_xrest += xrectangle.volume() # Temporary hack. Must purge the implementation of the algo.
                continue
        else:
            # b0 = Rectangle(xspace.min_corner, y.low)
            b0 = Rectangle(xrectangle.min_corner, y.low)
            vol_xrest += b0.volume()

            RootSearch.logger.debug('b0: {0}'.format(b0))

            # b1 = Rectangle(y.high, xspace.max_corner)
            b1 = Rectangle(y.high, xrectangle.max_corner)
            vol_xrest += b1.volume()

            RootSearch.logger.debug('b1: {0}'.format(b1))

            yrectangle = Rectangle(y.low, y.high)
            i = irect(incomparable, yrectangle, xrectangle)
        # i = pirect(incomparable, yrectangle, xrectangle)
        # l.extend(i)
        for rect in i:
            if intersection_empty_constrained(rect.diag(), f1, f2, list_constraints):
                vol_xrest += rect.volume()
            else:
                border.add(rect)
        # border += i
        RootSearch.logger.debug('irect: {0}'.format(i))

        # Remove boxes in the boundary with volume 0
        # border = border[border.bisect_key_right(0.0):]
        del border[:border.bisect_key_left(0.0)]

        vol_border = vol_total - vol_xrest

        RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}'.format(step, vol_border, vol_total,
                                                len(border),
                                                steps_binsearch))
        if sleep > 0.0:
            rs = ResultSet(border, [], intersect_region, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, [], intersect_region, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    print 'For pareto front intersection finding algorithm:'
    print 'remaining volume:', vol_border
    print 'total volume:',     vol_total
    print 'percentage unexplored:', (float(vol_border)/vol_total)*100

    return (intersect_box, border, xspace, intersect_region)

def posNegBoxGen(incompPos, incompNegDown, incompNegUp, yIn, yCover, xrectangle):
    incomp1 = incompPos[2:]
    incompListDown = [incompPos[0]]
    incompListUp   = [incompPos[1]]
    yrectMid = Rectangle(yIn.low, yIn.high)
    i1 = interirect(incomp1, yrectMid, xrectangle)
    i2 = interirect(incompListDown, yrectMid, xrectangle)
    i3 = interirect(incompListUp, yrectMid, xrectangle)
    iDown = []
    iUp   = []
    for rect in i2:
        yRectDown = Rectangle(yCover.low, rect.max_corner)
        iDown += interirect(incompNegDown, yRectDown, rect)
    for rect in i3:
        yRectUp   = Rectangle(yCover.high, rect.max_corner)
        iUp   += interirect(incompNegUp, yRectUp, rect)
    i = iDown + iUp + i1
    return i

def posOverlapBoxGen(incomparable, incomparable_segment, yIn, yCover, xrectangle):
    yRectIn = Rectangle(yIn.low, yIn.high)
    i1 = interirect(incomparable_segment, yRectIn, xrectangle)
    
    yRectDown = Rectangle(yCover.low, yIn.low)
    xRectDown = Rectangle(xrectangle.min_corner, yIn.high)
    i2 = irect(incomparable, yRectDown, xRectDown)

    yRectUp   = Rectangle(yIn.high, yCover.high)
    xRectUp   = Rectangle(yIn.low, xrectangle.max_corner)
    i3 = irect(incomparable, yRectUp, xRectUp)

    i = i1 + i2 + i3

    return i

def multidim_intersection_search_opt_1(xspace, list_constraints,
                          oracle1, oracle2,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle1, Oracle2, float, float, float, bool, float, bool) -> ResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    incompPos = incomp_segmentpos(n)
    incompNegDown = incomp_segmentNegRemoveDown(n)
    incompNegUp   = incomp_segmentNegRemoveUp(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    border = SortedListWithKey(key=Rectangle.adjustedVolume)
    # border = SortedSet(key=Rectangle.volume)
    border.add(xspace)


    # oracle functions
    f1 = oracle1.membership()
    f2 = oracle2.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_xrest = 0
    vol_border = vol_total
    vol_border_old = vol_border + delta*10 # initialization.
    step = 0

    # intersection.
    intersect_box = []
    intersect_region = []

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info('Report\nStep, Border, Total, nBorder, BinSearch')
    while (vol_border >= delta) and (step <= max_step) and (len(border) > 0):
        if step % 20 == 0:
            if (vol_border_old - vol_border < delta):
                bla = 1
                #break
            vol_border_old = vol_border
        step = step + 1

        xrectangle = border.pop()

        currentPrivilege = xrectangle.privilege

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        wantToExpand = False
        yIn, yCover, intersect_indicator, steps_binsearch = intersection_expansion_search(xrectangle.diag(), f1, f2, error, wantToExpand)
        #print 'vol_border:',vol_border,'step:',step,'max_step:',max_step,'len(border):',len(border)
        y = yCover
        RootSearch.logger.debug('y: {0}'.format(y))

        if intersect_indicator == 2:
            intersect_box.append(Rectangle(y.low,y.high))
            vol_xrest += xrectangle.volume()
            RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}'.format(step, vol_border, vol_total,
                                                len(border),
                                                steps_binsearch))
            continue
        elif intersect_indicator == 1:
            posBox = Rectangle(yIn.low, yIn.high)
            negBox1 = Rectangle(xrectangle.min_corner, yCover.low)
            negBox2 = Rectangle(yCover.high, xrectangle.max_corner)
            intersect_box.append(posBox)
            intersect_region.append(xrectangle)
            
            i = posNegBoxGen(incompPos, incompNegDown, incompNegUp, yIn, yCover, xrectangle)

            vol_xrest += posBox.volume() + negBox1.volume() + negBox2.volume()

        elif intersect_indicator == -3:
            vol_xrest += xrectangle.volume()
            RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}'.format(step, vol_border, vol_total,
                                                len(border),
                                                steps_binsearch))
            continue
        else:
            b0 = Rectangle(xrectangle.min_corner, y.low)
            vol_xrest += b0.volume()

            RootSearch.logger.debug('b0: {0}'.format(b0))

            b1 = Rectangle(y.high, xrectangle.max_corner)
            vol_xrest += b1.volume()

            RootSearch.logger.debug('b1: {0}'.format(b1))

            yrectangle = Rectangle(y.low, y.high)
            i = irect(incomparable, yrectangle, xrectangle)

        for rect in i:
            if intersection_empty(rect.diag(), f1, f2):
                vol_xrest += rect.volume()
            else:
                rect.privilege = currentPrivilege + 1
                border.add(rect)

        RootSearch.logger.debug('irect: {0}'.format(i))

        # Remove boxes in the boundary with volume 0
        # border = border[border.bisect_key_right(0.0):]
        del border[:border.bisect_key_left(0.0)]

        vol_border = vol_total - vol_xrest
        if(vol_border < 0):
            exit(0)

        RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}'.format(step, vol_border, vol_total,
                                                len(border),
                                                steps_binsearch))
        if sleep > 0.0:
            rs = ResultSet(border, [], intersect_region, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, [], intersect_region, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    print 'For pareto front intersection exploring algorithm:'
    print 'remaining volume:', vol_border
    print 'total volume:',     vol_total
    print 'percentage unexplored:', (float(vol_border)/vol_total)*100

    return (intersect_box, border, xspace, intersect_region)

def multidim_intersection_search_opt_2(xspace, list_constraints,
                          oracle1, oracle2,
                          epsilon=EPS,
                          delta=DELTA,
                          max_step=STEPS,
                          blocking=False,
                          sleep=0.0,
                          logging=True):
    # type: (Rectangle, Oracle1, Oracle2, float, float, float, bool, float, bool) -> ResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Set of comparable and incomparable rectangles, represented by 'alpha' indices
    comparable = comp(n)
    incomparable = incomp(n)
    incomparable_segment = incomp_segment(n)
    incompPos = incomp_segmentpos(n)
    incompNegDown = incomp_segmentNegRemoveDown(n)
    incompNegUp   = incomp_segmentNegRemoveUp(n)
    # comparable = [zero, one]
    # incomparable = list(set(alpha) - set(comparable))
    # with:
    # zero = (0_1,...,0_n)
    # one = (1_1,...,1_n)

    # List of incomparable rectangles
    # border = [xspace]
    rectSortKey = lambda rect: rect.scaledNormInf(xspace)
    border = SortedListWithKey(key=Rectangle.adjustedVolume)
    # border = SortedSet(key=Rectangle.volume)
    border.add(xspace)


    # oracle functions
    f1 = oracle1.membership()
    f2 = oracle2.membership()

    error = (epsilon,) * n
    vol_total = xspace.volume()
    vol_xrest = 0
    vol_border = vol_total
    vol_boxes = vol_border
    step = 0

    # intersection.
    intersect_box = []
    intersect_region = []

    RootSearch.logger.debug('xspace: {0}'.format(xspace))
    RootSearch.logger.debug('vol_border: {0}'.format(vol_border))
    RootSearch.logger.debug('delta: {0}'.format(delta))
    RootSearch.logger.debug('step: {0}'.format(step))
    RootSearch.logger.debug('incomparable: {0}'.format(incomparable))
    RootSearch.logger.debug('comparable: {0}'.format(comparable))

    # Create temporary directory for storing the result of each step
    tempdir = tempfile.mkdtemp()

    RootSearch.logger.info('Report\nStep, Border, Total, nBorder, BinSearch')
    while (vol_border >=  vol_total*delta) and (step <= max_step) and (len(border) > 0):
        step = step + 1

        xrectangle = border.pop()
        vol_boxes -= xrectangle.volume()

        currentPrivilege = xrectangle.privilege

        RootSearch.logger.debug('xrectangle: {0}'.format(xrectangle))
        RootSearch.logger.debug('xrectangle.volume: {0}'.format(xrectangle.volume()))
        RootSearch.logger.debug('xrectangle.norm: {0}'.format(xrectangle.norm()))

        wantToExpand = True
        yIn, yCover, intersect_indicator, steps_binsearch = intersection_expansion_search(xrectangle.diag(), f1, f2, error, wantToExpand)
        #print 'vol_border:',vol_border,'step:',step,'max_step:',max_step,'len(border):',len(border)
        if(intersect_indicator == -2):
            y = yIn
        else:
            y = yCover
        yrectangle = Rectangle(y.low, y.high)
        RootSearch.logger.debug('y: {0}'.format(y))

        if intersect_indicator == 2:
            intersect_box.append(Rectangle(y.low,y.high))
            vol_xrest += xrectangle.volume()
            vol_border = vol_total - vol_xrest
            RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}'.format(step, vol_border, vol_xrest+vol_boxes,
                                                len(border),
                                                steps_binsearch))
            continue
        elif intersect_indicator == 1:
            '''
            yCover.low = (2,2,2)
            yCover.high = (5,5,5)
            yIn.low = (3,3,3)
            yIn.high = (4,4,4)
            xrectangle = Rectangle((0,0,0),(6,6,6))
            '''
            if (1):
                posBox = Rectangle(yIn.low, yIn.high)
                negBox1 = Rectangle(xrectangle.min_corner, yCover.low)
                negBox2 = Rectangle(yCover.high, xrectangle.max_corner)
                intersect_box.append(posBox)
                intersect_region.append(xrectangle)

                # i = posNegBoxGen(incompPos, incompNegDown, incompNegUp, yIn, yCover, xrectangle)
                i = posOverlapBoxGen(incomparable, incomparable_segment, yIn, yCover, xrectangle)

                vol_xrest += posBox.volume() + negBox1.volume() + negBox2.volume()
                '''
                if (vol_total - vol_xrest) < 0:
                    print 'yIn',yIn
                    print 'yCover', yCover
                    print 'xrectangle', xrectangle
                    print 'posBox', posBox, posBox.volume()
                    print 'negBox1', negBox1, negBox1.volume()
                    print 'negBox2', negBox2, negBox2.volume()
                '''
            else:
                i = irect(incomparable, yrectangle, xrectangle)

                b0 = Rectangle(xrectangle.min_corner, y.low)
                vol_xrest += b0.volume()
                RootSearch.logger.debug('b0: {0}'.format(b0))

                b1 = Rectangle(y.high, xrectangle.max_corner)
                vol_xrest += b1.volume()
                RootSearch.logger.debug('b1: {0}'.format(b1))

        elif intersect_indicator == -2:
            i = interirect(incomparable_segment, yrectangle, xrectangle)
            lower_rect = Rectangle(xrectangle.min_corner, yrectangle.max_corner)
            upper_rect = Rectangle(yrectangle.min_corner, xrectangle.max_corner)
            vol_xrest += lower_rect.volume() + upper_rect.volume() - yrectangle.volume()
        elif intersect_indicator == -3:
            vol_xrest += xrectangle.volume()
            vol_border = vol_total - vol_xrest
            RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}'.format(step, vol_border, vol_boxes+vol_xrest,
                                                len(border),
                                                steps_binsearch))
            continue
        else:
            b0 = Rectangle(xrectangle.min_corner, y.low)
            vol_xrest += b0.volume()
            RootSearch.logger.debug('b0: {0}'.format(b0))

            b1 = Rectangle(y.high, xrectangle.max_corner)
            vol_xrest += b1.volume()
            RootSearch.logger.debug('b1: {0}'.format(b1))

            i = irect(incomparable, yrectangle, xrectangle)

        for rect in i:
            if intersection_empty(rect.diag(), f1, f2):
                vol_xrest += rect.volume()
            else:
                rect.privilege = currentPrivilege + 1
                border.add(rect)
                vol_boxes += rect.volume()

        RootSearch.logger.debug('irect: {0}'.format(i))

        # Remove boxes in the boundary with volume 0
        # border = border[border.bisect_key_right(0.0):]
        del border[:border.bisect_key_left(0.0)]

        vol_border = vol_total - vol_xrest

        RootSearch.logger.info(
            '{0}, {1}, {2}, {3}, {4}'.format(step, vol_border, vol_boxes+vol_xrest,
                                                len(border),
                                                steps_binsearch))
        if sleep > 0.0:
            rs = ResultSet(border, [], intersect_region, xspace)
            if n == 2:
                rs.plot_2D_light(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.plot_3D_light(blocking=blocking, sec=sleep, opacity=0.7)

        if logging:
            rs = ResultSet(border, [], intersect_region, xspace)
            name = os.path.join(tempdir, str(step))
            rs.to_file(name)

    print 'For pareto front intersection exploring algorithm (with negative segments):'
    print 'remaining volume:', vol_border
    print 'total volume:',     vol_total
    print 'percentage unexplored:', (float(vol_border)/vol_total)*100

    return (intersect_box, border, xspace, intersect_region)

'''

# sfsdfsdf
            yCover.low = (2,2,2)
            yCover.high = (5,5,5)
            yIn.low = (3,3,3)
            yIn.high = (4,4,4)
            xrectangle = Rectangle((0,0,0),(6,6,6))
            yrectangle = Rectangle(yIn.low, yIn.high)
            # sdfsdfsfd

            ## sfsdf
            border = SortedListWithKey(key=Rectangle.adjustedVolume)
            # border = SortedSet(key=Rectangle.volume)
            border.add(Rectangle(yIn.low,yIn.high))
            intersect_region = i
            intersection = []
            intersection.append(lower_rect)
            intersection.append(upper_rect)
            xspace = xrectangle
            return (intersection, border, xspace, intersect_region)
            # sfsdfsdf
'''