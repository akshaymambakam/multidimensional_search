from ParetoLib.Oracle.OracleEpsSTLe import OracleEpsSTLe
from ParetoLib.Oracle.OracleFunction import OracleFunction
from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import SearchIntersection2D, SearchIntersection3D, Search2D, EPS, DELTA, STEPS
from ParetoLib.Search.ResultSet import ResultSet

import sys

def pareto_3D_Intersection(ecg_name, numParams, formula_name1, formula_name2, min_tuple, max_tuple):
  nfile1 = './ecgLearn1.txt'
  nfile2 = './ecgLearn2.txt'
  #nfile1 = '../../Tests/Oracle/OracleFunction/2D/test1_1.txt'
  #nfile2 = '../../Tests/Oracle/OracleFunction/2D/test1_2.txt'

  # Copy the template file to a scratch file.
  stl_file   = open('./'+formula_name1+'.stl')
  stl_string = stl_file.read()
  stl_file.close()

  # Write the value of bound on num_fn here.
  stl_string = stl_string.replace('num_fn', str(sys.argv[2]))

  # Write the template formula into a scratch file.
  fn_scratch = open('scratchInterFn.stl', 'w')
  fn_scratch.write(stl_string)
  fn_scratch.close()

  # Copy the template file to a scratch file.
  stl_file   = open('./'+formula_name2+'.stl','r')
  stl_string = stl_file.read()
  stl_file.close()

  # Write the template formula into a scratch file.
  fp_scratch = open('scratchInterFp.stl','w')
  fp_scratch.write(stl_string)
  fp_scratch.close()

  paramFile = open('ecgLearn.param', 'w')
  for i in range(numParams):
    print >>paramFile, 'p'+str(i+1)
  paramFile.close()

  controlFile = open('ecgLearn1.txt', 'w')
  controlText = ''
  controlLines = []
  print >>controlFile, './scratchInterFn.stl'
  print >>controlFile, './'+ecg_name+'L.csv'
  print >>controlFile, './ecgLearn.param'

  controlFile.close()

  controlFile = open('ecgLearn2.txt', 'w')
  controlText = ''
  controlLines = []
  print >>controlFile, './scratchInterFp.stl'
  print >>controlFile, './'+ecg_name+'L.csv'
  print >>controlFile, './ecgLearn.param'

  controlFile.close()

  human_readable = True

  # Definition of the n-dimensional space
  min_x, min_y, min_z = min_tuple
  max_x, max_y, max_z = max_tuple

  orac1 = OracleSTLeLib()
  orac1.from_file(nfile1, human_readable)

  orac2 = OracleEpsSTLe(boundOnCount=int(sys.argv[3]))
  orac2.from_file(nfile2, human_readable)

  output_intersect = SearchIntersection3D(oracle1=orac1, oracle2=orac2,
                min_cornerx=min_x,
                min_cornery=min_y,
                min_cornerz=min_z,
                max_cornerx=max_x,
                max_cornery=max_y,
                max_cornerz=max_z,
                epsilon=EPS,
                delta=0.0000001,
                max_step=STEPS,
                blocking=False,
                sleep=0,
                opt_level=0,
                parallel=False,
                logging=False,
                simplify=True)
  print output_intersect
  return output_intersect

(intersection, border, xspace, intersect_region) = pareto_3D_Intersection(str(sys.argv[1]), 3, 'ecgTemplateFn3D', 'ecgInterTemplateFp3D', (0, -1.0, -1.0), (70, 1.0, 1.0))

rs = ResultSet(border=border, yup=intersect_region, xspace=xspace)
rs.plot_3D()