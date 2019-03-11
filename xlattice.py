"""
xlattice version 2.0
Written by Ruiqi Chen (rchensix at stanford dot edu) and Lucas Zhou (zzh at stanford dot edu)
February 25, 2019
This module utilizes the networkx module to generate unit cell lattice structures

WARNING: This module is not compatible with older code that utilize xlattice 1.4 and below!

NEW IN 2.1
-Added flip method in Lattice class
-Added mirror method in Lattice class

NEW IN 2.0
-All lattice family generators have been moved to a separate module called latticeDatabase
-All future lattices are wrapped in Lattice class by default
-Added scale method in Lattice class
-Added applyDiameterDistribution static method and in Lattice class

NEW IN 1.4
-Fixed bug in diamond lattice family
-Added regular triangle lattice family
-Modified network_plot_3D to plot using equal aspect ratio (or close enough since it's not officially supported by MPlot3D) given extents

NEW IN 1.3
-Added double_snap_through_lattice type, a variant from sanp_through. This one has two layers of snap-through feature.
-Added diamond lattice family
-Added a summary of lattice as an index in the comment section

NEW IN 1.2
-Added Lattice class
    -tessellation function
    -automatically checks for periodicity and extracts faces
    -assumes rectangular cuboid currently
-Added translate function for NetworkX Graphs and Lattices
-Modified network_plot_3D to be compabitible with Lattice class
-Created new wrapper functions to wrap existing FCC, BCC, and snapThrough lattices in Lattice class
-Add DeprecationWarning to old lattice generator functions that don't wrap in Lattice class
-Add DeprecationWarning to print_to_file function (not used by dynautil anymore)
-Added regular hexagon lattice

NEW IN 1.1
-Additional BCC lattice type added

NEW IN 1.0
-Initial release

"""
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import math
import warnings
import copy

# This class builds upon a NetworkX graph and adds features for checking periodicity, 
# determining periodic face nodes, and various utility methods like translation and tessellation

