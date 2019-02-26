import networkx as nx
import xlattice as xlt
import math

# Written by Ruiqi Chen (rchensix at stanford dot edu), Lucas Zhou (zzh at stanford dot edu), and Abhishek Tapadar (abhishektapadar at stanford dot edu)
# This module holds a collection of parameterizable lattice structures implemented using NetworkX and XLattice

"""
Represented lattices:

Snap Through
Double Snap Through
Simple Cubic
Face Centered Cubic (two types)
Body Centered Cubic
Regular Hexagon
Diamond
Regular Triangle
Pratt Truss
Perovskite (three types)
"""

"""
Version 1.0
February 25, 2019

Initial release
"""

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
    return xlt.Lattice(snap_through_lattice(inclined_angle, edge_length, wall_height, wall_grid_size, both_side)[0])

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

def doubleSnapThroughLattice(inclined_angle1, inclined_angle2, edge_length, wall_height, wall_grid_size, both_side=False):
    # Wraps in Lattice class
    return xlt.Lattice(double_snap_through_lattice(inclined_angle1, inclined_angle2, edge_length, wall_height, wall_grid_size, both_side)[0])


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
    return xlt.Lattice(generate_simple_cubic(width, depth, height)[0])

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
        return xlt.Lattice(generate_BCC(width, depth, height)[0])
    elif type == 2:
        return xlt.Lattice(generate_BCC_type2(width, depth, height)[0])

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
    return xlt.Lattice(generate_FCC(width, depth, height, open_type)[0]) 

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
    return xlt.Lattice(G)

###########################################################


def diamond_lattice (width, depth, height):
    G = nx.Graph()
    node_count = 1
    G.add_node(node_count, pos=(width/4, depth/4, height/4))
    node_count += 1
    G.add_node(node_count, pos=(width*3/4, depth*3/4, height/4))
    node_count += 1
    G.add_node(node_count, pos=(width*3/4, depth/4, height*3/4))
    node_count += 1
    G.add_node(node_count, pos=(width/4, depth*3/4, height*3/4))
    
    for i in np.arange(1,5):
        all_pos = nx.get_node_attributes(G,'pos').values()
        rev_all_pos = dict((v,k) for k, v in nx.get_node_attributes(G,'pos').items())
        (x,y,z) = G.nodes[i]["pos"]
        if (x-width/4, y-depth/4, z-height/4) not in all_pos:
            node_count += 1
            G.add_node(node_count, pos=(x-width/4, y-depth/4, z-height/4))
            G.add_edge(i, node_count)
        else:
            j = rev_all_pos.get((x-width/4, y-depth/4, z-height/4))
            G.add_edge(i, j)
        if (x+width/4, y+depth/4, z-height/4) not in all_pos:
            node_count += 1
            G.add_node(node_count, pos=(x+width/4, y+depth/4, z-height/4))
            G.add_edge(i, node_count)
        else:
            j = rev_all_pos.get((x+width/4, y+depth/4, z-height/4))
            G.add_edge(i, j)
        if (x+width/4, y-depth/4, z+height/4) not in all_pos:
            node_count += 1
            G.add_node(node_count, pos=(x+width/4, y-depth/4, z+height/4))
            G.add_edge(i, node_count)
        else:
            j = rev_all_pos.get((x+width/4, y-depth/4, z+height/4))
            G.add_edge(i, j)
        if (x-width/4, y+depth/4, z+height/4) not in all_pos:
            node_count += 1
            G.add_node(node_count, pos=(x-width/4, y+depth/4, z+height/4))
            G.add_edge(i, node_count)
        else:
            j = rev_all_pos.get((x-width/4, y+depth/4, z+height/4))
            G.add_edge(i, j)

    # add missing 4 lone corner nodes
    node_count += 1
    G.add_node(node_count, pos=(width, 0, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, depth, 0))
    node_count += 1
    G.add_node(node_count, pos=(0, 0, height))
    node_count += 1
    G.add_node(node_count, pos=(width, depth, height))

    return G

def diamondLattice(width, depth, height):
    # wraps NetworkX Graph in Lattice class
    return xlt.Lattice(diamond_lattice(width, depth, height))

