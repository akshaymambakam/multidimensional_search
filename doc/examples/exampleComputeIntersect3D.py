from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import Search2D, Search3D, EPS, DELTA, STEPS
from ParetoLib.Search.ResultSet import ResultSet
from ParetoLib.Geometry.Rectangle import Rectangle

import sys, os
import numpy as np
from scipy.interpolate import Rbf, InterpolatedUnivariateSpline
import matplotlib.pyplot as plt
import copy

rs1 = ResultSet()
rs1.from_file(sys.argv[1]+".zip")

##
rs2 = ResultSet()
rs2.from_file(sys.argv[2]+".zip")

rs1 = copy.deepcopy(rs1)
rs1.scale(f=lambda x: (x[0], x[1], -x[2]))

rs2 = copy.deepcopy(rs2)
rs2.scale(f=lambda x: (70.0-x[0], -x[1], x[2]))

'''
rs1.plot_2D_light(xaxe=0, yaxe=1)
rs1.plot_2D_light(xaxe=1, yaxe=2)
rs1.plot_2D_light(xaxe=0, yaxe=2)
rs2.plot_2D_light(xaxe=0, yaxe=1)
rs2.plot_2D_light(xaxe=1, yaxe=2)
rs2.plot_2D_light(xaxe=0, yaxe=2)
'''

rsOut = copy.deepcopy(rs1)
rsOut.yup = []

print len(rs1.yup)
print len(rs2.yup)
c = 0
for rect1 in rs1.yup:
	for rect2 in rs2.yup:
		rect1c = copy.deepcopy(rect1)
		rect2c = copy.deepcopy(rect2)
		c += 1
		#print c
		if rect1c.overlaps(rect2c):
			rectSect = rect1c.intersection(rect2c)
			rsOut.yup.append(rectSect)

print '------------------------------'

print len(rsOut.yup)
print rsOut.yup
rsOut.xspace = Rectangle((0.0,0.0,0.0), (70.0,1.00,1.00))
rsOut.ylow = []
rsOut.border = []
rsOut.plot_3D_light(fig_title='Intersection of pareto fronts', var_names=['p1','p2','p3'])
rsOut.plot_2D_light(xaxe=0, yaxe=1, fig_title =  'Projection on (p1,p2) of intersection', var_names=['p1','p2','p3'])
rsOut.plot_2D_light(xaxe=1, yaxe=2, fig_title =  'Projection on (p2,p3) of intersection', var_names=['p1','p2','p3'])
rsOut.plot_2D_light(xaxe=0, yaxe=2, fig_title =  'Projection on (p1,p3) of intersection', var_names=['p1','p2','p3'])
exit(0)

list1_1 = []
list1_2 = []
list2_1 = []
list2_2 = []

rs1 = sorted(rs1.get_points_pareto(), key=lambda x: x[0])
rs2 = sorted(rs2.get_points_pareto(), key=lambda x: 70-x[0])

for (x,y) in rs1:
	list1_1.append(x)
	list1_2.append(y)
for (x,y) in rs2:
	list2_1.append(70-x)
	list2_2.append(-y)

plt.plot(list1_1, list1_2, 'b', label='min fn')
plt.plot(list2_1, list2_2, 'g', label='min fp')
plt.xlabel('duration parameter')
plt.ylabel('range parameter')
plt.title('Intersection of pareto fronts.')
plt.legend()
plt.show()