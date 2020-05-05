from ParetoLib.Search.ResultSet import ResultSet
import sys, os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import Rbf, InterpolatedUnivariateSpline
from ParetoLib.Geometry.Rectangle import Rectangle

def main():
    if (sys.argv[2] != '10'):
        rs1 = ResultSet()    
        rs1.from_file(sys.argv[1]+".zip")
    
    if(sys.argv[2] == '3'):
	    rs1.ylow = []
	    # rs1.yup = []
	    rs1.border = []
	    rs1.xspace = Rectangle((0.0,0.0,-1), (70.0,1.0,0.0))
	    rs1.plot_3D(opacity=1, fig_title='Intersection of Pareto fronts', var_names=['p1','p2','p3'],clip=True)
    elif (sys.argv[2] == '10'):
        rs1 = ResultSet()
        rs2 = ResultSet()
        rs1.from_file("discPareto100.zip")
        rs2.from_file("disc100Pareto100.zip")
        rs1.plot_2D_figs(rs2, opacity=0.5,fig_title='Pareto front', var_names=['num of false negatives','num of false positives'])
    else:
		rs1.plot_2D(fig_title='Pareto front', var_names=['num of false negatives','num of false positives'])

if __name__ == '__main__':
    main()