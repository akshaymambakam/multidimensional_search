from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Oracle.OracleEpsSTLe import OracleEpsSTLe
from ParetoLib.Search.Search import SearchIntersectionND_2, EPS, DELTA, STEPS
from ParetoLib.Search.ResultSet import ResultSet
from ParetoLib.Geometry.Rectangle import Rectangle

import sys
import copy

import time
import math

import intervals as I

deltaGlobal = float(sys.argv[3])/1000
bcGlobal = 0
timeOut = 10*60

def get_learn_formula_oc(formula_name, parNum, limit):
  pstl_file = open('./'+formula_name+'.stl')
  pstl_string = pstl_file.read()
  pstl_file.close()
  inc_string = pstl_string
  inc_string = inc_string.replace("topToken", "(F (p"+str(parNum+1)+" "+str(limit)+"-p"+str(parNum+2)+")")
  inc_string = inc_string.replace("bottomToken", ")")
  return inc_string, parNum + 2
def get_learn_formula_th(formula_name, parNum, inc):
  pstl_file = open('./'+formula_name+'.stl')
  pstl_string = pstl_file.read()
  pstl_file.close()
  inc_string = pstl_string
  if(inc):
    inc_string = inc_string.replace("topToken", "(>=")
  else:
    inc_string = inc_string.replace("topToken", "(<=")
  if(inc):
    inc_string = inc_string.replace("bottomToken", "p"+str(parNum+1)+")")
  else:
    inc_string = inc_string.replace("bottomToken", "0-p"+str(parNum+1)+")")
  return inc_string, parNum + 1

def get_inc_formula(formula_string):
  inc_formula = "(G (0 inf) (-> (and (<= x1 2) (>= x1 2)) (not "
  inc_formula = inc_formula + formula_string
  inc_formula = inc_formula + " ) ) )"
  return inc_formula
def get_dec_formula(formula_string):
  inc_formula = "(G (0 inf) (-> (and (<= x1 1) (>= x1 1)) "
  inc_formula = inc_formula + formula_string
  inc_formula = inc_formula + " ) )"
  return inc_formula

def get_inc_formula_eps(formula_string):
  inc_formula = "(and (and (<= x1 2) (>= x1 2)) "
  inc_formula = inc_formula + formula_string
  inc_formula = inc_formula + " )"
  return inc_formula
def get_dec_formula_eps(formula_string):
  inc_formula = "(and (and (<= x1 1) (>= x1 1)) (not "
  inc_formula = inc_formula + formula_string
  inc_formula = inc_formula + " ) )"
  return inc_formula

# numParams = 1
def get_range(ecg_name, formula_name1, incToken, decToken, bottomToken, low_limit, high_limit, traceNum):
  pstl_file = open('./'+formula_name1+'.stl')
  pstl_string = pstl_file.read()
  pstl_file.close()
  inc_string = pstl_string
  inc_string = inc_string.replace("topToken", incToken)
  inc_string = inc_string.replace("bottomToken", bottomToken)

  dec_string = pstl_string
  dec_string = dec_string.replace("topToken", decToken)
  dec_string = dec_string.replace("bottomToken", bottomToken)
  wrapOuter1 = "(F (0 inf) (and (and (<= x1 "+str(traceNum)+") (>= x1 "+str(traceNum)+") ) "  
  wrapOuter2    = "))"
  fn_stl_string = wrapOuter1+inc_string+wrapOuter2
  fp_stl_string = wrapOuter1+dec_string+wrapOuter2
  
  #print fn_stl_string
  #print fp_stl_string

  fn_scratch = open('scratchInterFn.stl', 'w')
  fn_scratch.write(fn_stl_string)
  fn_scratch.close()

  fp_scratch = open('scratchInterFp.stl', 'w')
  fp_scratch.write(fp_stl_string)
  fp_scratch.close()

  list_intervals = [(low_limit, high_limit)]
  (intersection, border, xspace, intersect_region) = pareto_ND_Intersection(ecg_name, 1, "scratchInterFn", "scratchInterFp", list_intervals, [])
  return (intersection[0].min_corner[0], intersection[0].max_corner[0])

get_range_th = lambda x1,x2,x3,x4,x5: get_range(x1, x2, "(<= ", "(>= ", " p1)", x3, x4, x5)
get_range_oc = lambda x1,x2,x3,x4,x5: get_range(x1, x2, "(F (0 p1) ", "(F (p1 "+str(x4)+") ",")", x3, x4, x5)

def pareto_ND_Intersection(ecg_name, numParams, formula_name1, formula_name2, list_intervals, list_contraints):
  nfile1 = './ecgLearn1.txt'
  nfile2 = './ecgLearn2.txt'
  #nfile1 = '../../Tests/Oracle/OracleFunction/2D/test1_1.txt'
  #nfile2 = '../../Tests/Oracle/OracleFunction/2D/test1_2.txt'

  # Copy the template file to a scratch file.
  stl_file   = open('./'+formula_name1+'.stl')
  stl_string = stl_file.read()
  stl_file.close()

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

  orac1 = OracleSTLeLib()
  orac1.from_file(nfile1, human_readable)

  orac2 = OracleSTLeLib()
  orac2.from_file(nfile2, human_readable)

  output_intersect = SearchIntersectionND_2(orac1, orac2,
                list_intervals, list_contraints,
                epsilon=EPS,
                delta=deltaGlobal,
                max_step=STEPS,
                blocking=False,
                sleep=0,
                opt_level=int(sys.argv[2]),
                parallel=False,
                logging=False,
                simplify=True)
  return output_intersect

