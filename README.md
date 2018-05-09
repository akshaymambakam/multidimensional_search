# ParetoLib
**Multidimensional Pareto Boundary Learning Library for Python**

This library implements an algorithm for learning the boundary between an 
upward-closed set *X1* and its downward-closed component *X2* (i.e., *X=X1+X2*). 
Generally, the library supports spaces *X*  of dimension N.

The algorithm selects sampling points *x=(x1,x2,...,xN)* for which it submits membership queries 'is *x* in *X1*?' 
to an external *Oracle*.
Based on the *Oracle* answers and relying on monotonicity, the algorithm constructs 
an approximation of the boundary, called the Pareto front.

The algorithm generalizes binary search on the continuum from one-dimensional 
(and linearly-ordered) domains to multi-dimensional (and partially-ordered) ones. 

Applications include the approximation of Pareto fronts in multi-criteria optimization 
and parameter synthesis for predicates where the influence of parameters is monotone.
This library is based on the work-in-progress paper [1]. 

[1] [Learning Monotone Partitions of Partially-Ordered Domains (Work in Progress) 2017.〈hal-01556243〉] (https://hal.archives-ouvertes.fr/hal-01556243/)

## Installation

This library requires Python 2.7.9. The dependencies are listed in requirements.txt. 
If you have the python tool 'pip' installed, then you can run the following command for
installing the depencencies:

$ pip install -r requirements.txt

Afterwards you need to run:

$ python setup.py build

$ python setup.py install

for installing the library. In order to run all the tests, you must execute:

$ python setup.py test

or

$ cd Tests

$ pytest

from the root of the project folder.


For users that don’t have write permission to the global site-packages directory or 
do not want to install our library into it, Python enables the selection of the target 
installation folder with a simple option:

$ pip install -r requirements.txt --user

$ python setup.py build

$ python setup.py install --user

In Unix/Mac OS X environments:, the structure of the installation folders will be the following:

|Type of file |  Installation directory|
|------------ | --------------------------|
| modules | userbase/lib/pythonX.Y/site-packages |
| scripts | userbase/bin |
| data | userbase |
| C headers | userbase/include/pythonX.Y/distname |

And here are the values used on Windows:

| Type of file |  Installation directory |
|------------ | --------------------------|
| modules | userbase\PythonXY\site-packages |
| scripts | userbase\Scripts |
| data | userbase |
| C headers | userbase\PythonXY\Include\distname |

The advantage of using this scheme compared to the other ones described in [2] is that the 
user site-packages directory is under normal conditions always included in sys.path, which 
means that there is no additional step to perform after running the setup.py script to 
finalize the installation.

[2] Installing Python Modules (Legacy version) (https://docs.python.org/2/install/)

## Running

### Definition of the Oracle
The learning algorithm requires the existence of an external *Oracle* that guides 
the multidimensional search.
The *Oracle* determines the membership of a point *x=(x1,x2,...,xN)* to any of 
the two closures (*X1* or *X2*). 
The complete space is denoted by *X = X1 + X2*.

Our library supports two kind of *Oracles* for inferring the Pareto's front
and learning the membership of a point *x* to any of the two closures. 
The first *Oracle*, named *OracleFunction*, defines the membership of point *x*
to the closure *X1* based on polynomial constraints.
For instance, *x1 = x2* may define the boundary. Every point *x* having the coordinates
*x1 > x2* will belong to *X1*, while every point *x* having *x1 < x2* will belong to *X2*


The second *Oracle*, named *OraclePoint*, defines the membership of point *x*
to the closure *X1* based on a cloud of points. For instance, next image shows a dense
cloud of points in *X1* (dark side).

![alt text][cloudpoints]

The Pareto front is abbreviated by the following image, which only shows the points in the 
frontier. The Pareto front is obtained by a NDTree [3].

![alt text][paretofront]

Finally, the last image shows the partitioning that is learnt by our algorithm thanks to
the *Oracle* guidance. The green side corresponds to *X1* and the red side corresponds 
to *X2*. A gap in blue may appear between the two closures, which corresponds to the border 
and can be set arbitrarily small depending on the accuracy required by the user.

![alt text][multidim_search]


Samples of *OracleFunction* and *OraclePoint* definitions can be found in 
Tests/Oracle/Oracle* and Tests/Search/Oracle* folders.

[cloudpoints]: https://gricad-gitlab.univ-grenoble-alpes.fr/requenoj/multidimensional_search/blob/master/doc/image/cloud_points.png "Cloud of points"
[paretofront]: https://gricad-gitlab.univ-grenoble-alpes.fr/requenoj/multidimensional_search/blob/master/doc/image/pareto_front.png "Pareto front"
[multidim_search]: https://gricad-gitlab.univ-grenoble-alpes.fr/requenoj/multidimensional_search/blob/master/doc/image/multidim_search.png "Upper and lower closures"

[3] [ND-Tree-based update: a Fast Algorithm for the Dynamic Non-Dominance Problem] (https://ieeexplore.ieee.org/document/8274915/)

### Running the multidimensional search
The core of the library is the algorithm implementing the multidimensional search of the Pareto boundary.
It is implemented by the function:
 
ParetoLib.Search.Search.multidim_search(xspace,
                              oracle,
                              epsilon=EPSILON,
                              delta=DELTA,
                              verbose=False,
                              blocking=False,
                              sleep=0)

which takes as input the following parameters:
* xspace: the N-dimensional space that contains the upper and lower closures.
* oracle: the external knowledge repository that guides the learning process.
* epsilon: error representing the maximum distance between a point 'x' of the 
space and a point 'y' of the Pareto front.
* delta: error representing the maximum area/volume contained in the border
 that separates the upper and lower closures.
* verbose: boolean that specifies if the algorithm must print traces for
debugging options.
* blocking: boolean that specifies if the learning algorithm musts plot 
intermediate results in 2D/3D graphics.
* sleep: time in seconds that the intermediate 2D/3D graphic must be shown in the screen.
                    
As a result, the function returns an object of the class *ResultSet*. 
*Search2D*, *Search3D* and *SearchND* functions are wrappers that simplify 
and automatize the calling to the multidimensional search for *OracleFunction* and *OraclePoint* oracles.
A set of running examples for 2D, 3D and ND can be found in Test/test_Search.py.

```python
from ParetoLib.Oracle.OracleFunction import *
from ParetoLib.Search.Search import *

# File containing the definition of the Oracle
nfile='Tests/Search/OracleFunction/2D/test0.txt'
human_readable=True

# Definition of the n-dimensional space
min_x, min_y = (0.0, 0.0)
max_x, max_y = (1.0, 1.0)

oracle = OracleFunction()
oracle.fromFile(nfile, human_readable)
rs = Search2D(ora=oracle,
              min_cornerx=min_x,
              min_cornery=min_y,
              max_cornerx=max_x,
              max_cornery=max_y,
              epsilon=EPS,
              delta=DELTA,
              max_step=STEPS,
              blocking=False,
              sleep=0)
```                          

### Saving and plotting the results
The result of the learning process is saved in an object of the *ResultSet* class.
This object is a data structure composed of three elements: the upper closure (*X1*), the
lower closure (*X2*), and the gap between X1 and X2 representing the precision error of the
learning process. 
The size of this gap depends on the accuracy of the learning process, which can be tuned by 
the EPSILON and DELTA parameters during the invocation of the learning method.

The ResultSet class provides functions for:
- Testing the membership of a new point *y* to any of the closures.
- Plotting 2D and 3D spaces
- Exporting/Importing the results to text and binary files. 


