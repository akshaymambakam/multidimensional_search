from ParetoLib.Oracle.OracleFunction import OracleFunction
from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import SearchIntersection2D, Search2D, EPS, DELTA, STEPS
from ParetoLib.Search.ResultSet import ResultSet

def pareto_2D_func_intersection(min_tuple, max_tuple):
  nfile1 = '../../Tests/Oracle/OracleFunction/2D/test1_1.txt'
  nfile2 = '../../Tests/Oracle/OracleFunction/2D/test1_2.txt'

  human_readable = True
  
  orac1 = OracleFunction()
  orac1.from_file(nfile1, human_readable)

  orac2 = OracleFunction()
  orac2.from_file(nfile2, human_readable)

  # Definition of the n-dimensional space
  min_x, min_y = min_tuple
  max_x, max_y = max_tuple

  print 'Just before the top most call.'
  output_intersect = SearchIntersection2D(oracle1=orac1, oracle2=orac2,
                min_cornerx=min_x,
                min_cornery=min_y,
                max_cornerx=max_x,
                max_cornery=max_y,
                epsilon=EPS,
                delta=0.01,
                max_step=STEPS,
                blocking=False,
                sleep=0,
                opt_level=0,
                parallel=False,
                logging=False,
                simplify=True)
  return output_intersect

def pareto_2D_Intersection(ecg_name, numParams, formula_name1, formula_name2, min_tuple, max_tuple):
  nfile1 = './ecgLearn1.txt'
  nfile2 = './ecgLearn2.txt'
  #nfile1 = '../../Tests/Oracle/OracleFunction/2D/test1_1.txt'
  #nfile2 = '../../Tests/Oracle/OracleFunction/2D/test1_2.txt'

  paramFile = open('ecgLearn.param', 'w')
  for i in range(numParams):
    print >>paramFile, 'p'+str(i+1)
  paramFile.close()

  controlFile = open('ecgLearn1.txt', 'w')
  controlText = ''
  controlLines = []
  print >>controlFile, './'+formula_name1+'.stl'
  print >>controlFile, './'+ecg_name+'L.csv'
  print >>controlFile, './ecgLearn.param'

  controlFile.close()

  controlFile = open('ecgLearn2.txt', 'w')
  controlText = ''
  controlLines = []
  print >>controlFile, './'+formula_name2+'.stl'
  print >>controlFile, './'+ecg_name+'L.csv'
  print >>controlFile, './ecgLearn.param'

  controlFile.close()

  human_readable = True

  # Definition of the n-dimensional space
  min_x, min_y = min_tuple
  max_x, max_y = max_tuple

  orac1 = OracleSTLeLib()
  orac1.from_file(nfile1, human_readable)

  orac2 = OracleSTLeLib()
  orac2.from_file(nfile2, human_readable)

  '''

  orac1 = OracleFunction()
  orac1.from_file(nfile1, human_readable)

  orac2 = OracleFunction()
  orac2.from_file(nfile2, human_readable)

  '''

  print 'Just before the top most call.'
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
  print output_intersect
  return output_intersect

#(intersection, border, xspace, intersect_region) = pareto_2D_Intersection('221', 2, 'ecg2_fn2D', 'ecg2_fp2D', (0, -5.0), (70, 5.0))

(intersection, border, xspace, intersect_region) = pareto_2D_func_intersection((0.0, 0.0), (1.0, 1.0))

rs = ResultSet(border=border, yup=intersect_region, xspace=xspace)
rs.plot_2D()