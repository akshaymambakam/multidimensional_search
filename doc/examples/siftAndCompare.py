import os
import sys
import math

# Allowing an error of 5 time units.
def findInList(findList, goldenList):
	count = 0
	for findN in findList:
		countOld = count
		for goldN in goldenList:
			if abs(findN - goldN) <= 1:
				count += 1
				break
		if countOld != count:
			zer = 1
			# print 'Could find:', findN
	return count

f1 = open('ecg_fiveT.txt','r')
oneList = []
twoList = []
for line in f1:
	(time, label) = line.split(' ')
	time =  int(time)
	label = int(label)
	if label == 1:
		oneList.append(time)
	elif label == 2:
		twoList.append(time)
print 'oneList len:', len(oneList)
print 'twoList len:', len(twoList)
f1.close()
f1 = open('ecg_5Test.txt','r')
findList = []
for line in f1:
	(time, label) = line.split(' ')
	time = int(time)
	label = int(label)
	if label == 1:
		findList.append(time)
print 'findList len:', len(findList)
print findInList(findList, oneList)
print findInList(oneList, findList)
print findInList(findList, twoList)