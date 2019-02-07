"""
xlattice version 1.0
Written by Ruiqi Chen (rchensix at stanford dot edu) and Lucas Zhou (zzh at stanford dot edu)
February 4, 2019

This module utilizes the networkx module to generate unit cell lattice structures
"""
from __future__ import division
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import math

# Adopted from https://www.idtools.com.au/3d-network-graphs-python-mplot3d-toolkit/
def network_plot_3D(G, angle):

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
    
    ax.view_init(30, angle)
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
        print('Nodes under load: ', top_node,' and ', bottom_node)
        movingNodes.append(bottom_node)
    else:
        print('Nodes under load: ', top_node)
    
    
    temp3 = wall_grid_size[0]*node_each_layer
    print('Nodes being fixed: ', 1, 1+wall_grid_size[1],1+wall_grid_size[1]*2, 1+wall_grid_size[1]*3,
         1+temp3, 1+temp3+wall_grid_size[1],1+temp3+wall_grid_size[1]*2, 1+temp3+wall_grid_size[1]*3, '\n')

    fixedNodes = [1, 1+wall_grid_size[1],1+wall_grid_size[1]*2, 1+wall_grid_size[1]*3,
         1+temp3, 1+temp3+wall_grid_size[1],1+temp3+wall_grid_size[1]*2, 1+temp3+wall_grid_size[1]*3]

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
        for m in [5, 6, 7, 8]:
            G.add_edge(14, m)
        for n in [1, 2, 3, 4]:
            G.add_edge(13, n)
        node_count += 1
        G.add_node(node_count, pos=(width / 2, depth / 2, 0))
        node_count += 1
        G.add_node(node_count, pos=(width / 2, depth / 2, height))

    print('Nodes under load: 5, 6, 7, 8 \n')
    print('Nodes being fixed: 1, 2, 3, 4 \n')
    movingNodes = [5, 6, 7, 8]
    fixedNodes = [1, 2, 3, 4]

    return G, movingNodes, fixedNodes

def print_to_file(G, outputFile, movingNodes=None, fixedNodes=None):
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