import sys,os

if len(sys.argv) != 5:
    print 'Enter 3 args: ecg_name, num_fn, num_fp, 1 for computing both paretos otherwise we run intersect algo.'

if int(sys.argv[4]) == 1:
    os.system('sudo python exampleStlFn3D.py ecgTemplateFn3D '+sys.argv[1]+'L resultTmplFn3D '+sys.argv[2])
    os.system('sudo python exampleStlFp3D.py ecgTemplateFp3D '+sys.argv[1]+'L resultTmplFp3D '+sys.argv[3])
    os.system('sudo python exampleComputeIntersect3D.py resultTmplFn3D resultTmplFp3D')
    os.system('cp resultTmplFn3D.zip ~/pareto'+sys.argv[1]+'/.')
    os.system('cp resultTmplFp3D.zip ~/pareto'+sys.argv[1]+'/.')
elif int(sys.argv[4]) == 2:
    rd = '~/pareto'+sys.argv[1]+'/'
    os.system('sudo python exampleComputeIntersect3D.py '+rd+'resultTmplFn3D '+rd+'resultTmplFp3D')
else:
    os.system('sudo python exampleIntersect2Eps3D.py '+sys.argv[1]+' '+sys.argv[2]+' '+sys.argv[3])