def pareto_ND_Intersection_eps(ecg_name, numParams, formula_name1, formula_name2, list_intervals, list_contraints):
  nfile1 = './ecgLearn1.txt'
  nfile2 = './ecgLearn2.txt'
  #nfile1 = '../../Tests/Oracle/OracleFunction/2D/test1_1.txt'
  #nfile2 = '../../Tests/Oracle/OracleFunction/2D/test1_2.txt'

  # Copy the template file to a scratch file.
  stl_file   = open('./'+formula_name1+'.stl')
  stl_string = stl_file.read()
  stl_file.close()

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

  orac1 = OracleEpsSTLe(boundOnCount=bcGlobal, intvlEpsilon=1)
  orac1.from_file(nfile1, human_readable)

  orac2 = OracleEpsSTLe(boundOnCount=bcGlobal, intvlEpsilon=1)
  orac2.from_file(nfile2, human_readable)

  output_intersect = SearchIntersectionND_2(orac1, orac2,
                list_intervals, list_contraints,
                epsilon=EPS,
                delta=deltaGlobal,
                max_step=STEPS,
                blocking=False,
                sleep=0,
                opt_level=int(sys.argv[2]),
                parallel=False,
                logging=False,
                simplify=True)
  return output_intersect


t0 = time.time()
find_a_formula = True
if find_a_formula:
  feature_list = ['ditch_th', 'ditch_oc', 'peak1_th', 'peak1_oc', 'peak2_th', 'peak2_oc']
  range_list   = [(-10,10), (0, 136), (-10, 10), (0,60), (-10, 10), (0, 60)]
  index = 0
  rdiff_list = []
  for feature in feature_list:
    (rmin,rmax) = range_list[index]
    print 'index: ', index
    if '_th' in feature:
      fmin1, fmax1 = get_range_th(str(sys.argv[1]), feature, rmin, rmax, 1)
      fmin2, fmax2 = get_range_th(str(sys.argv[1]), feature, rmin, rmax, 2)
      
    else:
      fmin1, fmax1 = get_range_oc(str(sys.argv[1]), feature, rmin, rmax, 1)
      fmin2, fmax2 = get_range_oc(str(sys.argv[1]), feature, rmin, rmax, 2)
    r1 = I.closed(fmin1, fmax1)
    r2 = I.closed(fmin2, fmax2)
    rinter = r1.intersection(r2)
    rdiff1 = r1.difference(r2)
    rdiff2 = r2.difference(r1)
    rdiff = rdiff1.union(rdiff2)
    runion = r1.union(r2)
    rdiffval = 0
    runionval = 0 
    if not rdiff.is_empty():
      for rd in rdiff:
        rdiffval += (rd.upper - rd.lower)
    if not runion.is_empty():
      for ru in runion:
        runionval += (ru.upper - ru.lower)
    r1_size = r1.upper - r1.lower
    r2_size = r2.upper - r2.lower
    rinter_size = rinter.upper - rinter.lower
    #rdiffval = rdiffval / max(r1_size, r2_size)
    rdiffval = rdiffval / runionval
    # rdiffval = rdiffval / rinter_size
    print '>>>>>>>>>>>>>>>>>>>>>>>'
    print feature
    print rdiffval
    print r1, r1_size
    print r2, r2_size
    print '-------------------'
    # r1.contains(r2) or r2.contains(r1) or 
    #if not (r1.contains(r2) or r2.contains(r1) or (r1_size/(rmax-rmin) > 0.9) or (r2_size/(rmax-rmin) > 0.9)):
    if not ((r1_size/(rmax-rmin) > 0.9) or (r2_size/(rmax-rmin) > 0.9)):
      rdiffval = rdiffval
    else:
      rdiffval = 0
    print rdiffval
    print '-------------------'
    index += 1
    rdiff_list.append(rdiffval)



  rank_list = []
  for i in range(len(rdiff_list)):
    rank = 0
    for j in range(len(rdiff_list)):
      if(rdiff_list[i] < rdiff_list[j]):
        rank += 1
    rank_list.append(rank)
  print rank_list

  formula_index = 0
  numForFound = 0
  for i in range(max(rank_list)):
    first_index = rank_list.index(i)
    formula1_name = feature_list[first_index]
    inc_formula_list = []
    parNum = 0
    list_intervals = []
    list_constraints = []
    if '_th' in feature_list[first_index]:
      list_intervals.append(range_list[first_index])
      parNum = parNum + 1
    elif '_oc' in feature_list[first_index]:
      list_intervals.append(range_list[first_index])
      list_intervals.append(range_list[first_index])
      list_constraints.append([parNum+1,parNum+2,range_list[first_index][1]])
      parNum = parNum + 2
    list_intervals_old = list_intervals
    list_constraints_old = list_constraints

    for j in range(i+1, max(rank_list)):
      formula_index += 1
      list_intervals = copy.deepcopy(list_intervals_old)
      list_constraints = copy.deepcopy(list_constraints_old)
      new_list_constraints = []
      second_index = rank_list.index(j)
      formula2_name = feature_list[second_index]
      print '---'
      print i, j
      print first_index, second_index
      print '---'
      
      if '_th' in feature_list[second_index]:
        list_intervals.append(range_list[second_index])
        x = parNum + 1
      elif '_oc' in feature_list[second_index]:
        list_intervals.append(range_list[second_index])
        list_intervals.append(range_list[second_index])
        list_constraints.append([parNum+1,parNum+2,range_list[second_index][1]])
        x = parNum + 2
      
      for constraint in list_constraints:
        new_constraint = []
        for k in range(x):
          if (k+1) in constraint[:-1]:
            new_constraint.append(1)
          else:
            new_constraint.append(0)
        new_constraint.append(constraint[-1])
        new_constraint = tuple(new_constraint)
        new_list_constraints.append(new_constraint)

      if '_th' in feature_list[first_index]:
        bi_range = 2
      elif '_oc' in feature_list[first_index]:
        bi_range = 1

      if '_th' in feature_list[second_index]:
        bj_range = 2
      elif '_oc' in feature_list[second_index]:
        bj_range = 1

      for bi in range(bi_range):
        for bj in range(bj_range):
          if '_th' in feature_list[first_index]:
            (formula1, parNum) = get_learn_formula_th(formula1_name, 0, bi)
          elif '_oc' in feature_list[first_index]:
            (formula1, parNum) = get_learn_formula_oc(formula1_name, 0, range_list[first_index][1])

          if '_th' in feature_list[second_index]:
            (formula2, x) = get_learn_formula_th(formula2_name, parNum, bj)
          elif '_oc' in feature_list[second_index]:
            (formula2, x) = get_learn_formula_oc(formula2_name, parNum, range_list[second_index][1])

          total_formula = "(or \n"+formula1+"\n"+formula2+" )"
          inc_formula = get_inc_formula_eps(total_formula)
          dec_formula = get_dec_formula_eps(total_formula)

          fn_scratch = open('tempInterFn.stl', 'w')
          fn_scratch.write(inc_formula)
          fn_scratch.close()

          fp_scratch = open('tempInterFp.stl', 'w')
          fp_scratch.write(dec_formula)
          fp_scratch.close()

          print ':::::::::::::::::::::::::'
          print 'formula_index:', formula_index
          print "li:", list_intervals
          print "nlc:", new_list_constraints
          print 'x:', x
          print '>>>>>>>>>>>>>>>>>>>>>>>>>'
          print inc_formula
          # print dec_formula
          print ':::::::::::::::::::::::::'

          (intersection, border, xspace, intersect_region) = pareto_ND_Intersection_eps(str(sys.argv[1]), x, 'tempInterFn', 'tempInterFp', list_intervals, new_list_constraints)
          print len(intersection)
          if len(intersection) > 0:
            numForFound += 1
            print 'Eureka!'
            print intersection
            t1 = time.time()
            print 'time taken:', t1 - t0
            if(numForFound >= 2):
              exit(0)
          else:
            t1 = time.time()
            print 'time taken:', t1 - t0
            if(t1-t0 > timeOut):
              print 'timeOut after',timeOut 
              exit(0)
  exit(0)