def regularTriangleLattice(sideLength=1, diameter=None):
    # if diameter is specified, an edge attribute "diameter" will be added to all edges

    G = nx.Graph()

    # bottom layer
    G.add_node(1, pos=(0, 0, 0))
    G.add_node(2, pos=(0, sideLength, 0))
    G.add_node(3, pos=(math.sqrt(3)/2*sideLength, sideLength, 0))
    G.add_node(4, pos=(math.sqrt(3)*sideLength, sideLength, 0))
    G.add_node(5, pos=(math.sqrt(3)*sideLength, 0, 0))
    G.add_node(6, pos=(math.sqrt(3)/2*sideLength, 0, 0))
    G.add_node(7, pos=(math.sqrt(3)/2*sideLength, sideLength/2, 0))

    # middle layer
    h1 = math.sqrt(6)/3*sideLength
    G.add_node(8, pos=(0, sideLength/3, h1))
    G.add_node(9, pos=(0, 2/3*sideLength, h1))
    G.add_node(10, pos=(math.sqrt(3)/6*sideLength, sideLength, h1))
    G.add_node(11, pos=(2*math.sqrt(3)/3*sideLength, sideLength, h1))
    G.add_node(12, pos=(math.sqrt(3)*sideLength, 2/3*sideLength, h1))
    G.add_node(13, pos=(math.sqrt(3)*sideLength, sideLength/3, h1))
    G.add_node(14, pos=(2*math.sqrt(3)/3*sideLength, 0, h1))
    G.add_node(15, pos=(math.sqrt(3)/6*sideLength, 0, h1))
    G.add_node(16, pos=(math.sqrt(3)/6*sideLength, sideLength/2, h1))

    # upper layer
    h2 = 2*h1
    G.add_node(17, pos=(0, sideLength/3, h2))
    G.add_node(18, pos=(0, 2/3*sideLength, h2))
    G.add_node(19, pos=(math.sqrt(3)/3*sideLength, sideLength, h2))
    G.add_node(20, pos=(5*math.sqrt(3)/6*sideLength, sideLength, h2))
    G.add_node(21, pos=(math.sqrt(3)*sideLength, 2/3*sideLength, h2))
    G.add_node(22, pos=(math.sqrt(3)*sideLength, sideLength/3, h2))
    G.add_node(23, pos=(5*math.sqrt(3)/6*sideLength, 0, h2))
    G.add_node(24, pos=(math.sqrt(3)/3*sideLength, 0, h2))
    G.add_node(25, pos=(5*math.sqrt(3)/6*sideLength, sideLength/2, h2))

    # top layer - repeat bottom layer for periodicity
    h3 = 3*h1
    G.add_node(26, pos=(0, 0, h3))
    G.add_node(27, pos=(0, sideLength, h3))
    G.add_node(28, pos=(math.sqrt(3)/2*sideLength, sideLength, h3))
    G.add_node(29, pos=(math.sqrt(3)*sideLength, sideLength, h3))
    G.add_node(30, pos=(math.sqrt(3)*sideLength, 0, h3))
    G.add_node(31, pos=(math.sqrt(3)/2*sideLength, 0, h3))
    G.add_node(32, pos=(math.sqrt(3)/2*sideLength, sideLength/2, h3))

    # two additional weird nodes on +y/-y faces connecting middle and upper layers
    G.add_node(33, pos=(0, sideLength/2, 1.5*h1))
    G.add_node(34, pos=(math.sqrt(3)*sideLength, sideLength/2, 1.5*h1))

    def addEdge(n1, n2):
        if diameter == None:
            G.add_edge(n1, n2)
        else:
            G.add_edge(n1, n2, diameter=diameter)

    # bottom to bottom edges
    addEdge(1, 2)
    addEdge(4, 5)
    addEdge(1, 7)
    addEdge(2, 7)
    addEdge(3, 7)
    addEdge(4, 7)
    addEdge(5, 7)
    addEdge(6, 7)

    # bottom to middle edges
    addEdge(1, 16)
    addEdge(2, 16)
    addEdge(7, 16)
    addEdge(11, 7)
    addEdge(11, 4)
    addEdge(14, 7)
    addEdge(14, 5)

    # middle to middle edges
    addEdge(16, 8)
    addEdge(16, 9)
    addEdge(16, 10)
    addEdge(16, 11)
    addEdge(16, 14)
    addEdge(16, 15)
    addEdge(11, 14)
    addEdge(11, 12)
    addEdge(13, 14)

    # middle to upper edges
    addEdge(19, 16)
    addEdge(19, 11)
    addEdge(24, 16)
    addEdge(24, 14)
    addEdge(25, 11)
    addEdge(25, 14)
    # connect weird nodes
    addEdge(33, 16)
    addEdge(34, 25)

    # upper to upper edges
    addEdge(18, 19)
    addEdge(19, 24)
    addEdge(19, 25)
    addEdge(24, 25)
    addEdge(24, 17)
    addEdge(25, 20)
    addEdge(25, 21)
    addEdge(25, 22)
    addEdge(25, 23)

    # upper to top edges
    addEdge(32, 19)
    addEdge(32, 24)
    addEdge(32, 25)
    addEdge(26, 24)
    addEdge(27, 19)
    addEdge(29, 25)
    addEdge(30, 25)

    # top to top
    addEdge(26, 27)
    addEdge(29, 30)
    addEdge(26, 32)
    addEdge(27, 32)
    addEdge(28, 32)
    addEdge(29, 32)
    addEdge(30, 32)
    addEdge(31, 32)

    return xlt.Lattice(G)

