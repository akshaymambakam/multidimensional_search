import math
import time
from ParetoLib.Geometry.Rectangle import Rectangle
import ParetoLib.Search as RootSearch
from operator import sub

def create_ND_space(args):
    # type: (iter) -> Rectangle
    # args = [(minx, maxx), (miny, maxy),..., (minz, maxz)]
    RootSearch.logger.debug('Creating Space')
    start = time.time()
    minc = tuple(minx for minx, _ in args)
    maxc = tuple(maxx for _, maxx in args)
    xyspace = Rectangle(minc, maxc)
    end = time.time()
    time0 = end - start
    RootSearch.logger.debug('Time creating Space: {0}'.format(str(time0)))
    return xyspace

def bound_box_with_constraints(box, constraints):
	max_bound = 1
	min_bound = 0
	flag_max = 0
	flag_min = 0
 	for constraint in list_contraints:
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

if __name__ == '__main__':
	list_intervals = [(0, 10), (0, 60), (0, 10), (-35, 0), (0, 136), (0, 10)]
	xyspace = create_ND_space(list_intervals)
	list_contraints = [(0,1,1,0,0,0,60), (-1,0,0,-1,0,0, -5)]
	min_bound, max_bound =  bound_box_with_constraints(xyspace, list_contraints)
	end_min = tuple(i+(j-i)*min_bound for i,j in zip(xyspace.min_corner, xyspace.max_corner))
	end_max = tuple(i+(j-i)*max_bound for i,j in zip(xyspace.min_corner, xyspace.max_corner))
	mod_rectangle = Rectangle(end_min, end_max)
	print min_bound, max_bound
	print mod_rectangle