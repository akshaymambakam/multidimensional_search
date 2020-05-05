from ParetoLib.Oracle.OracleFnFp3D import OracleFnFp3D
from ParetoLib.Search.Search import Search2D, EPS, DELTA, STEPS
import sys

# File containing the definition of the Oracle
nfile = '../../Tests/Oracle/OracleFunction/2D/test1.txt'
human_readable = True

# Definition of the n-dimensional space
min_x, min_y = (0.0, 0.0)
max_x, max_y = (40.0, 40.0)

oracle = OracleFnFp3D('/home/mambakaa/Documents/paretoDev/scratchFnFp', sys.argv[1]+'L.csv', (0, -1.0, - 1.0), (70, 1.0, 1.0))
rs = Search2D(ora=oracle,
              min_cornerx=min_x,
              min_cornery=min_y,
              max_cornerx=max_x,
              max_cornery=max_y,
              epsilon=EPS,
              delta=DELTA,
              max_step=STEPS,
              blocking=False,
              sleep=0,
              opt_level=2,
              parallel=False,
              logging=True,
              simplify=True)
rs.to_file("discNew1000Pareto"+sys.argv[1]+".zip")
rs.plot_2D()