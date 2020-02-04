import os,sys, io

# Assuming we are given a list of left closed and right open intervals.
def countEpsilonSeparated(intervalList, epsilon):
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
    (tBegin, tEnd) = intervalList[currentIndex]
    if(startOfTime < tBegin):
        startOfTime = tBegin
    i = currentIndex
    while i < len(intervalList) and (startOfTime + epsilon) >= intervalList[i][1]:
        i += 1
    return i, startOfTime + epsilon

print countEpsilonSeparated([(1, 2), (3, 5), (10, 11), (12, 14.1)], 2)