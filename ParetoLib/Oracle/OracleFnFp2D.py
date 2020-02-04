import io, os

import ParetoLib.Oracle as RootOracle
from ParetoLib.Oracle.Oracle import Oracle
from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.Search.Search import SearchIntersection2D, Search2D, EPS, DELTA, STEPS


class OracleFnFp2D(Oracle):
    def __init__(self, scratchDir, ecgFile, min_tuple, max_tuple):
        # type: (Condition, str, str, str) -> None
        Oracle.__init__(self)
        self.runDir = scratchDir
        self.ecgFile = ecgFile
        self.min_tuple = min_tuple
        self.max_tuple = max_tuple
        nfile1 = self.runDir+'/ecgLearn1.txt'
        nfile2 = self.runDir+'/ecgLearn2.txt'
        #nfile1 = '../../Tests/Oracle/OracleFunction/2D/test1_1.txt'
        #nfile2 = '../../Tests/Oracle/OracleFunction/2D/test1_2.txt'
      
      	scratch_name1 = '/scratch_fn2D.stl'
    	scratch_name2 = '/scratch_fp2D.stl'
     	scratch_file1  = self.runDir + scratch_name1
    	scratch_file2  = self.runDir + scratch_name2

        paramFile = open(self.runDir+'/ecgLearn.param', 'w')
        for i in range(2):
          print >>paramFile, 'p'+str(i+1)
        paramFile.close()
      
        controlFile = open(nfile1, 'w')
        controlText = ''
        print >>controlFile, self.runDir+scratch_name1
        print >>controlFile, self.runDir+"/"+self.ecgFile
        print >>controlFile, self.runDir+'/ecgLearn.param'
      
        controlFile.close()
      
        controlFile = open(nfile2, 'w')
        controlText = ''
        print >>controlFile, self.runDir+scratch_name2
        print >>controlFile, self.runDir+"/"+self.ecgFile
        print >>controlFile, self.runDir+'/ecgLearn.param'

        controlFile.close()
      


    def member(self, point):
    	print 'Point Here:', point
    	print '------------------------------------'
    	nfile1 = self.runDir+'/ecgLearn1.txt'
        nfile2 = self.runDir+'/ecgLearn2.txt'

    	template_file1 = self.runDir + '/template_fn2D.stl'
    	template_file2 = self.runDir + '/template_fp2D.stl'

    	scratch_name1 = '/scratch_fn2D.stl'
    	scratch_name2 = '/scratch_fp2D.stl'
     	scratch_file1  = self.runDir + scratch_name1
    	scratch_file2  = self.runDir + scratch_name2

    	temp_file = open(template_file1, 'r')
    	temp_string = temp_file.read()
    	temp_string = temp_string.replace('num_fn',str(point[0]))
    	temp_file.close()
    	temp_file = open(scratch_file1, 'w')
    	temp_file.write(temp_string)
    	temp_file.close()

    	temp_file = open(template_file2, 'r')
    	temp_string = temp_file.read()
    	temp_string = temp_string.replace('num_fp',str(point[1]))
    	temp_file.close()
    	temp_file = open(scratch_file2, 'w')
    	temp_file.write(temp_string)
    	temp_file.close()

        temp_file = None

        '''
        human_readable = True
      
        # Definition of the n-dimensional space
        min_x, min_y = self.min_tuple
        max_x, max_y = self.max_tuple
      
        orac1 = OracleSTLeLib()
        orac1.from_file(nfile1, human_readable)
      
        orac2 = OracleSTLeLib()
        orac2.from_file(nfile2, human_readable)

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

        return_bool = len(output_intersect[0]) != 0
        orac1 = None
        orac2 = None
        output_intersect = None
        gc.collect()
        '''
        executePath = "/home/akshay/Documents/paretoDev/multidimensional_search/doc/examples/executeQuery2D.py"
        return_value = os.system("sudo python "+executePath+" "+nfile1+" "+nfile2)
        print return_value
        if return_value == 0:
            return_bool = True
        else:
            return_bool = False
        print 'return_bool:',return_bool
        return return_bool
        ''''
        # type: (Condition, tuple) -> Expr
        (x,y) = point
        if (x >= 1) and (y >= 8):
        	return True
        elif (x >= 4) and (y >= 4):
        	return True
        else:
        	return False
        '''
    def dim(self):
    	return 2