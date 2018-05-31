import __builtin__
import itertools
from multiprocessing import Manager, Pool, cpu_count
import multiprocessing as mp
import copy

from sortedcontainers import SortedListWithKey

from ParetoLib.Geometry.pRectangle import *
from ParetoLib.Search.CommonSearch import *
from ParetoLib.Search.pResultSet import *

# from ParetoLib.Search import vprint
from . import vprint

def pbin_search_ser(args):
    xrectangle, f, epsilon, n = args
    error = (epsilon,) * n
    y, steps_binsearch = binary_search(xrectangle.diagToSegment(), f, error)
    return y


def pbin_search(args):
    xrectangle, dict_man, epsilon, n = args
    ora = dict_man[mp.current_process().name]
    f = ora.membership()
    error = (epsilon,) * n
    y, steps_binsearch = binary_search(xrectangle.diagToSegment(), f, error)
    return y


def pb0(args):
    # b0 = Rectangle(xspace.min_corner, y.l)
    xrectangle, y = args
    return Rectangle(xrectangle.min_corner, y.l)


def pb1(args):
    # b1 = Rectangle(y.h, xspace.max_corner)
    xrectangle, y = args
    return Rectangle(y.h, xrectangle.max_corner)


def pborder(args):
    # border = irect(incomparable, yrectangle, xrectangle)
    incomparable, y, xrectangle = args
    yrectangle = Rectangle(y.l, y.h)
    return irect(incomparable, yrectangle, xrectangle)

def pborder_dominatedby_bi (args):
    bi_extended, rect = args
    return rect.intersection(bi_extended)


# Multidimensional search
# The search returns a set of Rectangles in Yup, Ylow and Border
def multidim_search(xspace,
                    oracle,
                    epsilon=EPS,
                    delta=DELTA,
                    max_step=STEPS,
                    blocking=False,
                    sleep=0.0,
                    opt_level=2):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet
    md_search = [multidim_search_deep_first_opt_0,
                 multidim_search_deep_first_opt_1,
                 multidim_search_deep_first_opt_2]

    #multidim_search_breadth_first_opt_0
    #multidim_search_breadth_first_opt_1
    #multidim_search_breadth_first_opt_2

    #vprint('Starting multidimensional search')
    start = time.time()
    rs = md_search[opt_level](xspace,
                              oracle,
                              epsilon=epsilon,
                              delta=delta,
                              max_step=max_step,
                              blocking=blocking,
                              sleep=sleep)
    end = time.time()
    time0 = end - start
    #vprint('Time multidim search: ', str(time0))

    return rs

def multidim_search_old(xspace,
                    oracle,
                    epsilon=EPS,
                    delta=DELTA,
                    max_step=STEPS,
                    blocking=False,
                    sleep=0.0):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet
    #vprint('Starting multidimensional search')
    start = time.time()
    # rs = multidim_search_breadth_first_opt_1(xspace,
    rs = multidim_search_deep_first_opt_1(xspace,
                                    oracle,
                                    epsilon=epsilon,
                                    delta=delta,
                                    max_step=max_step,
                                    blocking=blocking,
                                    sleep=sleep)
    end = time.time()
    time0 = end - start
    #vprint('Time multidim search: ', str(time0))

    return rs

##############################
# opt_2 = Maximum optimisation
# opt_1 = Medium optimisation
# opt_0 = No optimisation
##############################