def prattTrussLattice(length=1, width=1, height=1, horizontalDiameter=0.1, verticalDiameter=0.1, slantDiameter=0.1):
	assert(length > 0 and width > 0 and height > 0 and horizontalDiameter > 0 and verticalDiameter > 0 and slantDiameter > 0)
	G = nx.Graph()
	# start with simple cubic
	G.add_node(1, pos=(0, 0, 0))
	G.add_node(2, pos=(length, 0, 0))
	G.add_node(3, pos=(length, width, 0))
	G.add_node(4, pos=(0, width, 0))
	G.add_node(5, pos=(0, 0, height))
	G.add_node(6, pos=(length, 0, height))
	G.add_node(7, pos=(length, width, height))
	G.add_node(8, pos=(0, width, height))
	G.add_edge(1, 2, diameter=horizontalDiameter)
	G.add_edge(2, 3, diameter=horizontalDiameter)
	G.add_edge(3, 4, diameter=horizontalDiameter)
	G.add_edge(4, 1, diameter=horizontalDiameter)
	G.add_edge(5, 6, diameter=horizontalDiameter)
	G.add_edge(6, 7, diameter=horizontalDiameter)
	G.add_edge(7, 8, diameter=horizontalDiameter)
	G.add_edge(8, 5, diameter=horizontalDiameter)
	G.add_edge(1, 5, diameter=verticalDiameter)
	G.add_edge(2, 6, diameter=verticalDiameter)
	G.add_edge(3, 7, diameter=verticalDiameter)
	G.add_edge(4, 8, diameter=verticalDiameter)
	# add slant edges on opposing sides
	G.add_edge(2, 5, diameter=slantDiameter)
	G.add_edge(4, 5, diameter=slantDiameter)
	G.add_edge(3, 6, diameter=slantDiameter)
	G.add_edge(3, 8, diameter=slantDiameter)
	return xlt.Lattice(G)

	###################################################

def generate_perovskiteLattice(width, depth, height):
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
    G.add_node(node_count, pos=(width/2, depth, height/2))
    node_count += 1
    G.add_node(node_count, pos=(0, depth/2, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width/2, 0, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width, depth/2, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, 0))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height/2))


    for i in np.arange(1,5):
        G.add_edge(i, i+4)
    for j in [1,2,3,5,6,7]:
        G.add_edge(j, j+1)
    G.add_edge(1,4)
    G.add_edge(5,8)
    
    G.add_edge(9,10)
    G.add_edge(9,12)
    G.add_edge(9,13)
    G.add_edge(9,14)
    G.add_edge(10,11)
    G.add_edge(10,13)
    G.add_edge(10,14)
    G.add_edge(11,12)
    G.add_edge(11,14)
    G.add_edge(11,13)
    G.add_edge(12,13)
    G.add_edge(12,14)
    
    G.add_edge(9,15)
    G.add_edge(10,15)
    G.add_edge(11,15)
    G.add_edge(12,15)
    G.add_edge(13,15)
    G.add_edge(14,15)
    
    
    
    movingNodes = [5, 6, 7, 8, 13]
    fixedNodes = [1, 2, 3, 4, 12]
    
    return G, movingNodes, fixedNodes

