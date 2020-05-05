from ParetoLib.Oracle.OracleEpsSTLe import OracleEpsSTLe
from ParetoLib.Search.Search import Search3D, EPS, DELTA, STEPS
from ParetoLib.Search.ResultSet import ResultSet

import sys, os
EPS = 0.0001
DELTA = 0.01
#STEPS = 100

globalMinTuple = (16.40625, 0.125, -1.0)
globalMaxTuple = (70, 0.330078125, 0.125)



if len(sys.argv) <= 5:
    print 'Need 4 args: STLtemplateName, ecgName, resultFile, bound on num_fn'
    exit(-1)

def getParetoFrontFn3D(templateName, ecgName, resultFile, bound, minTuple, maxTuple, deltaIn):
    # File containing the definition of the Oracle
    nfile = './ecgLearn.txt'
    human_readable = True

    # Copy the template file to a scratch file.
    stl_file   = open('./'+templateName+'.stl')
    stl_string = stl_file.read()
    stl_file.close()


    # Write the template formula into a scratch file.
    fn_scratch = open('scratchFn.stl', 'w')
    fn_scratch.write(stl_string)
    fn_scratch.close()

    controlFile = open('ecgLearn.txt', 'w')
    controlText = ''
    controlLines = []
    print >>controlFile, './scratchFn.stl'
    print >>controlFile, './'+ecgName+'.csv'
    print >>controlFile, './ecgLearn3D.param'

    controlFile.close()

    min_x, min_y, min_z = minTuple
    max_x, max_y, max_z = maxTuple

    oracle = OracleEpsSTLe(boundOnCount = int(bound))
    oracle.from_file(nfile, human_readable)
    rs = Search3D(ora=oracle,
                min_cornerx=min_x,
                min_cornery=min_y,
                min_cornerz=min_z,
                max_cornerx=max_x,
                max_cornery=max_y,
                max_cornerz=max_z,
                epsilon=EPS,
                delta=deltaIn,
                max_step=100,
                blocking=False,
                sleep=0,
                opt_level=0,
                parallel=False,
                logging=False,
                simplify=True)
    rs.to_file(sys.argv[3]+".zip")
    return rs

def main():
    getParetoFrontFn3D(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], globalMinTuple, globalMaxTuple, DELTA)

if __name__ == "__main__":
    main()