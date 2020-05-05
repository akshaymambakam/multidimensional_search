import os
import sys
fname1 = ''
fname2 = ''
interact1 = 0
interact2 = 0
def compare_stats(fname1,fname2):
	# Read the files
	readFile1 = open(fname1, 'r')
	readFile2 = open(fname2, 'r')
	lines1 = readFile1.readlines()
	lines2 = readFile2.readlines()
	minNumLines = 0
	if len(lines1) <= len(lines2):
		minNumLines = len(lines1)
	else:
		minNumLines = len(lines2)
	numList1 = []
	numList2 = []
	for line in lines1:
		(x1,x2) = line.split()
		numx1 = float(x1)
		numx2 = int(x2)
		if(numx2 == 1):
			numList1.append(numx1)
	for line in lines2:
		(x1,x2) = line.split()
		numx1 = float(x1)
		numx2 = int(x2)
		if(numx2 == 1):
			numList2.append(numx1)
	# Find 1 in 2
	numOfProposedDetections = len(numList1)
	numOfActualDetections = len(numList2)
	numOfFalsePositives = 0
	numOfFalseNegatives = 0
	for num1 in numList1:
		in2 = False
		minAbs = 100000
		absLim = 10
		nearestIn2 = 0
		for num2 in numList2:
			if(abs(num2 - num1) <= minAbs):
				minAbs = abs(num2-num1)
				nearestIn2 = num2
			if(abs(num2 - num1) <= absLim):
				in2 = True
		if in2 is False:
			numOfFalsePositives = numOfFalsePositives + 1
	# Find 2 in 1
	for num2 in numList2:
		in1 = False
		minAbs = 100000
		absLim = 10
		nearestIn1 = 0
		for num1 in numList1:
			if(abs(num2 - num1) <= minAbs):
				minAbs = abs(num2-num1)
				nearestIn1 = num1
			if(abs(num2 - num1) <= absLim):
				in1 = True
		if in1 is False:
			numOfFalseNegatives = numOfFalseNegatives + 1
	return (numOfFalseNegatives, numOfFalsePositives, numOfActualDetections)

def compare_interactive(fname1, fname2, interact1, interact2):
	print 'Comparing',fname1,'and',fname2
	# Read the files
	readFile1 = open(fname1, 'r')
	readFile2 = open(fname2, 'r')
	lines1 = readFile1.readlines()
	lines2 = readFile2.readlines()
	print len(lines1)
	print len(lines2)
	minNumLines = 0
	if len(lines1) <= len(lines2):
		minNumLines = len(lines1)
	else:
		minNumLines = len(lines2)
	numList1 = []
	numList2 = []
	for line in lines1:
		(x1,x2) = line.split()
		numx1 = float(x1)
		numx2 = int(x2)
		if(numx2 == 1):
			numList1.append(numx1)
	for line in lines2:
		(x1,x2) = line.split()
		numx1 = float(x1)
		numx2 = int(x2)
		if(numx2 == 1):
			numList2.append(numx1)
	# Find 1 in 2
	numOfProposedDetections = len(numList1)
	numOfActualDetections = len(numList2)
	numOfCorrectDetections = 0
	numOfFalsePositives = 0
	numOfFalseNegatives = 0
	for num1 in numList1:
		in2 = False
		minAbs = 100000
		absLim = 10
		nearestIn2 = 0
		for num2 in numList2:
			if(abs(num2 - num1) <= minAbs):
				minAbs = abs(num2-num1)
				nearestIn2 = num2
			if(abs(num2 - num1) <= absLim):
				in2 = True
		if in2 is False:
			numOfFalsePositives = numOfFalsePositives + 1
			print num1, 'has no match in list2'
			leftP  = min(num1,nearestIn2)
			rightP = max(num1,nearestIn2)
			plotString = 'gnuplot -e "x='+str(leftP - 200)+'; y='+str(rightP + 200)+'; plot1=\\"'+fname1+'\\"; '+'plot2=\\"'+fname2+'\\";" '+'ecgPlot.p'
			print plotString
			if interact1:
				os.system(plotString)
				raw_input("Press Enter to continue:")
		else:
			numOfCorrectDetections = numOfCorrectDetections + 1
	# Find 2 in 1
	print '\n\n'
	print 'Next chapter...'
	print '\n\n'
	for num2 in numList2:
		in1 = False
		minAbs = 100000
		absLim = 10
		nearestIn1 = 0
		for num1 in numList1:
			if(abs(num2 - num1) <= minAbs):
				minAbs = abs(num2-num1)
				nearestIn1 = num1
			if(abs(num2 - num1) <= absLim):
				in1 = True
		if in1 is False:
			numOfFalseNegatives = numOfFalseNegatives + 1
			print num2, 'has no match in list1'
			print 'Nearest value in list1 is', nearestIn1, 'with abs distance of ', minAbs
			leftP  = min(nearestIn1,num2)
			rightP = max(nearestIn1,num2)
			plotString = 'gnuplot -e "x='+str(leftP - 200)+'; y='+str(rightP + 200)+'; plot1=\\"'+fname1+'\\"; '+'plot2=\\"'+fname2+'\\";" '+'ecgPlot.p'
			print plotString
			if interact2:			
				os.system(plotString)
				raw_input("Press Enter to continue:")

	print 'Accuracy:',float(numOfCorrectDetections)/numOfActualDetections
	print 'numOfCorrectDetections:', numOfCorrectDetections
	print 'numOfFalseNegatives:', numOfFalseNegatives
	print 'numOfFalsePositives:', numOfFalsePositives
	print 'numOfProposedDetections:', numOfProposedDetections
	print 'numOfActualDetections:', numOfActualDetections