"""
xlattice version 1.3
Written by Ruiqi Chen (rchensix at stanford dot edu) and Lucas Zhou (zzh at stanford dot edu)
February 11, 2019
This module utilizes the networkx module to generate unit cell lattice structures

SUMMARY OF LATTICE TYPES (AS OF VERSION 1.3)
-Sanp Through Lattice (single-sided and double-sided)
-Doube Sanp Through Lattice (single-sided and double-sided)
-Simple Cubic 
-BCC (type 1 and type 2)
-FCC (close-type and open-type)
-Regular Hexagon

NEW IN 1.3
-Added double_snap_through_lattice type, a variant from sanp_through. This one has two layers of snap-through feature.
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
from __future__ import division
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
        if not inPlace:
            return Lattice(result, self.tol)

    def plot(self, elevation=30, azimuth=None):
        network_plot_3D(self.G, elevation, azimuth)

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

def network_plot_3D(G, elevation=30, angle=None):

    if isinstance(G, Lattice): G = G.G # make this function support plotting Lattice class directory

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
            ax.scatter(xi, yi, zi, s=20+20*G.degree(key), edgecolors='k', alpha=0.7)

        for i, j in enumerate(G.edges()):
            x = np.array((pos[j[0]][0], pos[j[1]][0]))
            y = np.array((pos[j[0]][1], pos[j[1]][1]))
            z = np.array((pos[j[0]][2], pos[j[1]][2]))
            ax.plot(x, y, z, c='black', alpha=0.5)
    
    ax.view_init(elevation, angle)
    #ax.set_axis_off()

    plt.show()
    return


######################################################
# Input Explanation:
# inclined_angle: describe how much the bistable beam tilts
# edge_length: long edge length
# wall_height: short edge height
# wall_grid_size: number of grids for the side wall, in the form of (m,n), m = vertical, n = horizontal 
# both_side: whether to have bistable beams on both side of the unit lattice, default: False

# In the future: beam weight should be added. 

def snap_through_lattice(inclined_angle, edge_length, wall_height, wall_grid_size, both_side=False):
    G = nx.Graph()
    node_count = 1
    node_each_layer = wall_grid_size[1]*4
    
    for z in np.arange(wall_grid_size[0]+1):
        z_pos = (wall_height/wall_grid_size[0]) * z
          
        for side1 in np.arange(wall_grid_size[1]):
            y_pos = 0
            old_node = node_count
            x_pos = (edge_length/wall_grid_size[1]) * side1
            G.add_node(node_count, pos=(x_pos, y_pos, z_pos))
            node_count +=1
            if old_node-1 != 0:
                if (old_node-1)%node_each_layer !=0:
                    G.add_edge(old_node, old_node-1)
            
        for side2 in np.arange(wall_grid_size[1]):
            x_pos = edge_length
            old_node = node_count
            y_pos = (edge_length/wall_grid_size[1]) * side2
            G.add_node(node_count, pos=(x_pos, y_pos, z_pos))
            node_count +=1
            G.add_edge(old_node, old_node-1)
            
        for side3 in np.arange(wall_grid_size[1]):
            y_pos = edge_length
            old_node = node_count
            x_pos = edge_length - (edge_length/wall_grid_size[1]) * side3
            G.add_node(node_count, pos=(x_pos, y_pos, z_pos))
            node_count += 1
            G.add_edge(old_node, old_node-1)
        
        for side4 in np.arange(wall_grid_size[1]):
            x_pos = 0
            old_node = node_count
            y_pos = edge_length - (edge_length/wall_grid_size[1]) * side4
            G.add_node(node_count, pos=(x_pos, y_pos, z_pos))
            node_count +=1          
            G.add_edge(old_node, old_node-1)

    nodes_list = list(G.nodes())
    
    # Add missing horizontal edges
    temp2 = len(nodes_list)//node_each_layer
    for i in np.arange(temp2):
        G.add_edge(1+node_each_layer*i, node_each_layer*(i+1))
            
            
    # Add vertical edges
    temp1 = nodes_list[-1-node_each_layer]
    for each_node in np.arange(temp1):
        G.add_edge(each_node+1, each_node+1 + node_each_layer)
          
    # Add top node and the edges to it
    top_node_z = math.tan(math.pi*(inclined_angle/180)) * math.sqrt(2) / 2 * edge_length + wall_height       
    G.add_node(node_count, pos=(edge_length/2, edge_length/2, top_node_z))
    top_node = node_count
    for j in np.arange(4):
        G.add_edge(top_node, top_node-node_each_layer+wall_grid_size[1]*j)
    
    movingNodes = [top_node]

    # If wanted, add bottom node and the edges to it
    if both_side:
        node_count += 1 
        bottom_node_z = -math.tan(math.pi*(inclined_angle/180)) * math.sqrt(2) / 2 * edge_length
        G.add_node(node_count, pos=(edge_length/2, edge_length/2, bottom_node_z))  
        bottom_node = node_count
        for jj in np.arange(4):
            G.add_edge(node_count, 1 + wall_grid_size[1]*jj)         
        # print('Nodes under load: ', top_node,' and ', bottom_node)
        movingNodes.append(bottom_node)
    # else:
    #     print('Nodes under load: ', top_node)
    
    
    temp3 = wall_grid_size[0]*node_each_layer
    # print('Nodes being fixed: ', 1, 1+wall_grid_size[1],1+wall_grid_size[1]*2, 1+wall_grid_size[1]*3,
    #      1+temp3, 1+temp3+wall_grid_size[1],1+temp3+wall_grid_size[1]*2, 1+temp3+wall_grid_size[1]*3, '\n')

    fixedNodes = [1, 1+wall_grid_size[1],1+wall_grid_size[1]*2, 1+wall_grid_size[1]*3,
         1+temp3, 1+temp3+wall_grid_size[1],1+temp3+wall_grid_size[1]*2, 1+temp3+wall_grid_size[1]*3]

    return G, movingNodes, fixedNodes

def snapThroughLattice(inclined_angle, edge_length, wall_height, wall_grid_size, both_side=False):
    # uses the Lattice class instead
    return Lattice(snap_through_lattice(inclined_angle, edge_length, wall_height, wall_grid_size, both_side)[0])

###################################################
# Another variant from snap_through_lattice. 

def double_snap_through_lattice(inclined_angle1, inclined_angle2, edge_length, wall_height, wall_grid_size, both_side=False):
    G, movingNodes, fixedNodes = snap_through_lattice(inclined_angle1,edge_length,wall_height,wall_grid_size, both_side)
    node_each_layer = wall_grid_size[1]*4
    node_count = list(G.nodes())[-1] +1
    top_node_z2 = math.tan(math.pi*(inclined_angle2/180)) * math.sqrt(2) / 2 * edge_length + wall_height
    G.add_node(node_count, pos=(edge_length/2, edge_length/2, top_node_z2))
    
    if not both_side:
        for j in np.arange(4):
            G.add_edge(node_count, node_count-1-node_each_layer+wall_grid_size[1]*j)
        G.add_edge(node_count, node_count-1)
        movingNodes = [node_count]
    else:  
        bottom_node_z2 = -math.tan(math.pi*(inclined_angle2/180)) * math.sqrt(2) / 2 * edge_length
        node_count += 1
        G.add_node(node_count, pos=(edge_length/2, edge_length/2, -top_node_z2))
        for j in np.arange(4):
            G.add_edge(node_count-1, node_count-3-node_each_layer+wall_grid_size[1]*j)
            G.add_edge(node_count, wall_grid_size[1]*j+1)
        G.add_edge(node_count, node_count-2)
        G.add_edge(node_count-1, node_count-3)
        movingNodes = [node_count, node_count-1]
        
    return G, movingNodes, fixedNodes


###################################################
def generate_simple_cubic (width, depth, height):
    G = nx.Graph()
    node_count = 1
    G.add_node(node_count, pos=(0, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, height))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, height))


    for i in np.arange(1,5):
        G.add_edge(i, i+4)
    for j in [1,2,3,5,6,7]:
        G.add_edge(j, j+1)
    G.add_edge(1,4)
    G.add_edge(5,8)
    movingNodes = [5, 6, 7, 8]
    fixedNodes = [1, 2, 3, 4]
    
    return G, movingNodes, fixedNodes

def simpleCubicLattice(width, depth, height):
    # uses the Lattice class instead
    return Lattice(generate_simple_cubic(width, depth, height)[0])

###################################################
def generate_BCC (width, depth, height):
    G = nx.Graph()
    node_count = 1
    G.add_node(node_count, pos=(0, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, height))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, height))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height/2))

    for i in np.arange(1,9):
        G.add_edge(i, 9)

    movingNodes = [5, 6, 7, 8]
    fixedNodes = [1, 2, 3, 4]
    
    return G, movingNodes, fixedNodes

###################################################
def generate_BCC_type2 (width, depth, height):
    G = nx.Graph()
    node_count = 1
    G.add_node(node_count, pos=(0, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, height))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, height))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height/2))

    for i in np.arange(1,9):
        G.add_edge(i, 9)
    for j in np.arange(1,5):
        G.add_edge(j, j+4)
        
    movingNodes = [5, 6, 7, 8]
    fixedNodes = [1, 2, 3, 4]
    
    return G, movingNodes, fixedNodes

def bccLatice(width, depth, height, type=1):
    # uses the Lattice class instead and combines multiple BCC lattices
    if type == 1:
        return Lattice(generate_BCC(width, depth, height)[0])
    elif type == 2:
        return Lattice(generate_BCC_type2(width, depth, height)[0])

###################################################
# open type FCC does not top center and bottom center nodes in a unit lattice
def generate_FCC(width, depth, height, open_type=False):
    G = nx.Graph()
    node_count = 1
    G.add_node(node_count, pos=(0, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, height))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, height))
    node_count += 1

    G.add_node(node_count, pos=(width / 2, 0, height / 2))
    node_count += 1
    G.add_node(node_count, pos=(width, depth / 2, height / 2))
    node_count += 1
    G.add_node(node_count, pos=(width / 2, depth, height / 2))
    node_count += 1
    G.add_node(node_count, pos=(0, depth / 2, height / 2))

    for i in np.arange(9, 13):
        for j in [-8, -7, -4, -3]:
            if i + j == 9:
                G.add_edge(i, 1)
            else:
                G.add_edge(i, i + j)

    if not open_type:            
        node_count += 1
        G.add_node(node_count, pos=(width / 2, depth / 2, 0))
        node_count += 1
        G.add_node(node_count, pos=(width / 2, depth / 2, height))
        for m in [5, 6, 7, 8]:
            G.add_edge(14, m)
        for n in [1, 2, 3, 4]:
            G.add_edge(13, n)

    print('Nodes under load: 5, 6, 7, 8 \n')
    print('Nodes being fixed: 1, 2, 3, 4 \n')
    movingNodes = [5, 6, 7, 8]
    fixedNodes = [1, 2, 3, 4]

    return G, movingNodes, fixedNodes

def fccLattice(width, depth, height, open_type=False):
    # uses the lattice class instead
    return Lattice(generate_FCC(width, depth, height, open_type)[0]) 

###########################################################

def regularHexagonLattice(sideLength, height):
    G = nx.Graph([(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1), (5, 7), 
        (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 8), (12, 14),
        (1, 8), (2, 9), (3, 10), (4, 11), (5, 12), (6, 13), (7, 14)])
    G.nodes[1]["pos"] = (sideLength/2, 0, 0)
    G.nodes[2]["pos"] = (0, sideLength*math.sqrt(3)/2, 0)
    G.nodes[3]["pos"] = (0.5*sideLength, sideLength*math.sqrt(3), 0)
    G.nodes[4]["pos"] = (1.5*sideLength, sideLength*math.sqrt(3), 0)
    G.nodes[5]["pos"] = (2*sideLength, sideLength*math.sqrt(3)/2, 0)
    G.nodes[6]["pos"] = (1.5*sideLength, 0, 0)
    G.nodes[7]["pos"] = (3*sideLength, sideLength*math.sqrt(3)/2, 0)
    G.nodes[8]["pos"] = (sideLength/2, 0, height)
    G.nodes[9]["pos"] = (0, sideLength*math.sqrt(3)/2, height)
    G.nodes[10]["pos"] = (0.5*sideLength, sideLength*math.sqrt(3), height)
    G.nodes[11]["pos"] = (1.5*sideLength, sideLength*math.sqrt(3), height)
    G.nodes[12]["pos"] = (2*sideLength, sideLength*math.sqrt(3)/2, height)
    G.nodes[13]["pos"] = (1.5*sideLength, 0, height)
    G.nodes[14]["pos"] = (3*sideLength, sideLength*math.sqrt(3)/2, height)
    return Lattice(G)

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