class Lattice:
    def __init__(self, G, tol=1e-5):
        self.update(G, tol)

    def update(self, G, tol=1e-5):
        # update instance variable information
        self.G = G
        self.tol = tol
        self.periodicInfo = findPeriodicNodes(G, tol)
        self.xPeriodic = self.periodicInfo[0]
        self.yPeriodic = self.periodicInfo[1]
        self.zPeriodic = self.periodicInfo[2]
        self.xMinFace = self.periodicInfo[3]
        self.xMaxFace = self.periodicInfo[4]
        self.yMinFace = self.periodicInfo[5]
        self.yMaxFace = self.periodicInfo[6]
        self.zMinFace = self.periodicInfo[7]
        self.zMaxFace = self.periodicInfo[8]      
        self.isFullyPeriodic = self.periodicInfo[9]
        self.extents = self.periodicInfo[10]

    def tessellate(self, nX, nY, nZ, inPlace=True):
    # tessellates the current lattice in the x, y, and z directions into a nX*nY*nZ lattice
    # nI=1 means don't tessellate along direction I
    # nI must be < 0 for all directions I
    # new lattices are always added on the +x, +y, and +z faces
    # if inPlace is False, a newly tessellated copy of the original Lattice will be returned
    # otherwise, the Lattice will be modified in place
    # if mirror is True, every other unit cell will be mirror images (this guarantees tessellation even for non-symmetric unit cells)
        assert(nX > 0 and nY > 0 and nZ > 0)

        if not inPlace:
            originalG = self.G.copy() # keep copy of original graph to rebuild later

        def propagate(G, n, axis):
            maxNodeNumber = max(list(G))
            assert(axis == 0 or axis == 1 or axis == 2)
            for i in range(n):
                if i != 0:
                    # determine which face nodes will be renamed
                    if axis == 0:
                        face = self.xMinFace
                        periodic = self.xPeriodic
                    elif axis == 1:
                        face = self.yMinFace
                        periodic = self.yPeriodic
                    else:
                        face = self.zMinFace
                        periodic = self.zPeriodic
                    # create new graph, translate in direction of axis
                    translationDistance = i*(self.extents[2*axis + 1] - self.extents[2*axis])
                    if axis == 0:
                        newG = translate(self.G, translationDistance, 0, 0, inPlace=False)
                    elif axis == 1:
                        newG = translate(self.G, 0, translationDistance, 0, inPlace=False)
                    else:
                        newG = translate(self.G, 0, 0, translationDistance, inPlace=False)
                    # rename all nodes in newG
                    mapping = dict()
                    for node in list(newG):
                        if node in face:
                            mapping[node] = periodic[node] + (i-1)*maxNodeNumber
                        else:
                            mapping[node] = node + i*maxNodeNumber
                    nx.relabel.relabel_nodes(newG, mapping, copy=False)
                    # merge graphs G and newG
                    G = nx.algorithms.operators.binary.compose(G, newG)
            return G

        for axis in range(3):
            if axis == 0: nA = nX
            elif axis == 1: nA = nY
            else: nA = nZ
            G = self.G.copy()
            G = propagate(G, nA, axis)
            self.update(G, self.tol)

        if not inPlace:
            self.update(originalG, self.tol)
            return Lattice(G, self.tol)

    def translate(self, dx, dy, dz, inPlace=True):
        result = translate(self.G, dx, dy, dz, inPlace)
        if inPlace:
            xMin, xMax, yMin, yMax, zMin, zMax = self.extents
            self.extents = (xMin + dx, xMax + dx, yMin + dy, yMax + dy, zMin + dz, zMax + dz)
        if not inPlace:
            return Lattice(result, self.tol)

    def scale(self, mx, my=None, mz=None, inPlace=True):
        if my == None and mz == None:
            my = mx
            mz = mx
        assert(mx > 0 and my > 0 and mz > 0)
        if inPlace:
            G = self.G
        else:
            G = self.G.copy()
        for n in list(G):
            x, y, z = G.nodes[n]["pos"]
            G.nodes[n]["pos"] = (mx*x, my*y, mz*z)
        if inPlace:
            xMin, xMax, yMin, yMax, zMin, zMax = self.extents
            self.extents = (xMin*mx, xMax*mx, yMin*my, yMax*my, zMin*mz, zMax*mz)
        if not inPlace:
            return Lattice(G, self.tol)

    def flip(self, plane, inPlace=True):
        # options are:
        # plane == 0: mirror about YZ plane
        # plane == 1: mirror about XZ plane
        # plane == 2: mirror about XY plane
        assert(plane >= 0 and plane <= 2)
        if inPlace:
            G = self.G
        else:
            G = self.G.copy()
        for n in list(G):
            x, y, z = G.nodes[n]["pos"]
            if plane == 0:
                x = self.extents[1] + self.extents[0] - x
            elif plane == 1:
                y = self.extents[3] + self.extents[2] - y
            elif plane == 2:
                z = self.extents[5] + self.extents[4] - z
            G.nodes[n]["pos"] = (x, y, z)
        if not inPlace:
            return Lattice(G, self.tol)

    def mirror(self, plane, inPlace=True):
        assert(plane >= 0 and plane <= 2)
        if inPlace:
            G = self.G
        else:
            G = self.G.copy()
        # makes copy, performs flip, then merges the lattices together
        newLattice = self.flip(plane, inPlace=False)
        if plane == 0:
            newLattice.translate(self.extents[1] - self.extents[0], 0, 0)
            nodesNotToRename = newLattice.xMinFace
        elif plane == 1:
            newLattice.translate(0, self.extents[3] - self.extents[2], 0)
            nodesNotToRename = newLattice.yMinFace
        elif plane == 2:
            newLattice.translate(0, 0, self.extents[5] - self.extents[4])
            nodesNotToRename = newLattice.zMinFace
        newG = newLattice.G
        # merge graphs G and newG
        maxNodeNumber = max(list(newG))
        mapping = dict()
        i = 1
        for n in list(newG):
            if n not in nodesNotToRename:
                mapping[n] = maxNodeNumber + i
                i += 1
        nx.relabel.relabel_nodes(newG, mapping, copy=False)
        G = nx.algorithms.operators.binary.compose(G, newG)
        if inPlace:
            self.G = G
            self.update(G)
        if not inPlace:
            return Lattice(G, self.tol)

    def plot(self, elevation=30, azimuth=None):
        network_plot_3D(self.G, elevation, azimuth, self.extents)

    def applyDiameterDistribution(self, f, mode=1, inPlace=True):
        result = applyDiameterDistribution(self.G, f, mode, inPlace)
        if not inPlace:
            return Lattice(result, self.tol)

