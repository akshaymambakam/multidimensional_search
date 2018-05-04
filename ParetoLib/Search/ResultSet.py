import __builtin__
import time
import pickle
from itertools import chain, combinations_with_replacement, product
from multiprocessing import Pool, cpu_count

import matplotlib.pyplot as plt

from ParetoLib.Geometry.Rectangle import *


# p = Pool(cpu_count())

class ResultSet:
    def __init__(self, border=list(), ylow=list(), yup=list(), xspace=Rectangle()):
        # type: (ResultSet, list, list, list, Rectangle) -> None
        self.border = border
        self.ylow = ylow
        self.yup = yup
        self.xspace = xspace

        self.suffix_Yup = 'up'
        self.suffix_Ylow = 'low'
        self.suffix_Border = 'border'
        self.suffix_Space = 'space'

    # Printers
    def toStr(self):
        # type: (ResultSet) -> str
        # _string = "("
        # for i, data in enumerate(self.l):
        #    _string += str(data)
        #    if i != dim(self.l) - 1:
        #        _string += ", "
        # _string += ")"
        _string = "<"
        _string += str(self.yup)
        _string += ', '
        _string += str(self.ylow)
        _string += ', '
        _string += str(self.border)
        _string += ">"
        return _string

    def __repr__(self):
        # type: (ResultSet) -> str
        return self.toStr()

    def __str__(self):
        # type: (ResultSet) -> str
        return self.toStr()

    # Equality functions
    def __eq__(self, other):
        # type: (ResultSet) -> bool
        return (other.border == self.border) and \
               (other.ylow == self.ylow) and \
               (other.yup == self.yup) and \
               (other.xspace == self.xspace)

    def __ne__(self, other):
        # type: (ResultSet) -> bool
        return not self.__eq__(other)

    # Identity function (via hashing)
    def __hash__(self):
        # type: (ResultSet) -> int
        return hash((self.border, self.ylow, self.yup, self.xspace))

    # Vertex functions
    def verticesYup(self):
        # type: (ResultSet) -> set
        vertices = set()
        for rect in self.yup:
            vertices = vertices.union(set(rect.vertices()))
        return vertices

    def verticesYlow(self):
        # type: (ResultSet) -> set
        vertices = set()
        for rect in self.ylow:
            vertices = vertices.union(set(rect.vertices()))
        return vertices

    def verticesBorder(self):
        # type: (ResultSet) -> set
        vertices = set()
        for rect in self.border:
            vertices = vertices.union(set(rect.vertices()))
        return vertices

    def vertices(self):
        # type: (ResultSet) -> set
        vertices = self.verticesYup()
        vertices = vertices.union(self.verticesYlow())
        vertices = vertices.union(self.verticesBorder())
        return vertices

    # Volume functions
    def _overlappingVolume(self, pairs_of_rect):
        # type: (ResultSet, list) -> float
        # remove pairs (recti, recti) from previous list
        pairs_of_rect_filt = [pair for pair in pairs_of_rect if pair[0] != pair[1]]
        overlapping_rect = [r1.intersection(r2) for (r1, r2) in pairs_of_rect_filt]
        # vol_overlapping_rect = p.map(Rectangle.volume, overlapping_rect)
        vol_overlapping_rect = [rect.volume() for rect in overlapping_rect]
        return sum(vol_overlapping_rect)
        # vol_overlapping_rect = p.map_async(volume, overlapping_rect)
        # vol_overlapping_rect.wait()
        # return sum(vol_overlapping_rect.get())

    def overlappingVolumeYup(self):
        # type: (ResultSet) -> float
        # self.yup = [rect1, rect2,..., rectn]
        # pairs_of_rect = [(rect1, rect1), (rect1, rect2),..., (rectn, rectn)]
        pairs_of_rect = list(combinations_with_replacement(self.yup, 2))
        # pairs_of_rect = list(product(self.yup, 2))
        return self._overlappingVolume(pairs_of_rect)

    def overlappingVolumeYlow(self):
        # type: (ResultSet) -> float
        # self.ylow = [rect1, rect2,..., rectn]
        # pairs_of_rect = [(rect1, rect1), (rect1, rect2),..., (rectn, rectn)]
        pairs_of_rect = list(combinations_with_replacement(self.ylow, 2))
        # pairs_of_rect = list(product(self.ylow, 2))
        return self._overlappingVolume(pairs_of_rect)

    def overlappingVolumeBorder(self):
        # type: (ResultSet) -> float
        # self.border = [rect1, rect2,..., rectn]
        # pairs_of_rect = [(rect1, rect1), (rect1, rect2),..., (rectn, rectn)]
        pairs_of_rect = list(combinations_with_replacement(self.border, 2))
        # pairs_of_rect = list(product(self.border, 2))
        return self._overlappingVolume(pairs_of_rect)

    def volumeYup(self):
        # type: (ResultSet) -> float
        # vol_list = p.map(Rectangle.volume, self.yup)
        vol_list = [rect.volume() for rect in self.yup]
        return sum(vol_list)
        # return sum(vol_list) - self.overlappingVolumeYup()
        # vol_list = p.map_async(volume, self.yup)
        # vol_list.wait()
        # return sum(vol_list.get())

    def volumeYlow(self):
        # type: (ResultSet) -> float
        # vol_list = p.map(Rectangle.volume, self.ylow)
        vol_list = [rect.volume() for rect in self.ylow]
        return sum(vol_list)
        # return sum(vol_list) - self.overlappingVolumeYlow()
        # vol_list = p.map_async(volume, self.ylow)
        # vol_list.wait()
        # return sum(vol_list.get())

    def volumeBorder(self):
        # type: (ResultSet) -> float
        vol_total = self.xspace.volume()
        vol_ylow = self.volumeYlow()
        vol_yup = self.volumeYup()
        return vol_total - vol_ylow - vol_yup

    # By construction, overlapping of rectangles only happens in the boundary
    def volumeBorderExact(self):
        # type: (ResultSet) -> float
        # vol_list = p.map(Rectangle.volume, self.border)
        vol_list = [rect.volume() for rect in self.border]
        return sum(vol_list) - self.overlappingVolumeBorder()
        # vol_list = p.map_async(volume, self.border)
        # vol_overlapping = self.overlappingVolumeBorder()
        # vol_list.wait()
        # return sum(vol_list.get()) - vol_overlapping

    def volumeTotal(self):
        # type: (ResultSet) -> float
        vol_total = self.xspace.volume()
        return vol_total

    # By construction, overlapping of rectangles only happens in the boundary
    def volumeTotalExact(self):
        # type: (ResultSet) -> float
        # vol_list = p.map(Rectangle.volume, self.border)
        vol_total = self.volumeYlow() + self.volumeYup() + self.volumeBorder()
        return vol_total

    def volumeReport(self):
        # type: (ResultSet) -> str
        vol_report = ('Volume report (Ylow, Yup, Border, Total): (%s, %s, %s, %s)\n'
                      % (
                          str(self.volumeYlow()), str(self.volumeYup()), str(self.volumeBorder()),
                          str(self.volumeTotal())))
        return vol_report

    # Membership functions
    def __contains__(self, xpoint):
        # type: (ResultSet, tuple) -> bool
        # xpoint is inside the upper/lower closure or in the border
        return self.memberBorder(xpoint) or \
               self.memberYlow(xpoint) or \
               self.memberYup(xpoint)

    def memberYup(self, xpoint):
        # type: (ResultSet, tuple) -> bool
        isMember = False
        for rect in self.yup:
            isMember = isMember or (xpoint in rect)
        return isMember

    def memberYlow(self, xpoint):
        # type: (ResultSet, tuple) -> bool
        isMember = False
        for rect in self.ylow:
            isMember = isMember or (xpoint in rect)
        return isMember

    def memberBorder(self, xpoint):
        # type: (ResultSet, tuple) -> bool
        isMember = False
        for rect in self.border:
            isMember = isMember or (xpoint in rect)
        return isMember

    def memberSpace(self, xpoint):
        # type: (ResultSet, tuple) -> bool
        return xpoint in self.xspace

    # Points of closure
    def getPointsYup(self, n):
        # type: (ResultSet, int) -> list
        m = n / len(self.yup)
        m = 1 if m < 1 else m
        point_list = [rect.getPoints(m) for rect in self.yup]
        # Flatten list
        # Before
        # point_list = [ [] , [], ..., [] ]
        # After
        # point_list = [ ... ]
        merged = list(chain.from_iterable(point_list))
        return merged

    def getPointsYlow(self, n):
        # type: (ResultSet, int) -> list
        m = n / len(self.ylow)
        m = 1 if m < 1 else m
        point_list = [rect.getPoints(m) for rect in self.ylow]
        merged = list(chain.from_iterable(point_list))
        return merged

    def getPointsBorder(self, n):
        # type: (ResultSet, int) -> list
        m = n / len(self.border)
        m = 1 if m < 1 else m
        point_list = [rect.getPoints(m) for rect in self.border]
        merged = list(chain.from_iterable(point_list))
        return merged

    def getPointsSpace(self, n):
        return self.xspace.getPoints(n)

    # MatPlot Graphics
    def toMatPlotYup2D(self, xaxe=0, yaxe=1, opacity=1.0):
        # type: (ResultSet, int, int, float) -> list
        patches = [rect.toMatplot2D('green', xaxe, yaxe, opacity) for rect in self.yup]
        return patches

    def toMatPlotYlow2D(self, xaxe=0, yaxe=1, opacity=1.0):
        # type: (ResultSet, int, int, float) -> list
        patches = [rect.toMatplot2D('red', xaxe, yaxe, opacity) for rect in self.ylow]
        return patches

    def toMatPlotBorder2D(self, xaxe=0, yaxe=1, opacity=1.0):
        # type: (ResultSet, int, int, float) -> list
        patches = [rect.toMatplot2D('blue', xaxe, yaxe, opacity) for rect in self.border]
        return patches

    def toMatPlot2D(self,
                    filename='',
                    xaxe=0,
                    yaxe=1,
                    targetx=list(),
                    targety=list(),
                    blocking=False,
                    sec=0.0,
                    opacity=1.0):
        # type: (ResultSet, str, int, int, list, list, bool, float, float) -> plt
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111, aspect='equal')
        ax1.set_title('Approximation of the Pareto front (x,y): (' + str(xaxe) + ', ' + str(yaxe) + ')')

        pathpatch_yup = self.toMatPlotYup2D(xaxe, yaxe, opacity)
        pathpatch_ylow = self.toMatPlotYlow2D(xaxe, yaxe, opacity)
        pathpatch_border = self.toMatPlotBorder2D(xaxe, yaxe, opacity)

        pathpatch = pathpatch_yup
        pathpatch += pathpatch_ylow
        pathpatch += pathpatch_border

        for pathpatch_i in pathpatch:
            ax1.add_patch(pathpatch_i)
        ax1.autoscale_view()

        # Include the vertices of the rectangles of the ResultSet in the plotting
        # The inclusion of explicit points forces the autoscaling of the image
        rs_vertices = self.vertices()
        xs = [vi[0] for vi in rs_vertices]
        ys = [vi[1] for vi in rs_vertices]

        targetx += [__builtin__.min(xs), __builtin__.max(xs)]
        targety += [__builtin__.min(ys), __builtin__.max(ys)]

        plt.plot(targetx, targety, 'kp')
        plt.autoscale()
        plt.show(block=blocking)
        time.sleep(sec)

        if filename != '':
            fig1.savefig(filename, dpi=90, bbox_inches='tight')

        plt.close()
        return plt

    def toMatPlotYup3D(self, xaxe=0, yaxe=1, zaxe=2, opacity=1.0):
        # type: (ResultSet, int, int, int, float) -> list
        faces = [rect.toMatplot3D('green', xaxe, yaxe, zaxe, opacity) for rect in self.yup]
        return faces

    def toMatPlotYlow3D(self, xaxe=0, yaxe=1, zaxe=2, opacity=1.0):
        # type: (ResultSet, int, int, int, float) -> list
        faces = [rect.toMatplot3D('red', xaxe, yaxe, zaxe, opacity) for rect in self.ylow]
        return faces

    def toMatPlotBorder3D(self, xaxe=0, yaxe=1, zaxe=2, opacity=1.0):
        # type: (ResultSet, int, int, int, float) -> list
        faces = [rect.toMatplot3D('blue', xaxe, yaxe, zaxe, opacity) for rect in self.border]
        return faces

    def toMatPlot3D(self,
                    filename='',
                    xaxe=0,
                    yaxe=1,
                    zaxe=2,
                    targetx=list(),
                    targety=list(),
                    targetz=list(),
                    blocking=False,
                    sec=0.0,
                    opacity=1.0):
        # type: (ResultSet, str, int, int, int, list, list, list, bool, float, float) -> plt
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111, aspect='equal', projection='3d')
        ax1.set_title('Approximation of the Pareto front (x,y,z): ('
                      + str(xaxe) + ', ' + str(yaxe) + ', ' + str(zaxe) + ')')

        faces_yup = self.toMatPlotYup3D(xaxe, yaxe, zaxe, opacity)
        faces_ylow = self.toMatPlotYlow3D(xaxe, yaxe, zaxe, opacity)
        faces_border = self.toMatPlotBorder3D(xaxe, yaxe, zaxe, opacity)

        faces = faces_yup
        faces += faces_ylow
        faces += faces_border

        for faces_i in faces:
            ax1.add_collection3d(faces_i)

        # Include the vertices of the rectangles of the ResultSet in the plotting
        # The inclusion of explicit points forces the autoscaling of the image
        rs_vertices = self.vertices()
        xs = [vi[0] for vi in rs_vertices]
        ys = [vi[1] for vi in rs_vertices]
        zs = [vi[2] for vi in rs_vertices]

        targetx += [__builtin__.min(xs), __builtin__.max(xs)]
        targety += [__builtin__.min(ys), __builtin__.max(ys)]
        targetz += [__builtin__.min(zs), __builtin__.max(zs)]

        ax1.scatter(targetx, targety, targetz, c='k')
        # ax1.autoscale_view()
        # ax1.autoscale(enable=True, tight=True)

        plt.show(block=blocking)
        if sec > 0:
            time.sleep(sec)
        if filename != '':
            fig1.savefig(filename, dpi=90, bbox_inches='tight')
        plt.close()
        return plt

    # Saving/loading results
    def toFileYup(self, f):
        # type: (ResultSet, str) -> None
        with open(f, 'wb') as output:
            for rect in self.yup:
                pickle.dump(rect, output, pickle.HIGHEST_PROTOCOL)

    def toFileYlow(self, f):
        # type: (ResultSet, str) -> None
        with open(f, 'wb') as output:
            for rect in self.ylow:
                pickle.dump(rect, output, pickle.HIGHEST_PROTOCOL)

    def toFileBorder(self, f):
        # type: (ResultSet, str) -> None
        with open(f, 'wb') as output:
            for rect in self.border:
                pickle.dump(rect, output, pickle.HIGHEST_PROTOCOL)

    def toFileSpace(self, f):
        # type: (ResultSet, str) -> None
        with open(f, 'wb') as output:
            pickle.dump(self.xspace, output, pickle.HIGHEST_PROTOCOL)

    def toFile(self, f):
        # type: (ResultSet, str) -> None
        self.toFileYup(f + self.suffix_Yup)
        self.toFileYlow(f + self.suffix_Ylow)
        self.toFileBorder(f + self.suffix_Border)
        self.toFileSpace(f + self.suffix_Space)

    def fromFileYup(self, f):
        # type: (ResultSet, str) -> None
        self.yup = set()
        with open(f, 'rb') as inputfile:
            self.yup = pickle.load(inputfile)

    def fromFileYlow(self, f):
        # type: (ResultSet, str) -> None
        self.ylow = set()
        with open(f, 'rb') as inputfile:
            self.ylow = pickle.load(inputfile)

    def fromFileBorder(self, f):
        # type: (ResultSet, str) -> None
        self.border = set()
        with open(f, 'rb') as inputfile:
            self.border = pickle.load(inputfile)

    def fromFileSpace(self, f):
        # type: (ResultSet, str) -> None
        self.xspace = Rectangle()
        with open(f, 'rb') as inputfile:
            self.xspace = pickle.load(inputfile)

    def fromFile(self, f):
        # type: (ResultSet, str) -> None
        self.fromFileYup(f + self.suffix_Yup)
        self.fromFileYlow(f + self.suffix_Ylow)
        self.fromFileBorder(f + self.suffix_Border)