list_intervals = [(0, 60), (0, 60), (-10, 10)]
list_constraints = [(1,1,0,60)]
# (intersection, border, xspace, intersect_region) = pareto_ND_Intersection(str(sys.argv[1]), 3, 'ecgInterTemplateFnND', 'ecgInterTemplateFpND', list_intervals, list_constraints)
(intersection, border, xspace, intersect_region) = pareto_ND_Intersection_eps(str(sys.argv[1]), 3, 'ecgInterTemplateEpsFnND', 'ecgInterTemplateEpsFpND', list_intervals, list_constraints)
print len(intersection)
print intersection
#print border
#print intersect_region
intersect_region = []
border = []
exit(0)
rs1 = ResultSet(border=border, yup=intersection, ylow=intersect_region, xspace=xspace)
rs1.to_file(sys.argv[1]+"_testJD.zip")
rs1.plot_3D(opacity=0.1, fig_title='Intersection of pareto fronts', var_names=['p1','p2','p3'],clip=True)
rs1.plot_2D_light(xaxe=0, yaxe=1, fig_title =  'Projection on (p1,p2) of intersection', var_names=['p1','p2','p3'])
rs1.plot_2D_light(xaxe=1, yaxe=2, fig_title =  'Projection on (p2,p3) of intersection', var_names=['p1','p2','p3'])
rs1.plot_2D_light(xaxe=0, yaxe=2, fig_title =  'Projection on (p1,p3) of intersection', var_names=['p1','p2','p3'])
t1 = time.time()