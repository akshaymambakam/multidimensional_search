# -*- coding: utf-8 -*-
# Copyright (c) 2018 J.I. Requeno et al
#
# This file is part of the ParetoLib software tool and governed by the
# 'GNU License v3'. Please see the LICENSE file that should have been
# included as part of this software.
"""CommontSearch.

This module instantiate the abstract interface Oracle.
The OraclePoint defines the boundary between the upper and lower
closures based on a discrete cloud of points. The cloud of points is
saved in a NDTree [1], a data structure that is optimised for storing
a Pareto front by removing redundant non-dominating points from the
surface. A point x that dominates every member of the Pareto front
belongs to the lower part of the monotone partition, while a point x
that is dominated by any element of the Pareto front will fall in the
upper part.

[1] Andrzej Jaszkiewicz and Thibaut Lust. ND-Tree-based update: a
fast algorithm for the dynamic non-dominance problem. IEEE Trans-
actions on Evolutionary Computation, 2018.
"""

from ParetoLib.Geometry.Point import add, subtract, less_equal, div
from ParetoLib.Geometry.Segment import Segment

# EPS = sys.float_info.epsilon
# DELTA = sys.float_info.epsilon
# STEPS = 100

EPS = 1e-5
DELTA = 1e-5
STEPS = float('inf')


def binary_search(x,
                  member,
                  error):
    # type: (Segment, callable, tuple) -> (Segment, int)
    i = 0
    y = x

    if member(y.low):
        # All the cube belongs to B1
        y.low = x.low
        y.high = x.low
    elif not member(y.high):
        # All the cube belongs to B0
        y.low = x.high
        y.high = x.high
    else:
        # We don't know. We search for a point in the diagonal
        # dist = subtract(y.high, y.low)
        dist = y.norm()
        # while not less_equal(dist, error):
        while dist > error[0]:
            i += 1
            # yval = div(add(y.low, y.high), 2.0)
            yval = y.center()
            # We need a oracle() for guiding the search
            if member(yval):
                y.high = yval
            else:
                y.low = yval
            # dist = subtract(y.high, y.low)
            dist = y.norm()
    return y, i

def intersection_empty(x, member1, member2):
    if (not member1(x.high)) or (not member2(x.low)):
        # The cube doesn't contain an intersection.
        return True
    else:
        return False

def intersection_binary_search(x,
                  member1, member2,
                  error):
    # type: (Segment, callable, callable, tuple) -> (Segment, int)
    # member1 is the function whose truth value increases with x.
    # member2 is the function whose truth value decreases with x.
    i = 0
    y = x
    intersect_indicator = -1
    if member1(y.low) and member2(y.high):
        # All the cube belongs to B1
        intersect_indicator = 2
    elif (not member1(y.high)) or (not member2(y.low)):
        # All the cube belongs to B0
        y.low = x.high
        y.high = x.high
        intersect_indicator = -3
    else:
        # We don't know. We search for a point in the diagonal
        # dist = subtract(y.high, y.low)
        dist = y.norm()
        # while not less_equal(dist, error):
        while dist > error[0]:
            i += 1
            # yval = div(add(y.low, y.high), 2.0)
            yval = y.center()
            # We need a oracle() for guiding the search
            result1 = member1(yval)
            result2 = member2(yval)
            if result1 and result2:
                # assign
                y.low  = yval
                y.high = yval
                intersect_indicator = 1
                break
            elif not (result1 or result2):
                # assign
                y.low  = yval
                y.high = yval
                intersect_indicator = -2
                break
            elif result1 and (not result2):
                y.high = yval
            else: # (not result1) and (result2)
                y.low  = yval
            # dist = subtract(y.high, y.low)
            dist = y.norm()
    return y, intersect_indicator, i

def discrete_binary_search(x,
                  member,
                  error):
    # type: (Segment, callable, tuple) -> (Segment, int)
    i = 0
    y = x
    search_ended = 0
    if member(y.low):
        # All the cube belongs to B1
        y.low = x.low
        y.high = x.low
    elif not member(y.high):
        # All the cube belongs to B0
        y.low = x.high
        y.high = x.high
    else:
        # We don't know. We search for a point in the diagonal
        # dist = subtract(y.high, y.low)
        dist = y.norm()
        # while not less_equal(dist, error):
        while dist > 1.42:
            i += 1
            # yval = div(add(y.low, y.high), 2.0)
            yval = y.center_round()
            # We need a oracle() for guiding the search
            if member(yval):
                y.high = yval
            else:
                y.low = yval
            # dist = subtract(y.high, y.low)
            dist = y.norm()
        search_ended = 1
    if search_ended:
        y.low = y.high
    return y, i