def perovskiteLattice(width, depth, height):
    # uses the Lattice class instead
    return xlt.Lattice(generate_perovskiteLattice(width, depth, height)[0])

###################################################################################

def generate_stripped_perovskiteLattice(width, depth, height):
    G = nx.Graph()
    
    node_count = 9
    G.add_node(node_count, pos=(width/2, depth, height/2))
    node_count += 1
    G.add_node(node_count, pos=(0, depth/2, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width/2, 0, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width, depth/2, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, 0))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height/2))
    
    G.add_edge(9,10)
    G.add_edge(9,12)
    G.add_edge(9,13)
    G.add_edge(9,14)
    G.add_edge(10,11)
    G.add_edge(10,13)
    G.add_edge(10,14)
    G.add_edge(11,12)
    G.add_edge(11,14)
    G.add_edge(11,13)
    G.add_edge(12,13)
    G.add_edge(12,14)
    
    G.add_edge(9,15)
    G.add_edge(10,15)
    G.add_edge(11,15)
    G.add_edge(12,15)
    G.add_edge(13,15)
    G.add_edge(14,15)
    
    
    
    movingNodes = [5, 6, 7, 8, 13]
    fixedNodes = [1, 2, 3, 4, 12]
    
    return G, movingNodes, fixedNodes

def stripped_perovskiteLattice(width, depth, height):
    # uses the Lattice class instead
    return xlt.Lattice(generate_perovskiteLattice(width, depth, height)[0])



###################################################################################

def generate_rigid_perovskiteLattice(width, depth, height):
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
    G.add_node(node_count, pos=(width/2, depth, height/2))
    node_count += 1
    G.add_node(node_count, pos=(0, depth/2, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width/2, 0, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width, depth/2, height/2))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, 0))
    node_count += 1
    G.add_node(node_count, pos=(width/2, depth/2, height/2))


    for i in np.arange(1,5):
        G.add_edge(i, i+4)
    for j in [1,2,3,5,6,7]:
        G.add_edge(j, j+1)
    G.add_edge(1,4)
    G.add_edge(5,8)
    
    G.add_edge(9,10)
    G.add_edge(9,12)
    G.add_edge(9,13)
    G.add_edge(9,14)
    G.add_edge(10,11)
    G.add_edge(10,13)
    G.add_edge(10,14)
    G.add_edge(11,12)
    G.add_edge(11,14)
    G.add_edge(11,13)
    G.add_edge(12,13)
    G.add_edge(12,14)
    
    G.add_edge(9,15)
    G.add_edge(10,15)
    G.add_edge(11,15)
    G.add_edge(12,15)
    G.add_edge(13,15)
    G.add_edge(14,15)
    
    G.add_edge(1,11)
    G.add_edge(2,11)
    G.add_edge(6,11)
    G.add_edge(5,11)
    
    G.add_edge(4,9)
    G.add_edge(8,9)
    G.add_edge(7,9)
    G.add_edge(3,9)
    
    G.add_edge(1,10)
    G.add_edge(4,10)
    G.add_edge(8,10)
    G.add_edge(5,10)
    
    G.add_edge(2,12)
    G.add_edge(3,12)
    G.add_edge(7,12)
    G.add_edge(6,12)
    
    G.add_edge(5,13)
    G.add_edge(8,13)
    G.add_edge(7,13)
    G.add_edge(6,13)
    
    G.add_edge(1,14)
    G.add_edge(2,14)
    G.add_edge(3,14)
    G.add_edge(4,14)
    
    
    
    movingNodes = [5, 6, 7, 8, 13]
    fixedNodes = [1, 2, 3, 4, 12]
    
    return G, movingNodes, fixedNodes

def rigid_perovskiteLattice(width, depth, height):
    # uses the Lattice class instead
    return xlt.Lattice(generate_perovskiteLattice(width, depth, height)[0])

###########################################################