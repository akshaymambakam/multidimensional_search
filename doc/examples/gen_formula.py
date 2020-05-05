import os
import sys

def gen_formula(outName, csv_name):
	outfname = outName
	# Run the property
	stleCmd='./stle '+csv_name+' -ff scratch.stl -os 1 -osf g -osn "tub" > localmax_max.txt'
	os.system(stleCmd)
	# Read the output
	readFile = open('localmax_max.txt', 'r')
	fileContent = readFile.read()
	readFile.close()
	# write the output.
	outContent = fileContent[fileContent.find('tub"')+4:fileContent.find('"tub points')]
	outContent = outContent.strip()
	outFile = open("ecg_"+outfname+".txt", 'w')
	outFile.write(outContent)
	outFile.close()

def gen_label(outName, csv_name, label_num):
	outfname = outName
	# Run the property
	stleCmd='./stle '+csv_name+' -f x'+str(label_num)+' -os 1 -osf g -osn "tub" > localmax_max.txt'
	os.system(stleCmd)
	# Read the output
	readFile = open('localmax_max.txt', 'r')
	fileContent = readFile.read()
	readFile.close()
	# write the output.
	outContent = fileContent[fileContent.find('tub"')+4:fileContent.find('"tub points')]
	outContent = outContent.strip()
	outFile = open("ecg_"+outfname+".txt", 'w')
	outFile.write(outContent)
	outFile.close()

def gen_direct_formula(outName, csv_name, direct_formula):
	outfname = outName
	# Run the property
	of = open('scratch.stl','w')
	of.write(direct_formula)
	of.close()
	stleCmd='./stle '+csv_name+' -ff scratch.stl -os 1 -osf g -osn "tub" > localmax_max.txt'
	print stleCmd
	os.system(stleCmd)
	# Read the output
	readFile = open('localmax_max.txt', 'r')
	fileContent = readFile.read()
	readFile.close()
	# write the output.
	outContent = fileContent[fileContent.find('tub"')+4:fileContent.find('"tub points')]
	outContent = outContent.strip()
	outFile = open("ecg_"+outfname+".txt", 'w')
	outFile.write(outContent)
	outFile.close()

def gen_form_label(outName, csv_name, form_file):
	outfname = outName
	# Run the property
	stleCmd='./stle '+csv_name+' -ff '+form_file+' -os 1 -osf g -osn "tub" > localmax_max.txt'
	os.system(stleCmd)
	# Read the output
	readFile = open('localmax_max.txt', 'r')
	fileContent = readFile.read()
	readFile.close()
	# write the output.
	outContent = fileContent[fileContent.find('tub"')+4:fileContent.find('"tub points')]
	outContent = outContent.strip()
	outFile = open("ecg_"+outfname+".txt", 'w')
	outFile.write(outContent)
	outFile.close()	