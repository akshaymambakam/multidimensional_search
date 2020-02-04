import ParetoLib.Oracle as RootOracle
from ParetoLib.Oracle.OracleSTLe import OracleSTLeLib
from ParetoLib.STLe.STLe import MAX_STLE_CALLS

import os

def countEpsilonSeparated(intervalList, epsilon):
    if len(intervalList) == 0:
        return 0
    startOfTime = 0
    cardinality = 0
    i = 0
    (beginOfEnd, end) = intervalList[-1]
    startOfTime = 0
    epsCoveringSize = 0
    currentIndex = 0
    while currentIndex < len(intervalList):
        oldStartOfTime = startOfTime
        (currentIndex, startOfTime) = moveTimeNeedleByEpsilon(intervalList, epsilon, currentIndex, startOfTime)
        epsCoveringSize += 1
    return epsCoveringSize

def moveTimeNeedleByEpsilon(intervalList, epsilon, currentIndex, startOfTime):
    if(startOfTime == intervalList[currentIndex][1]):
        return (currentIndex + 1, startOfTime)
    (tBegin, tEnd) = intervalList[currentIndex]
    if(startOfTime < tBegin):
        startOfTime = tBegin
    i = currentIndex
    while i < len(intervalList) and (startOfTime + epsilon) >= intervalList[i][1]:
        i += 1
    return i, startOfTime + epsilon

class OracleEpsSTLe(OracleSTLeLib):
    def __init__(self, boundOnCount, intvlEpsilon=5, stl_prop_file='', csv_signal_file='', stl_param_file=''):
        # type: (OracleEpsSTLe, str, str, str) -> None
        """
        Initialization of Oracle.
        OracleSTLeLib interacts directly with the C library of STLe via the C API that STLe exports.
        OracleSTLeLib should be usually faster than OracleSTLe
        This class is an extension of the STLe oracle.
		It is intended for computing the size of minimal epsilon covering.
        """

        OracleSTLeLib.__init__(self, stl_prop_file, csv_signal_file, stl_param_file)
        self.epsilon = intvlEpsilon
        self.bound   = boundOnCount

    def member(self, xpoint):
        # type: (OracleEpsSTLe, tuple) -> bool
        """
        See Oracle.member().
        """
        RootOracle.logger.debug('Running membership function')
        # Cleaning the cache of STLe after MAX_STLE_CALLS (i.e., 'gargage collector')
        if self.num_oracle_calls > MAX_STLE_CALLS:
            self.num_oracle_calls = 0
            self._clean_cache()

        # Replace parameters of the STL formula with current values in xpoint tuple
        val_stl_formula = self._replace_val_stl_formula(xpoint)
        # Invoke STLe for solving the STL formula for the current values for the parameters
        result = False

        self.num_oracle_calls = self.num_oracle_calls + 1

        epsSeparationSize = 0
        if(1):
            epsSeparationSize = self.eps_separate_stl_formula(val_stl_formula, self.epsilon)
        else:
            outContent = self.gen_result(val_stl_formula)
            # get the interval list.    
            intvlList = self.get_interval_list(outContent)
            # compute the count, compare and return.
        #print 'epsSeparationSize:', epsSeparationSize, 'bound:', self.bound
        return epsSeparationSize <= self.bound
        #return countEpsilonSeparated(intvlList, 1) < self.bound

    def get_interval_list(self, outContent):
        outLines = outContent.split('\n')
        intvlList = []
        seen = False
        intvlStart = 0
        for line in outLines:
            parts = line.split(' ')
            timeStamp = parts[0].strip()
            boolVal   = parts[1].strip()
            if seen:
                intvlEnd = float(timeStamp)
                intvlList.append((intvlStart, intvlEnd))
                seen     = False
            elif(boolVal == '1'):
                intvlStart = float(timeStamp)
                seen = True
        return intvlList

    def gen_result(self, val_stl_formula):
        outfname = 'quickEtdirty'
        # Run the property
        stle_path = '/home/akshay/Documents/examples/stle'
        stleCmd=stle_path+' '+self.csv_signal_file+' -f "'+val_stl_formula+'" -os 1 -osf g -osn "tub" > localmax_max.txt'
        os.system(stleCmd)
        
        # Read the output
        readFile = open('localmax_max.txt', 'r')
        fileContent = readFile.read()
        readFile.close()

        outContent = fileContent[fileContent.find('tub"')+4:fileContent.find('"tub points')]
        outContent = outContent.strip()

        return outContent