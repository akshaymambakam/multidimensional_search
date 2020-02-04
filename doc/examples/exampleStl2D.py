from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import Search2D, Search3D, EPS, DELTA, STEPS
from ParetoLib.Search.ResultSet import ResultSet

import sys, os
EPS = 0.0001
DELTA = 0.0001
STEPS = 100
# File containing the definition of the Oracle
nfile = './ecgLearn.txt'
human_readable = True

controlFile = open('ecgLearn.txt', 'w')
controlText = ''
controlLines = []
print >>controlFile, './'+sys.argv[1]+'.stl'
print >>controlFile, './'+sys.argv[2]+'.csv'
print >>controlFile, './ecgLearn2D.param'

controlFile.close()

# Definition of the n-dimensional space
min_x, min_y = (0.0, -1.0)
max_x, max_y = (70.0, 1.0)

oracle = OracleSTLeLib()
oracle.from_file(nfile, human_readable)
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
              parallel=True,
              logging=False,
              simplify=False)
rs.plot_2D()
rs.to_file(sys.argv[3]+".zip")