def applyDiameterDistribution(G, f, mode=1, inPlace=True):
    # mode 1 assumes diameter = f(x, y, z)
        # this assigns beams at (x, y, z) a diameter equal to f
    # mode 2 assumes diameter = f(azimuth, inclination)
        # this assigns beams with the same azimuth and/or inclination (in a spherical coordinate sense) with the same diameter
        # aximuth is measured CCW starting from x-axis
        # inclination is measured starting from z-axis
        # all angles should be in radians
        # see Wikipedia article on ISO convention of spherical coordinates
    isLattice = False
    if isinstance(G, Lattice):
        isLattice = True
        G = G.G
    if not inPlace:
        G = G.copy()
    for e in G.edges:
        n0 = e[0]
        n1 = e[1]
        x0, y0, z0 = G.nodes[n0]["pos"]
        x1, y1, z1 = G.nodes[n1]["pos"]
        if mode == 1:
            d = f((x0 + x1)/2, (y0 + y1)/2, (z0 + z1)/2)
        elif mode == 2:
            r = math.sqrt((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2)
            inclination = math.acos(abs(z1 - z0)/r)
            if z1 > z0:
                azimuth = math.atan2(y1 - y0, x1 - x0)
            else:
                azimuth = math.atan2(y0 - y1, x0 - x1)
            d = f(azimuth, inclination)
        G.edges[n0, n1]["diameter"] = d
    if not inPlace:
        if isLattice:
            return Lattice(G)
        else:
            return G

def translate(G, dx, dy, dz, inPlace=False):
    # translates all nodes in a networkx graph by (dx, dy, dz)
    if not inPlace:
        G = G.copy()
    for n in list(G):
        x, y, z = G.nodes[n]["pos"]
        G.nodes[n]["pos"] = (x + dx, y + dy, z + dz)
    if not inPlace:
        return G

def findPeriodicNodes(G, tol=1e-5):
    # Given a graph G representing a rectangular cuboid lattice, this function finds periodic nodes

    # these sets store all periodic nodes
    xMinFace = set()
    xMaxFace = set()
    yMinFace = set()
    yMaxFace = set()
    zMinFace = set()
    zMaxFace = set()

    # determine extents of the graph and which faces nodes are on
    minX = float("inf")
    maxX = float("-inf")
    minY = float("inf")
    maxY = float("-inf")
    minZ = float("inf")
    maxZ = float("-inf")
    for n in list(G): # an iterator would be more efficient but there seems to be compatibility issues between NetworkX 1.1 and 2.2
        x, y, z = G.nodes[n]["pos"] # position of current node n
        # find the extents
        # if extents are updated, the periodic dicts have to be cleared if out of tolerance
        if x < minX:
            if abs(x - minX) > tol:
                xMinFace.clear()
            minX = x
        if x > maxX:
            if abs(x - maxX) > tol:
                xMaxFace.clear()
            maxX = x
        if y < minY:
            if abs(y - minY) > tol:
                yMinFace.clear()
            minY = y
        if y > maxY:
            if abs(y - maxY) > tol:
                yMaxFace.clear()
            maxY = y            
        if z < minZ:
            if abs(z - minZ) > tol:
                zMinFace.clear()
            minZ = z            
        if z > maxZ:
            if abs(z - maxZ) > tol:                
                zMaxFace.clear()
            maxZ = z

        # check if current node is equal to one of the extents
        # if so, put into face set
        # note: corner and edge nodes can be in multiple sets
        if abs(x - minX) <= tol:
            xMinFace.add(n)
        if abs(x - maxX) <= tol:
            xMaxFace.add(n)
        if abs(y - minY) <= tol:
            yMinFace.add(n)
        if abs(y - maxY) <= tol:
            yMaxFace.add(n)
        if abs(z - minZ) <= tol:
            zMinFace.add(n)
        if abs(z - maxZ) <= tol:
            zMaxFace.add(n)

    fullyPeriodic = True
    # Look at opposing faces and match up nodes
    # Give a warning if a match cannot be found
    def matchFaceNodes(face1, face2, axis):
        # given two faces and axis (0-x, 1-y, 2-z), finds matching nodes with identical pos[i] where i is NOT axis
        periodic = dict() # two way dict that stores periodicity information
        axes = [0, 1, 2]
        axes.remove(axis) # only search for matches along these two axes
        for n1 in face1:
            for n2 in face2:
                if n2 not in periodic: # don't look at already assigned nodes
                    if abs(G.nodes[n1]["pos"][axes[0]] - G.nodes[n2]["pos"][axes[0]]) <= tol:
                        if abs(G.nodes[n1]["pos"][axes[1]] - G.nodes[n2]["pos"][axes[1]]) <= tol:
                            periodic[n1] = n2
                            periodic[n2] = n1
            if n1 not in periodic:
                msg = "Input graph is not periodic! Cannot match node " + str(n1) + "."
                warnings.warn(msg)
                fullyPeriodic = False
        return periodic

    xPeriodic = matchFaceNodes(xMinFace, xMaxFace, 0)
    yPeriodic = matchFaceNodes(yMinFace, yMaxFace, 1)
    zPeriodic = matchFaceNodes(zMinFace, zMaxFace, 2)
    extents = (minX, maxX, minY, maxY, minZ, maxZ)

    return [xPeriodic, yPeriodic, zPeriodic, xMinFace, xMaxFace, yMinFace, yMaxFace, zMinFace, zMaxFace, fullyPeriodic, extents]

# Adopted from https://www.idtools.com.au/3d-network-graphs-python-mplot3d-toolkit/

def network_plot_3D(G, elevation=30, angle=None, extents=None):

    NODE_DISPLAY_SIZE = 10

    if isinstance(G, Lattice): 
        extents = G.extents
        G = G.G # make this function support plotting Lattice class directory

    pos = nx.get_node_attributes(G, 'pos')
    n = G.number_of_nodes()
    # 3D network plot
    with plt.style.context(('ggplot')):
        fig = plt.figure(figsize=(8,6))
        ax = Axes3D(fig)   
        for key, value in pos.items():
            xi = value[0]
            yi = value[1]
            zi = value[2]   
            # ax.scatter(xi, yi, zi, s=20+20*G.degree(key), edgecolors='k', alpha=0.7)
            ax.scatter(xi, yi, zi, s=NODE_DISPLAY_SIZE, edgecolors='k', alpha=0.7)

        for i, j in enumerate(G.edges()):
            x = np.array((pos[j[0]][0], pos[j[1]][0]))
            y = np.array((pos[j[0]][1], pos[j[1]][1]))
            z = np.array((pos[j[0]][2], pos[j[1]][2]))
            ax.plot(x, y, z, c='black', alpha=0.5)
    
    ax.view_init(elevation, angle)
    #ax.set_axis_off()

    if extents != None:
        maxLength = max([extents[1] - extents[0], extents[3] - extents[2], extents[5] - extents[4]])
        ax.auto_scale_xyz([extents[0], extents[0] + maxLength], [extents[2], extents[2] + maxLength], [extents[4], extents[4] + maxLength])

    plt.show()
    return

###########################################################

def print_to_file(G, outputFile, movingNodes=None, fixedNodes=None):


    # DEPRECATED!
    # dynautil already handles this
    msg = "The module dynautil can generate meshes without using this function!"
    warnings.warn(msg, DeprecationWarning, stacklevel=2)

    # prints nodes and elements in format specified by Abhishek Tapadar (abhishektapadar at stanford dot edu)
    # G is a NetworkX graph object
    # outputFile is the name of the output file (can be just filename or a full path + name)
    # optionally prints moving nodes and fixed nodes

    def writeNodesFormatted(nodes):
        for n in nodes:
            file.write(str(n) + " ")
            pos = G.node[n]["pos"]
            for i in range(len(pos)):
                file.write(str(pos[i]) + " ")
            file.write("\n")

    def writeElementsFormatted(elements):
        for e in elements:
            if e[0] > e[1]:
                file.write(str(e[1]) + " " + str(e[0]) + " ")
            else:
                file.write(str(e[0]) + " " + str(e[1]) + " ")
            file.write("\n")


    file = open(outputFile, "w")
    # sort nodes and output in ascending order
    file.write("NODES: NODE_ID X Y Z\n")
    nodes = sorted(list(G))
    writeNodesFormatted(nodes)
    
    # output elements (order does not matter) as (n1, n2) tuples where n1 < n2
    file.write("ELEMENTS: N1 N2\n")
    writeElementsFormatted(G.edges)
        
    # output moving nodes
    if movingNodes != None:
        file.write("MOVING NODES: NODE_ID X Y Z\n")
        movingNodes.sort()
        writeNodesFormatted(movingNodes)

    # output fixed nodes
    if fixedNodes != None:
        file.write("FIXED NODES: NODE_ID X Y Z\n")
        fixedNodes.sort()
        writeNodesFormatted(fixedNodes)

    file.close()