########################################################################################################################
# Multidimensional search prioritizing the analysis of rectangles with highest volume
def multidim_search_deep_first_opt_2(xspace,
                               oracle,
                               epsilon=EPS,
                               delta=DELTA,
                               max_step=STEPS,
                               blocking=False,
                               sleep=0.0):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Alpha in [0,1]^n
    alphaprime = (range(2),) * n
    alpha = itertools.product(*alphaprime)

    # Particular cases of alpha
    # zero = (0_1,...,0_n)    random.uniform(min_corner, max_corner)
    zero = (0,) * n
    # one = (1_1,...,1_n)
    one = (1,) * n

    # Set of comparable and incomparable rectangles
    comparable = [zero, one]
    incomparable = list(set(alpha) - set(comparable))

    # List of incomparable rectangles
    # border = [xspace]
    # border = SortedListWithKey(key=Rectangle.volume)

    border = SortedSet(key=Rectangle.volume)
    border.add(xspace)

    # Upper and lower clausure
    ylow = []
    yup = []

    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0
    remaining_steps = max_step - step

    num_proc = cpu_count()
    p = Pool(num_proc)

    # oracle function
    # f = oracle.membership()

    man = Manager()
    dict_man = man.dict()

    # 'f = oracle.membership()' is not thread safe!
    # Create a copy of 'oracle' for each concurrent process

    # dict_man = {proc: copy.deepcopy(oracle) for proc in mp.active_children()}
    for proc in mp.active_children():
        dict_man[proc.name] = copy.deepcopy(oracle)

    #vprint('xspace: ', xspace)
    #vprint('vol_border: ', vol_border)
    #vprint('delta: ', delta)
    #vprint('step: ', step)
    #vprint('incomparable: ', incomparable)
    #vprint('comparable: ', comparable)

    print('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder')
    while (vol_border >= delta) and (remaining_steps > 0):
        # Divide the list of incomparable rectangles in chunks of 'num_proc' elements.
        # We get the 'num_proc' elements with highest volume.

        chunk = __builtin__.min(num_proc, remaining_steps)
        chunk = __builtin__.min(chunk, len(border))
        # Take the rectangles with highest volume
        slice_border = border[-chunk:]

        # Remove elements of the slice_border from the original border
        border -= slice_border

        step += chunk
        remaining_steps = max_step - step

        # Process the 'border' until the number of maximum steps is reached
        # border = border[:remaining_steps] if (remaining_steps <= len(border)) else border
        # step += len(border)
        # remaining_steps = max_step - step

        # Search the intersection point of the Pareto front and the diagonal
        # args_pbin_search = [(xrectangle, dict_man, epsilon, n) for xrectangle in slice_border]
        args_pbin_search = ((xrectangle, dict_man, epsilon, n) for xrectangle in slice_border)
        y_list = p.map(pbin_search, args_pbin_search)

        # Compute comparable rectangles b0 and b1
        b0_list = p.map(pb0, zip(slice_border, y_list))
        b1_list = p.map(pb1, zip(slice_border, y_list))

        ylow.extend(b0_list)
        yup.extend(b1_list)

        vol_b0_list = p.imap_unordered(pvol, b0_list)
        vol_b1_list = p.imap_unordered(pvol, b1_list)

        vol_ylow += sum(vol_b0_list)
        vol_yup += sum(vol_b1_list)

        ################################
        for (yl, yh) in y_list:
            # Every Border rectangle that dominates B0 is included in Ylow
            # Every Border rectangle that is dominated by B1 is included in Yup
            b0_extended = Rectangle(xspace.min_corner, yl)
            b1_extended = Rectangle(yh, xspace.max_corner)

            border_overlapping_b0 = [rect for rect in border if b0_extended.overlaps(rect)]
            border -= border_overlapping_b0

            for rect in border_overlapping_b0:
                border |= list(rect - b0_extended)

            border_overlapping_b1 = [rect for rect in border if b1_extended.overlaps(rect)]
            border -= border_overlapping_b1

            for rect in border_overlapping_b1:
                border |= list(rect - b1_extended)

            #border_dominatedby_b0 = [rect.intersection(b0_extended) for rect in border_overlapping_b0]
            #border_dominatedby_b1 = [rect.intersection(b1_extended) for rect in border_overlapping_b1]

            # Use [] (list, static) instead of () (iterator, dynamic) for preventing interleaving and racing conditions
            # of copy.deepcopy when running in parallel
            args_pborder_dominatedby_b0 = [(copy.deepcopy(b0_extended), rect) for rect in border_overlapping_b0]
            args_pborder_dominatedby_b1 = [(copy.deepcopy(b1_extended), rect) for rect in border_overlapping_b1]

            border_dominatedby_b0 = p.map(pborder_dominatedby_bi, args_pborder_dominatedby_b0)
            border_dominatedby_b1 = p.map(pborder_dominatedby_bi, args_pborder_dominatedby_b1)

            ylow.extend(border_dominatedby_b0)
            yup.extend(border_dominatedby_b1)

            vol_b0_list = p.imap_unordered(pvol, border_dominatedby_b0)
            vol_b1_list = p.imap_unordered(pvol, border_dominatedby_b1)

            vol_ylow += sum(vol_b0_list)
            vol_yup += sum(vol_b1_list)
        ################################

        # Compute incomparable rectangles
        # copy 'incomparable' list for avoiding racing conditions when running p.map in parallel
        # args_pborder = ((incomparable, y, xrectangle) for xrectangle, y in zip(slice_border, y_list))
        args_pborder = [(copy.deepcopy(incomparable), y, xrectangle) for xrectangle, y in zip(slice_border, y_list)]
        new_incomp_rects_iter = p.imap_unordered(pborder, args_pborder)

        # Flatten list
        new_incomp_rects = set(chain.from_iterable(new_incomp_rects_iter))

        # Add new incomparable rectangles to the border
        border |= new_incomp_rects

        ################################
        # Every rectangle in 'new_incomp_rects' is incomparable for current B0 and for all B0 included in Ylow
        # Every rectangle in 'new_incomp_rects' is incomparable for current B1 and for all B1 included in Yup
        ################################

        vol_border = vol_total - vol_yup - vol_ylow

        print('%s, %s, %s, %s, %s, %d, %d, %d'
              % (step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border)))

        if sleep > 0.0:
            # rs = pResultSet(list(border), ylow, yup, xspace)
            rs = ResultSet(list(border), ylow, yup, xspace)
            if n == 2:
                rs.toMatPlot2D(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.toMatPlot3D(blocking=blocking, sec=sleep, opacity=0.7)

    # Stop multiprocessing
    p.close()
    p.join()

    return pResultSet(list(border), ylow, yup, xspace)

def multidim_search_deep_first_opt_1(xspace,
                               oracle,
                               epsilon=EPS,
                               delta=DELTA,
                               max_step=STEPS,
                               blocking=False,
                               sleep=0.0):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Alpha in [0,1]^n
    alphaprime = (range(2),) * n
    alpha = itertools.product(*alphaprime)

    # Particular cases of alpha
    # zero = (0_1,...,0_n)    random.uniform(min_corner, max_corner)
    zero = (0,) * n
    # one = (1_1,...,1_n)
    one = (1,) * n

    # Set of comparable and incomparable rectangles
    comparable = [zero, one]
    incomparable = list(set(alpha) - set(comparable))

    # List of incomparable rectangles
    # border = [xspace]
    # border = SortedListWithKey(key=Rectangle.volume)

    border = SortedSet(key=Rectangle.volume)
    border.add(xspace)

    # Upper and lower clausure
    ylow = []
    yup = []

    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0
    remaining_steps = max_step - step

    num_proc = cpu_count()
    p = Pool(num_proc)

    # oracle function
    # f = oracle.membership()

    man = Manager()
    dict_man = man.dict()

    # 'f = oracle.membership()' is not thread safe!
    # Create a copy of 'oracle' for each concurrent process

    # dict_man = {proc: copy.deepcopy(oracle) for proc in mp.active_children()}
    for proc in mp.active_children():
        dict_man[proc.name] = copy.deepcopy(oracle)

    #vprint('xspace: ', xspace)
    #vprint('vol_border: ', vol_border)
    #vprint('delta: ', delta)
    #vprint('step: ', step)
    #vprint('incomparable: ', incomparable)
    #vprint('comparable: ', comparable)

    print('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder')
    while (vol_border >= delta) and (remaining_steps > 0):
        # Divide the list of incomparable rectangles in chunks of 'num_proc' elements.
        # We get the 'num_proc' elements with highest volume.

        chunk = __builtin__.min(num_proc, remaining_steps)
        chunk = __builtin__.min(chunk, len(border))
        # Take the rectangles with highest volume
        slice_border = border[-chunk:]

        # Remove elements of the slice_border from the original border
        # border = list(set(border).difference(set(slice_border)))
        border -= slice_border

        step += chunk
        remaining_steps = max_step - step

        # Process the 'border' until the number of maximum steps is reached
        # border = border[:remaining_steps] if (remaining_steps <= len(border)) else border
        # step += len(border)
        # remaining_steps = max_step - step

        # Search the intersection point of the Pareto front and the diagonal
        # args_pbin_search = [(xrectangle, dict_man, epsilon, n) for xrectangle in slice_border]
        args_pbin_search = ((xrectangle, dict_man, epsilon, n) for xrectangle in slice_border)
        y_list = p.map(pbin_search, args_pbin_search)

        # Compute comparable rectangles b0 and b1
        b0_list = p.map(pb0, zip(slice_border, y_list))
        b1_list = p.map(pb1, zip(slice_border, y_list))

        ylow.extend(b0_list)
        yup.extend(b1_list)

        vol_b0_list = p.imap_unordered(pvol, b0_list)
        vol_b1_list = p.imap_unordered(pvol, b1_list)

        vol_ylow += sum(vol_b0_list)
        vol_yup += sum(vol_b1_list)

        ################################
        # Every Border rectangle that dominates B0 is included in Ylow
        # Every Border rectangle that is dominated by B1 is included in Yup
        ylow_candidates = [rect for rect in border if any(rect.dominatesRect(b0) for b0 in b0_list)]
        yup_candidates = [rect for rect in border if any(rect.isDominatedByRect(b1) for b1 in b1_list)]

        ylow.extend(ylow_candidates)
        yup.extend(yup_candidates)

        vol_ylow_opt_list = p.imap_unordered(pvol, ylow_candidates)
        vol_yup_opt_list = p.imap_unordered(pvol, yup_candidates)

        vol_ylow += sum(vol_ylow_opt_list)
        vol_yup += sum(vol_yup_opt_list)

        border -= ylow_candidates
        border -= yup_candidates
        ################################

        # Compute incomparable rectangles
        # copy 'incomparable' list for avoiding racing conditions when running p.map in parallel
        # args_pborder = ((incomparable, y, xrectangle) for xrectangle, y in zip(slice_border, y_list))
        args_pborder = [(copy.deepcopy(incomparable), y, xrectangle) for xrectangle, y in zip(slice_border, y_list)]
        new_incomp_rects_iter = p.imap_unordered(pborder, args_pborder)

        # Flatten list
        new_incomp_rects = set(chain.from_iterable(new_incomp_rects_iter))

        ################################
        # Every Incomparable rectangle that dominates B0 is included in Ylow
        # Every Incomparable rectangle that is dominated by B1 is included in Yup
        ylow_candidates = [inc for inc in new_incomp_rects if any(inc.dominatesRect(b0) for b0 in ylow)]
        yup_candidates = [inc for inc in new_incomp_rects if any(inc.isDominatedByRect(b1) for b1 in yup)]

        ylow.extend(ylow_candidates)
        yup.extend(yup_candidates)

        vol_ylow_opt_list = p.imap_unordered(pvol, ylow_candidates)
        vol_yup_opt_list = p.imap_unordered(pvol, yup_candidates)

        vol_ylow += sum(vol_ylow_opt_list)
        vol_yup += sum(vol_yup_opt_list)

        new_incomp_rects -= ylow_candidates
        new_incomp_rects -= yup_candidates
        ################################

        # Add new incomparable rectangles to the border
        border |= new_incomp_rects

        vol_border = vol_total - vol_yup - vol_ylow

        print('%s, %s, %s, %s, %s, %d, %d, %d'
              % (step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border)))

        if sleep > 0.0:
            # rs = pResultSet(list(border), ylow, yup, xspace)
            rs = ResultSet(list(border), ylow, yup, xspace)
            if n == 2:
                rs.toMatPlot2D(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.toMatPlot3D(blocking=blocking, sec=sleep, opacity=0.7)

    # Stop multiprocessing
    p.close()
    p.join()

    return pResultSet(list(border), ylow, yup, xspace)


def multidim_search_deep_first_opt_0(xspace,
                               oracle,
                               epsilon=EPS,
                               delta=DELTA,
                               max_step=STEPS,
                               blocking=False,
                               sleep=0.0):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Alpha in [0,1]^n
    alphaprime = (range(2),) * n
    alpha = itertools.product(*alphaprime)

    # Particular cases of alpha
    # zero = (0_1,...,0_n)    random.uniform(min_corner, max_corner)
    zero = (0,) * n
    # one = (1_1,...,1_n)
    one = (1,) * n

    # Set of comparable and incomparable rectangles
    comparable = [zero, one]
    incomparable = list(set(alpha) - set(comparable))

    # List of incomparable rectangles
    # border = [xspace]
    # border = SortedListWithKey(key=Rectangle.volume)

    border = SortedSet(key=Rectangle.volume)
    border.add(xspace)

    # Upper and lower clausure
    ylow = []
    yup = []

    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0
    remaining_steps = max_step - step

    num_proc = cpu_count()
    p = Pool(num_proc)

    # oracle function
    # f = oracle.membership()

    man = Manager()
    dict_man = man.dict()

    # 'f = oracle.membership()' is not thread safe!
    # Create a copy of 'oracle' for each concurrent process

    # dict_man = {proc: copy.deepcopy(oracle) for proc in mp.active_children()}
    for proc in mp.active_children():
        dict_man[proc.name] = copy.deepcopy(oracle)

    #vprint('xspace: ', xspace)
    #vprint('vol_border: ', vol_border)
    #vprint('delta: ', delta)
    #vprint('step: ', step)
    #vprint('incomparable: ', incomparable)
    #vprint('comparable: ', comparable)

    print('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder')
    while (vol_border >= delta) and (remaining_steps > 0):
        # Divide the list of incomparable rectangles in chunks of 'num_proc' elements.
        # We get the 'num_proc' elements with highest volume.

        chunk = __builtin__.min(num_proc, remaining_steps)
        chunk = __builtin__.min(chunk, len(border))
        # Take the rectangles with highest volume
        slice_border = border[-chunk:]

        # Remove elements of the slice_border from the original border
        # border = list(set(border).difference(set(slice_border)))
        border -= slice_border

        step += chunk
        remaining_steps = max_step - step

        # Process the 'border' until the number of maximum steps is reached
        # border = border[:remaining_steps] if (remaining_steps <= len(border)) else border
        # step += len(border)
        # remaining_steps = max_step - step

        # Search the intersection point of the Pareto front and the diagonal
        # args_pbin_search = [(xrectangle, dict_man, epsilon, n) for xrectangle in slice_border]
        args_pbin_search = ((xrectangle, dict_man, epsilon, n) for xrectangle in slice_border)
        y_list = p.map(pbin_search, args_pbin_search)

        # Compute comparable rectangles b0 and b1
        b0_list = p.map(pb0, zip(slice_border, y_list))
        b1_list = p.map(pb1, zip(slice_border, y_list))

        ylow.extend(b0_list)
        yup.extend(b1_list)

        vol_b0_list = p.imap_unordered(pvol, b0_list)
        vol_b1_list = p.imap_unordered(pvol, b1_list)

        vol_ylow += sum(vol_b0_list)
        vol_yup += sum(vol_b1_list)

        # Compute incomparable rectangles
        # copy 'incomparable' list for avoiding racing conditions when running p.map in parallel
        # args_pborder = ((incomparable, y, xrectangle) for xrectangle, y in zip(slice_border, y_list))
        args_pborder = [(copy.deepcopy(incomparable), y, xrectangle) for xrectangle, y in zip(slice_border, y_list)]
        new_incomp_rects_iter = p.imap_unordered(pborder, args_pborder)

        # Flatten list
        new_incomp_rects = set(chain.from_iterable(new_incomp_rects_iter))

        # Add new incomparable rectangles to the border
        border |= new_incomp_rects

        vol_border = vol_total - vol_yup - vol_ylow

        print('%s, %s, %s, %s, %s, %d, %d, %d'
              % (step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border)))

        if sleep > 0.0:
            # rs = pResultSet(list(border), ylow, yup, xspace)
            rs = ResultSet(list(border), ylow, yup, xspace)
            if n == 2:
                rs.toMatPlot2D(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.toMatPlot3D(blocking=blocking, sec=sleep, opacity=0.7)

    # Stop multiprocessing
    p.close()
    p.join()

    return pResultSet(list(border), ylow, yup, xspace)

########################################################################################################################
# Multidimensional search with no priority for rectangles with highest volume
def multidim_search_breadth_first_opt_2(xspace,
                                    oracle,
                                    epsilon=EPS,
                                    delta=DELTA,
                                    max_step=STEPS,
                                    blocking=False,
                                    sleep=0.0):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Alpha in [0,1]^n
    alphaprime = (range(2),) * n
    alpha = itertools.product(*alphaprime)

    # Particular cases of alpha
    # zero = (0_1,...,0_n)    random.uniform(min_corner, max_corner)
    zero = (0,) * n
    # one = (1_1,...,1_n)
    one = (1,) * n

    # Set of comparable and incomparable rectangles
    comparable = [zero, one]
    incomparable = list(set(alpha) - set(comparable))

    # List of incomparable rectangles
    border = [xspace]

    # Upper and lower clausure
    ylow = []
    yup = []

    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0
    remaining_steps = max_step - step

    num_proc = cpu_count()
    p = Pool(num_proc)

    # oracle function
    # f = oracle.membership()

    man = Manager()
    dict_man = man.dict()

    # 'f = oracle.membership()' is not thread safe!
    # Create a copy of 'oracle' for each concurrent process

    # dict_man = {proc: copy.deepcopy(oracle) for proc in mp.active_children()}
    for proc in mp.active_children():
        dict_man[proc.name] = copy.deepcopy(oracle)

    #vprint('xspace: ', xspace)
    #vprint('vol_border: ', vol_border)
    #vprint('delta: ', delta)
    #vprint('step: ', step)
    #vprint('incomparable: ', incomparable)
    #vprint('comparable: ', comparable)

    print('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder')
    while (vol_border >= delta) and (remaining_steps > 0):
        # Process the 'border' until the number of maximum steps is reached

        chunk = __builtin__.min(remaining_steps, len(border))
        border = border[:chunk]
        step += chunk
        remaining_steps = max_step - step

        # Search the intersection point of the Pareto front and the diagonal
        # args_pbin_search = [(xrectangle, dict_man, epsilon, n) for xrectangle in border]
        args_pbin_search = ((xrectangle, dict_man, epsilon, n) for xrectangle in border)
        y_list = p.map(pbin_search, args_pbin_search)

        b0_list = p.map(pb0, zip(border, y_list))
        b1_list = p.map(pb1, zip(border, y_list))

        ylow.extend(b0_list)
        yup.extend(b1_list)

        vol_b0_list = p.imap_unordered(pvol, b0_list)
        vol_b1_list = p.imap_unordered(pvol, b1_list)

        vol_ylow += sum(vol_b0_list)
        vol_yup += sum(vol_b1_list)

        ################################
        for (yl, yh) in y_list:
            # Every Border rectangle that dominates B0 is included in Ylow
            # Every Border rectangle that is dominated by B1 is included in Yup

            b0_extended = Rectangle(xspace.min_corner, yl)
            b1_extended = Rectangle(yh, xspace.max_corner)

            border_overlapping_b0 = [rect for rect in border if b0_extended.overlaps(rect)]
            #border -= border_overlapping_b0
            border = [rect for rect in border if not b0_extended.overlaps(rect)]

            for rect in border_overlapping_b0:
                border += list(rect - b0_extended)

            border_overlapping_b1 = [rect for rect in border if b1_extended.overlaps(rect)]
            #border -= border_overlapping_b1
            border = [rect for rect in border if not b1_extended.overlaps(rect)]

            for rect in border_overlapping_b1:
                border += list(rect - b1_extended)

            #border_dominatedby_b0 = [rect.intersection(b0_extended) for rect in border_overlapping_b0]
            #border_dominatedby_b1 = [rect.intersection(b1_extended) for rect in border_overlapping_b1]

            # Use [] (list, static) instead of () (iterator, dynamic) for preventing interleaving and racing conditions
            # of copy.deepcopy when running in parallel

            args_pborder_dominatedby_b0 = [(copy.deepcopy(b0_extended), rect) for rect in border_overlapping_b0]
            args_pborder_dominatedby_b1 = [(copy.deepcopy(b1_extended), rect) for rect in border_overlapping_b1]

            border_dominatedby_b0 = p.map(pborder_dominatedby_bi, args_pborder_dominatedby_b0)
            border_dominatedby_b1 = p.map(pborder_dominatedby_bi, args_pborder_dominatedby_b1)

            yup.extend(border_dominatedby_b1)
            ylow.extend(border_dominatedby_b0)

            vol_yup += sum(b1.volume() for b1 in border_dominatedby_b1)
            vol_ylow += sum(b0.volume() for b0 in border_dominatedby_b0)
        ################################

        #args_pborder = ((incomparable, y, xrectangle) for xrectangle, y in zip(border, y_list))
        #new_incomp_rects = p.map(pborder, args_pborder)

        # Compute incomparable rectangles
        # copy 'incomparable' list for avoiding racing conditions when running p.map in parallel
        args_pborder = [(copy.deepcopy(incomparable), y, xrectangle) for xrectangle, y in zip(border, y_list)]
        new_incomp_rects = p.imap_unordered(pborder, args_pborder)

        # Flatten list
        border = list(chain.from_iterable(new_incomp_rects))

        ################################
        # Every rectangle in 'new_incomp_rects' is incomparable for current B0 and for all B0 included in Ylow
        # Every rectangle in 'new_incomp_rects' is incomparable for current B1 and for all B1 included in Yup
        ################################

        vol_border = vol_total - vol_yup - vol_ylow

        print('%s, %s, %s, %s, %s, %d, %d, %d'
              % (step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border)))

        if sleep > 0.0:
            # rs = pResultSet(list(border), ylow, yup, xspace)
            rs = ResultSet(list(border), ylow, yup, xspace)
            if n == 2:
                rs.toMatPlot2D(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.toMatPlot3D(blocking=blocking, sec=sleep, opacity=0.7)

    # Stop multiprocessing
    p.close()
    p.join()

    return pResultSet(border, ylow, yup, xspace)


def multidim_search_breadth_first_opt_1(xspace,
                                  oracle,
                                  epsilon=EPS,
                                  delta=DELTA,
                                  max_step=STEPS,
                                  blocking=False,
                                  sleep=0.0):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Alpha in [0,1]^n
    alphaprime = (range(2),) * n
    alpha = itertools.product(*alphaprime)

    # Particular cases of alpha
    # zero = (0_1,...,0_n)    random.uniform(min_corner, max_corner)
    zero = (0,) * n
    # one = (1_1,...,1_n)
    one = (1,) * n

    # Set of comparable and incomparable rectangles
    comparable = [zero, one]
    incomparable = list(set(alpha) - set(comparable))

    # List of incomparable rectangles
    border = [xspace]

    # Upper and lower clausure
    ylow = []
    yup = []

    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0
    remaining_steps = max_step - step

    num_proc = cpu_count()
    p = Pool(num_proc)

    # oracle function
    # f = oracle.membership()

    man = Manager()
    dict_man = man.dict()

    # 'f = oracle.membership()' is not thread safe!
    # Create a copy of 'oracle' for each concurrent process

    # dict_man = {proc: copy.deepcopy(oracle) for proc in mp.active_children()}
    for proc in mp.active_children():
        dict_man[proc.name] = copy.deepcopy(oracle)

    #vprint('xspace: ', xspace)
    #vprint('vol_border: ', vol_border)
    #vprint('delta: ', delta)
    #vprint('step: ', step)
    #vprint('incomparable: ', incomparable)
    #vprint('comparable: ', comparable)

    print('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder')
    while (vol_border >= delta) and (remaining_steps > 0):
        # Process the 'border' until the number of maximum steps is reached

        chunk = __builtin__.min(remaining_steps, len(border))
        border = border[:chunk]
        step += chunk
        remaining_steps = max_step - step

        # Search the intersection point of the Pareto front and the diagonal
        # args_pbin_search = [(xrectangle, dict_man, epsilon, n) for xrectangle in border]
        args_pbin_search = ((xrectangle, dict_man, epsilon, n) for xrectangle in border)
        y_list = p.map(pbin_search, args_pbin_search)

        b0_list = p.map(pb0, zip(border, y_list))
        b1_list = p.map(pb1, zip(border, y_list))

        ylow.extend(b0_list)
        yup.extend(b1_list)

        vol_b0_list = p.imap_unordered(pvol, b0_list)
        vol_b1_list = p.imap_unordered(pvol, b1_list)

        vol_ylow += sum(vol_b0_list)
        vol_yup += sum(vol_b1_list)

        #args_pborder = ((incomparable, y, xrectangle) for xrectangle, y in zip(border, y_list))
        #new_incomp_rects = p.map(pborder, args_pborder)

        # Compute incomparable rectangles
        # copy 'incomparable' list for avoiding racing conditions when running p.map in parallel
        args_pborder = [(copy.deepcopy(incomparable), y, xrectangle) for xrectangle, y in zip(border, y_list)]
        new_incomp_rects = p.imap_unordered(pborder, args_pborder)

        # Flatten list
        border = list(chain.from_iterable(new_incomp_rects))

        ################################
        # Every Border rectangle that dominates B0 is included in Ylow
        # Every Border rectangle that is dominated by B1 is included in Yup
        ylow_candidates = [rect for rect in border if any(rect.dominatesRect(b0) for b0 in b0_list)] # b0_list?, ylow?
        yup_candidates = [rect for rect in border if any(rect.isDominatedByRect(b1) for b1 in b1_list)] # b1_list?, yup?

        ylow.extend(ylow_candidates)
        yup.extend(yup_candidates)

        vol_ylow_opt_list = p.imap_unordered(pvol, ylow_candidates)
        vol_yup_opt_list = p.imap_unordered(pvol, yup_candidates)

        vol_ylow += sum(vol_ylow_opt_list)
        vol_yup += sum(vol_yup_opt_list)

        for rect in ylow_candidates:
            border.remove(rect)

        for rect in yup_candidates:
            border.remove(rect)
        ################################

        vol_border = vol_total - vol_yup - vol_ylow

        print('%s, %s, %s, %s, %s, %d, %d, %d'
              % (step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border)))

        if sleep > 0.0:
            # rs = pResultSet(list(border), ylow, yup, xspace)
            rs = ResultSet(list(border), ylow, yup, xspace)
            if n == 2:
                rs.toMatPlot2D(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.toMatPlot3D(blocking=blocking, sec=sleep, opacity=0.7)

    # Stop multiprocessing
    p.close()
    p.join()

    return pResultSet(border, ylow, yup, xspace)


def multidim_search_breadth_first_opt_0(xspace,
                                  oracle,
                                  epsilon=EPS,
                                  delta=DELTA,
                                  max_step=STEPS,
                                  blocking=False,
                                  sleep=0.0):
    # type: (Rectangle, Oracle, float, float, int, bool, float) -> pResultSet

    # Xspace is a particular case of maximal rectangle
    # Xspace = [min_corner, max_corner]^n = [0, 1]^n
    # xspace.min_corner = (0,) * n
    # xspace.max_corner = (1,) * n

    # Dimension
    n = xspace.dim()

    # Alpha in [0,1]^n
    alphaprime = (range(2),) * n
    alpha = itertools.product(*alphaprime)

    # Particular cases of alpha
    # zero = (0_1,...,0_n)    random.uniform(min_corner, max_corner)
    zero = (0,) * n
    # one = (1_1,...,1_n)
    one = (1,) * n

    # Set of comparable and incomparable rectangles
    comparable = [zero, one]
    incomparable = list(set(alpha) - set(comparable))

    # List of incomparable rectangles
    border = [xspace]

    # Upper and lower clausure
    ylow = []
    yup = []

    vol_total = xspace.volume()
    vol_yup = 0
    vol_ylow = 0
    vol_border = vol_total
    step = 0
    remaining_steps = max_step - step

    num_proc = cpu_count()
    p = Pool(num_proc)

    # oracle function
    # f = oracle.membership()

    man = Manager()
    dict_man = man.dict()

    # 'f = oracle.membership()' is not thread safe!
    # Create a copy of 'oracle' for each concurrent process

    # dict_man = {proc: copy.deepcopy(oracle) for proc in mp.active_children()}
    for proc in mp.active_children():
        dict_man[proc.name] = copy.deepcopy(oracle)

    #vprint('xspace: ', xspace)
    #vprint('vol_border: ', vol_border)
    #vprint('delta: ', delta)
    #vprint('step: ', step)
    #vprint('incomparable: ', incomparable)
    #vprint('comparable: ', comparable)

    print('Report\nStep, Ylow, Yup, Border, Total, nYlow, nYup, nBorder')
    while (vol_border >= delta) and (remaining_steps > 0):
        # Process the 'border' until the number of maximum steps is reached

        chunk = __builtin__.min(remaining_steps, len(border))
        border = border[:chunk]
        step += chunk
        remaining_steps = max_step - step

        # Search the intersection point of the Pareto front and the diagonal
        # args_pbin_search = [(xrectangle, dict_man, epsilon, n) for xrectangle in border]
        args_pbin_search = ((xrectangle, dict_man, epsilon, n) for xrectangle in border)
        y_list = p.map(pbin_search, args_pbin_search)

        b0_list = p.map(pb0, zip(border, y_list))
        b1_list = p.map(pb1, zip(border, y_list))

        ylow.extend(b0_list)
        yup.extend(b1_list)

        vol_b0_list = p.imap_unordered(pvol, b0_list)
        vol_b1_list = p.imap_unordered(pvol, b1_list)

        vol_ylow += sum(vol_b0_list)
        vol_yup += sum(vol_b1_list)

        # Compute incomparable rectangles
        # copy 'incomparable' list for avoiding racing conditions when running p.map in parallel
        # args_pborder = ((incomparable, y, xrectangle) for xrectangle, y in zip(border, y_list))
        args_pborder = [(copy.deepcopy(incomparable), y, xrectangle) for xrectangle, y in zip(border, y_list)]
        new_incomp_rects = p.imap_unordered(pborder, args_pborder)

        # Flatten list
        border = list(chain.from_iterable(new_incomp_rects))

        vol_border = vol_total - vol_yup - vol_ylow

        print('%s, %s, %s, %s, %s, %d, %d, %d'
              % (step, vol_ylow, vol_yup, vol_border, vol_total, len(ylow), len(yup), len(border)))

        if sleep > 0.0:
            # rs = pResultSet(list(border), ylow, yup, xspace)
            rs = ResultSet(list(border), ylow, yup, xspace)
            if n == 2:
                rs.toMatPlot2D(blocking=blocking, sec=sleep, opacity=0.7)
            elif n == 3:
                rs.toMatPlot3D(blocking=blocking, sec=sleep, opacity=0.7)

    # Stop multiprocessing
    p.close()
    p.join()

    return pResultSet(border, ylow, yup, xspace)

########################################################################################################################

# Dimensional tests
def Search2D(ora,
             min_cornerx=0.0,
             min_cornery=0.0,
             max_cornerx=1.0,
             max_cornery=1.0,
             epsilon=EPS,
             delta=DELTA,
             max_step=STEPS,
             blocking=False,
             sleep=0.0,
             opt_level=2):
    # type: (Oracle, float, float, float, float, float, float, int, bool, float, int) -> pResultSet
    xyspace = create2DSpace(min_cornerx, min_cornery, max_cornerx, max_cornery)
    rs = multidim_search(xyspace, ora, epsilon, delta, max_step, blocking, sleep, opt_level)

    # Explicitly print a set of n points in the Pareto boundary for emphasizing the front
    n = int((max_cornerx - min_cornerx) / 0.1)
    points = rs.getPointsBorder(n)

    #vprint("Points ", points)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]

    # rs.toMatPlot2D(targetx=xs, targety=ys, blocking=True)
    # rs.toMatPlot2DLight(targetx=xs, targety=ys, blocking=True)
    rs.simplify()
    rs.toMatPlot2DLight(blocking=True)
    return rs


def Search3D(ora,
             min_cornerx=0.0,
             min_cornery=0.0,
             min_cornerz=0.0,
             max_cornerx=1.0,
             max_cornery=1.0,
             max_cornerz=1.0,
             epsilon=EPS,
             delta=DELTA,
             max_step=STEPS,
             blocking=False,
             sleep=0.0,
             opt_level=2):
    # type: (Oracle, float, float, float, float, float, float, float, float, int, bool, float, int) -> pResultSet
    xyspace = create3DSpace(min_cornerx, min_cornery, min_cornerz, max_cornerx, max_cornery, max_cornerz)

    rs = multidim_search(xyspace, ora, epsilon, delta, max_step, blocking, sleep, opt_level)

    # Explicitly print a set of n points in the Pareto boundary for emphasizing the front
    n = int((max_cornerx - min_cornerx) / 0.1)
    points = rs.getPointsBorder(n)

    #vprint("Points ", points)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]

    # rs.toMatPlot3D(targetx=xs, targety=ys, targetz=zs, blocking=True)
    # rs.toMatPlot3DLight(targetx=xs, targety=ys, targetz=zs, blocking=True)
    rs.simplify()
    rs.toMatPlot3DLight(blocking=True)
    return rs


def SearchND(ora,
             min_corner=0.0,
             max_corner=1.0,
             epsilon=EPS,
             delta=DELTA,
             max_step=STEPS,
             blocking=False,
             sleep=0.0,
             opt_level=2):
    # type: (Oracle, float, float, float, float, int, bool, float, int) -> pResultSet
    d = ora.dim()

    minc = (min_corner,) * d
    maxc = (max_corner,) * d
    xyspace = Rectangle(minc, maxc)

    rs = multidim_search(xyspace, ora, epsilon, delta, max_step, blocking, sleep, opt_level)
    rs.simplify()
    return rs