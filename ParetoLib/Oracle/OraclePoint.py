import pickle

from ParetoLib.Oracle.NDTree import *

from ParetoLib.Oracle.Oracle import Oracle
# from ParetoLib.Oracle import vprint
from . import vprint


class OraclePoint(Oracle):
# class OraclePoint:
    # OraclePoint defines membership function based on a cloud of points that belongs to the closure.
    # OraclePoint saves a set of points in a NDTree
    def __init__(self, MAX_P=2, MIN_CH=2):
        # type: (OraclePoint, int, int) -> None
        #super(OraclePoint, self).__init__()
        Oracle.__init__(self)
        self.oracle = NDTree(MAX_P=MAX_P, MIN_CH=MIN_CH)

    # Printers
    def __repr__(self):
        # type: (OraclePoint) -> str
        return self.toStr()

    def __str__(self):
        # type: (OraclePoint) -> str
        return self.toStr()

    def toStr(self):
        # type: (OraclePoint) -> str
        return str(self.oracle)

    # Equality functions
    def __eq__(self, other):
        # type: (OraclePoint, OraclePoint) -> bool
        return (self.oracle == other.oracle)

    def __ne__(self, other):
        # type: (OraclePoint, OraclePoint) -> bool
        return not self.__eq__(other)

    # Identity function (via hashing)
    def __hash__(self):
        # type: (OraclePoint) -> int
        return hash((self.oracle))

    # Oracle operations
    def addPoint(self, p):
        # type: (OraclePoint, tuple) -> None
        self.oracle.updatePoint(p)

    def addPoints(self, setpoints):
        # type: (OraclePoint, set) -> None
        for point in setpoints:
            self.addPoint(point)

    def getPoints(self):
        # type: (OraclePoint) -> set
        return self.oracle.getPoints()

    def dim(self):
        # type: (OraclePoint) -> int
        return self.oracle.dim()

    # Membership functions
    def __contains__(self, p):
        # type: (OraclePoint, tuple) -> bool
        # set_points = self.getPoints()
        # return p in set_points
        return self.member(p)

    def member(self, p):
        # type: (OraclePoint, tuple) -> bool
        # Returns 'True' if p belongs to the set of points stored in the Pareto archive
        return p in self.getPoints()

    def membership(self):
        # type: (OraclePoint) -> function
        return lambda p: self.oracle.dominates(p)

    def dominates2(self, p):
        # type: (OraclePoint, tuple) -> bool
        # Returns 'True' if p dominates any point of the set of points stored in the Pareto archive
        #return any(greater_equal(p, point) for point in self.getPoints())
        # Returns 'True' if p is dominated by any point stored in the Pareto archive
        return any(less_equal(point, p) for point in self.points)

    def membership2(self):
        # type: (OraclePoint) -> function
        # return lambda p: self.member(p)
        return lambda p: self.dominates2(p)

    # Read/Write file functions
    def fromFile(self, fname='', human_readable=False):
        # type: (OraclePoint, str, bool) -> None
        assert (fname != ''), "Filename should not be null"

        mode = 'rb'
        finput = open(fname, mode)
        if human_readable:
            self.fromFileHumRead(finput)
        else:
            self.fromFileNonHumRead(finput)
        finput.close()

    def fromFileNonHumRead(self, finput=None):
        # type: (OraclePoint, BinaryIO) -> None
        assert (finput is not None), "File object should not be null"

        # Setting maximum recursion. It is required for the NDTree build
        # sys.getrecursionlimit()
        max_rec = 0x100000
        resource.setrlimit(resource.RLIMIT_STACK, [0x100 * max_rec, resource.RLIM_INFINITY])
        sys.setrecursionlimit(max_rec)

        self.oracle = pickle.load(finput)

    def fromFileHumRead(self, finput=None):
        # type: (OraclePoint, BinaryIO) -> None
        assert (finput is not None), "File object should not be null"

        def _line2tuple(inline):
            line = inline
            line = line.replace('(', '')
            line = line.replace(')', '')
            line = line.split(',')
            return tuple(float(pi) for pi in line)

        self.oracle = NDTree()

        point_list = (_line2tuple(line) for line in finput)
        #point_list = (self._line2tuple(line) for line in finput)

        #map(self.oracle.updatePoint, point_list)
        [self.oracle.updatePoint(point) for point in point_list]

    def fromFileHumRead2(self, finput=None):
        # type: (OraclePoint, BinaryIO) -> None
        assert (finput is not None), "File object should not be null"

        self.oracle = NDTree()
        i = 0
        for i, line in enumerate(finput):
            line = line.replace('(', '')
            line = line.replace(')', '')
            line = line.split(',')
            point = tuple(float(pi) for pi in line)
            vprint("Adding: ", i, point)
            self.oracle.updatePoint(point)
        vprint("numPoints: ", i)

    def toFile(self, fname='', append=False, human_readable=False):
        # type: (OraclePoint, str, bool, bool) -> None
        assert (fname != ''), "Filename should not be null"

        if append:
            mode = 'ab'
        else:
            mode = 'wb'

        foutput = open(fname, mode)
        if human_readable:
            self.toFileHumRead(foutput)
        else:
            self.toFileNonHumRead(foutput)
        foutput.close()

    def toFileNonHumRead(self, foutput=None):
        # type: (OraclePoint, BinaryIO) -> None
        assert (foutput is not None), "File object should not be null"

        # Setting maximum recursion. It is required for the NDTree build
        # sys.getrecursionlimit()
        max_rec = 0x100000
        resource.setrlimit(resource.RLIMIT_STACK, [0x100 * max_rec, resource.RLIM_INFINITY])
        sys.setrecursionlimit(max_rec)

        pickle.dump(self.oracle, foutput, pickle.HIGHEST_PROTOCOL)

    def toFileHumRead(self, foutput=None):
        # type: (OraclePoint, BinaryIO) -> None
        assert (foutput is not None), "File object should not be null"

        setPoints = self.getPoints()
        vprint("Set of points ")
        vprint(setPoints)
        for point in setPoints:
            foutput.write(str(point))
            foutput.write('\n')
