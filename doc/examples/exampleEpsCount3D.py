from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import Search3D, EPS, DELTA, STEPS
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
print >>controlFile, './ecgLearn3D.param'

controlFile.close()


min_x, min_y, min_z = (0,   -2, -2)
max_x, max_y, max_z = (70.0, 2,  2)

oracle = OracleEpsSTLe(boundOnCount = 2)
oracle.from_file(nfile, human_readable)
rs = Search3D(ora=oracle,
              min_cornerx=min_x,
              min_cornery=min_y,
              min_cornerz=min_z,
              max_cornerx=max_x,
              max_cornery=max_y,
              max_cornerz=max_z,
              epsilon=EPS,
              delta=DELTA,
              max_step=STEPS,
              blocking=False,
              sleep=0,
              opt_level=0,
              parallel=False,
              logging=False,
              simplify=True)
rs.to_file(sys.argv[3]+".zip")