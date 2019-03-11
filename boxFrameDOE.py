import sys
sys.path.insert(1, "/me329/rchensix/.local/lib/python3.6/site-packages/")
import latticesim as lsim
import networkx as nx
import xlattice as xlt

def boxFrameLattice(length, diameter1, diameter2, diameter3):
	# length is the length of all sides of the cubic lattice
	# diameter1 is the diameter of the horizontal beam elements
	# diameter2 is the diameter of the slant beam elements
	# diameter3 is the diameter of the vertical beam elements

	G = nx.Graph()
	G.add_node(1, pos=(0, 0, 0))
	G.add_node(2, pos=(length/2, 0, 0))
	G.add_node(3, pos=(length, 0, 0))
	G.add_node(4, pos=(length, length/2, 0))
	G.add_node(5, pos=(length, length, 0))
	G.add_node(6, pos=(length/2, length, 0))
	G.add_node(7, pos=(0, length, 0))
	G.add_node(8, pos=(0, length/2, 0))
	G.add_node(9, pos=(0, 0, length))
	G.add_node(10, pos=(length/2, 0, length))
	G.add_node(11, pos=(length, 0, length))
	G.add_node(12, pos=(length, length/2, length))
	G.add_node(13, pos=(length, length, length))
	G.add_node(14, pos=(length/2, length, length))
	G.add_node(15, pos=(0, length, length))
	G.add_node(16, pos=(0, length/2, length))

	# horizontal elements
	G.add_edge(1, 2, diameter=diameter1)
	G.add_edge(2, 3, diameter=diameter1)
	G.add_edge(3, 4, diameter=diameter1)
	G.add_edge(4, 5, diameter=diameter1)
	G.add_edge(5, 6, diameter=diameter1)
	G.add_edge(6, 7, diameter=diameter1)
	G.add_edge(7, 8, diameter=diameter1)
	G.add_edge(8, 1, diameter=diameter1)
	G.add_edge(9, 10, diameter=diameter1)
	G.add_edge(10, 11, diameter=diameter1)
	G.add_edge(11, 12, diameter=diameter1)
	G.add_edge(12, 13, diameter=diameter1)
	G.add_edge(13, 14, diameter=diameter1)
	G.add_edge(14, 15, diameter=diameter1)
	G.add_edge(15, 16, diameter=diameter1)
	G.add_edge(16, 9, diameter=diameter1)

	# slant elements
	G.add_edge(1, 12, diameter=diameter2)
	G.add_edge(3, 14, diameter=diameter2)
	G.add_edge(5, 16, diameter=diameter2)
	G.add_edge(7, 10, diameter=diameter2)

	# vertical elements
	G.add_edge(1, 9, diameter=diameter3)
	G.add_edge(3, 11, diameter=diameter3)
	G.add_edge(5, 13, diameter=diameter3)
	G.add_edge(7, 15, diameter=diameter3)

	return xlt.Lattice(G)

lsim.fullFactorialSimulation(boxFrameLattice, homeDirectory=None, length=[10], diameter1=[2], diameter2=[1], diameter3=[0.2, 0.4, 0.6, 0.8, 1])