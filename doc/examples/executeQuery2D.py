import sys
import io

import ParetoLib.Oracle as RootOracle
from ParetoLib.Oracle.Oracle import Oracle
from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import SearchIntersection2D, Search2D, EPS, DELTA, STEPS


# Definition of the n-dimensional space
min_x, min_y = (0, -5)
max_x, max_y = (70, 5)

human_readable = True

orac1 = OracleSTLeLib()
orac1.from_file(sys.argv[1], human_readable)

orac2 = OracleSTLeLib()
orac2.from_file(sys.argv[2], human_readable)

output_intersect = SearchIntersection2D(oracle1=orac1, oracle2=orac2,
              min_cornerx=min_x,
              min_cornery=min_y,
              max_cornerx=max_x,
              max_cornery=max_y,
              epsilon=EPS,
              delta=0.0001,
              max_step=STEPS,
              blocking=False,
              sleep=0,
              opt_level=0,
              parallel=False,
              logging=False,
              simplify=True)

return_bool = len(output_intersect[0]) != 0
orac1 = None
orac2 = None
output_intersect = None

if(return_bool):
    exit(0)
else:
    exit(1)