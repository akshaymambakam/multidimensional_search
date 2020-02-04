from ParetoLib.Oracle.OracleFnFp3D import OracleFnFp3D
from ParetoLib.Search.Search import Search2D, EPS, DELTA, STEPS

# File containing the definition of the Oracle
nfile = '../../Tests/Oracle/OracleFunction/2D/test1.txt'
human_readable = True

# Definition of the n-dimensional space
min_x, min_y = (0.0, 0.0)
max_x, max_y = (40.0, 40.0)

oracle = OracleFnFp3D('/home/akshay/Documents/paretoDev/scratchFnFp', '201L.csv', (0, -1.0, - 1.0), (70, 1.0, 1.0))
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
              opt_level=0,
              parallel=False,
              logging=True,
              simplify=True)
rs.plot_2D()
rs.to_file("result.zip")