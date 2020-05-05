import os,sys

os.system('sudo python exampleIntersectND.py '+sys.argv[1]+' 0 '+'100 > enumresT_'+sys.argv[1]+'_100')
os.system('sudo python exampleIntersectND.py '+sys.argv[1]+' 0 '+'10 > enumresT_'+sys.argv[1]+'_10')
os.system('sudo python exampleIntersectND.py '+sys.argv[1]+' 0 '+'5 > enumresT_'+sys.argv[1]+'_5')

