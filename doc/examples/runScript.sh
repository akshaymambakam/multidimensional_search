echo '123 opt=0'
sudo python exampleIntersect2Eps3D.py 123 1 2 0
echo '123 opt=1'
sudo python exampleIntersect2Eps3D.py 123 1 2 1
echo '221 opt=0'
sudo python exampleIntersect2Eps3D.py 221 1 2 0
echo '221 opt=1'
sudo python exampleIntersect2Eps3D.py 221 1 2 1
echo '100 opt=0'
sudo python exampleIntersect2Eps3D.py 100 33 33 0
echo '100 opt=1'
sudo python exampleIntersect2Eps3D.py 100 33 33 1
echo '100 opt=0 no intersection.'
sudo python exampleIntersect2Eps3D.py 100 0 33 0
echo '100 opt=1 no intersection'
sudo python exampleIntersect2Eps3D.py 100 0 33 1