import sys
from gen_formula import gen_formula, gen_label
from compare import compare_stats, compare_interactive

# Please note that all parameters values should be positive for the script to work.
(p1, p2, p3) = (15.3125, 0.765625, 0.3212890625)

if len(sys.argv) != 4:
    print 'Provide 3 arguments: stl pattern template file, ecgName, interactive'
    exit(0)

f = open(sys.argv[1])
stl_string = f.read()
f.close()

stl_string = stl_string.replace('p1', str(p1))
stl_string = stl_string.replace('p2', str(p2))
stl_string = stl_string.replace('p3', str(p3))

f = open('scratch.stl','w')
f.write(stl_string)
f.close()

gen_label('label', sys.argv[2]+'L.csv', 2)
gen_label('in', sys.argv[2]+'L.csv', 0)
gen_formula('temp', sys.argv[2]+'L.csv')

if sys.argv[3] == '1':
    compare_interactive('ecg_temp.txt', 'ecg_label.txt', 1, 1)
else:
    compare_interactive('ecg_temp.txt', 'ecg_label.txt', 0, 0)
