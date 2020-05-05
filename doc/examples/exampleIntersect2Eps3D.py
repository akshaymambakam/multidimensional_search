from ParetoLib.Oracle.OracleEpsSTLe import OracleEpsSTLe
from ParetoLib.Oracle.OracleFunction import OracleFunction
from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import SearchIntersection2D, SearchIntersection3D, Search3D, EPS, DELTA, STEPS
from ParetoLib.Search.ResultSet import ResultSet
from ParetoLib.Geometry.Rectangle import Rectangle

import sys
from exampleStlFp3D import getParetoFrontFp3D
from exampleStlFn3D import getParetoFrontFn3D
from exampleComputeIntersect3D import computeIntersect3D
import copy

import time

def filter_dup_box(testBox, compareBox):
  newBox = []
  for i in range(len(testBox)):
    insi = False
    ri = testBox[i]
    for j in range(len(compareBox)):
      rj = compareBox[j]
      if rj == ri:
        continue
      if rj.inside(ri.min_corner) and rj.inside(ri.max_corner):
        insi = True
        break
    if not insi:
      newBox.append(ri)
  return newBox

def getIntersectRegion(setBoxes):
  intersection = []
  flambda = lambda x: (70.0-x[0], -x[1], -x[2])
  for box in setBoxes:
    minTuple = box.min_corner
    maxTuple = box.max_corner
    deltaIn = box.volume()/float(100)
    rs1 = getParetoFrontFn3D('ecgTemplateFn3D', sys.argv[1]+'L', 'resultTmplFn3D', sys.argv[2], minTuple, maxTuple, deltaIn)
    maxTuple2 = flambda(minTuple)
    minTuple2 = flambda(maxTuple)
    rs2 = getParetoFrontFp3D('ecgTemplateFp3D', sys.argv[1]+'L', 'resultTmplFp3D', sys.argv[3], minTuple2, maxTuple2, deltaIn)
    boxPareto = computeIntersect3D(rs1, rs2, flambda)
    intersection += boxPareto
  return intersection


def pareto_3D_Intersection(ecg_name, numParams, formula_name1, formula_name2, min_tuple, max_tuple):
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

  # Definition of the n-dimensional space
  min_x, min_y, min_z = min_tuple
  max_x, max_y, max_z = max_tuple

  print sys.argv

  orac1 = OracleEpsSTLe(boundOnCount=int(sys.argv[2]),intvlEpsilon=1)
  orac1.from_file(nfile1, human_readable)

  orac2 = OracleEpsSTLe(boundOnCount=int(sys.argv[3]),intvlEpsilon=10)
  orac2.from_file(nfile2, human_readable)

  output_intersect = SearchIntersection3D(oracle1=orac1, oracle2=orac2,
                min_cornerx=min_x,
                min_cornery=min_y,
                min_cornerz=min_z,
                max_cornerx=max_x,
                max_cornery=max_y,
                max_cornerz=max_z,
                epsilon=EPS,
                delta=1.0/float(sys.argv[5]),
                max_step=10000,
                blocking=False,
                sleep=0,
                opt_level=int(sys.argv[4]),
                parallel=False,
                logging=False,
                simplify=True)
  return output_intersect

t0 = time.time()
min_tuple = (0.0,-1.0,-1.0)
max_tuple = (70.0,1.00,1.0)
(intersection, border, xspace, intersect_region) = pareto_3D_Intersection(str(sys.argv[1]), 3, 'ecgInterTemplateFn3D', 'ecgInterTemplateFp3D', min_tuple, max_tuple)
print "num intersection boxes:", len(intersection)
t1 = time.time()
print 'TRESIMP: Time taken for intersection pareto (1):', t1 - t0
rs1 = ResultSet(border=border, yup=intersection, ylow=intersect_region, xspace=xspace)
#rs1.plot_3D(opacity=0.1, fig_title='Intersection of pareto fronts', var_names=['p1','p2','p3'],clip=True)
rs1.to_file(sys.argv[1]+"_characterizeOnlyOne"+sys.argv[5]+".zip")
exit(0)

t0 = time.time()
fromTotalBox = getIntersectRegion([xspace])
t1 = time.time()
print 'TRESIMP: Time taken for full pareto (1):', t1 - t0
rs0 = copy.deepcopy(rs1)
rs0.border = []
rs0.xspace = xspace
rs0.yup    = fromTotalBox
rs0.ylow   = []
# rs0.plot_3D(opacity=0.1, fig_title='Intersection of pareto fronts', var_names=['p1','p2','p3'],clip=True)
rs0.to_file(sys.argv[1]+"_0parInBoxAdjustedVolume.zip")


print 'bef (intersect_region):', len(intersect_region)
intersect_region = filter_dup_box(intersect_region, intersect_region)
print 'Regions containing an intersection. length = ', len(intersect_region)
ci = 0
for box in intersect_region:
  print ci,'--->',box, 'vol:', box.volume()
  ci += 1

t0 = time.time()
fromIntersectRegion = getIntersectRegion(intersect_region)
t1 = time.time()
print 'TRESIMP: Time taken for full pareto in intersect_region (2):', t1 - t0
rs2 = copy.deepcopy(rs1)
rs2.yup  = fromIntersectRegion
rs2.ylow = intersect_region
rs2.to_file(sys.argv[1]+"_2parInBoxAdjustedVolume.zip")
# rs2.plot_3D(opacity=0.1, fig_title='Intersection of pareto fronts', var_names=['p1','p2','p3'],clip=True)

print 'bef border:', len(border)
borderFilt = filter_dup_box(border, intersect_region)
print 'Regions in the border (after filter). length = ', len(borderFilt)
ci = 0
for box in borderFilt:
  print ci,'--->',box, 'vol:', box.volume()
  ci += 1

t0 = time.time()
fromBorderFilt = getIntersectRegion(borderFilt)
t1 = time.time()
print 'TRESIMP: Time taken for full pareto in border not in intersect_region (3):', t1 - t0
rs3 = copy.deepcopy(rs1)
rs3.yup  = fromBorderFilt
rs3.ylow = borderFilt
rs3.to_file(sys.argv[1]+'_3parInBoxAdjustedVolume'+".zip")
# rs3.plot_3D(opacity=0.1, fig_title='Intersection of pareto fronts', var_names=['p1','p2','p3'],clip=True)
exit(0)
t0 = time.time()
fromBorderFull = getIntersectRegion(border)
t1 = time.time()
print 'TRESIMP: Time taken for full pareto in border total (4):', t1 - t0
rs4 = copy.deepcopy(rs1)
rs4.yup  = fromBorderFull
rs4.ylow = border
rs4.to_file(sys.argv[1]+'_4parInBoxAdjustedVolume'+".zip")
# rs4.plot_3D(opacity=0.1, fig_title='Intersection of pareto fronts', var_names=['p1','p2','p3'],clip=True)