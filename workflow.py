# Written by Ruiqi Chen
# February 5, 2019
# This code serves as the main code and (will eventually) does the following:
#	Generate a lattice from parameters
#	Mesh lattice and create LS-Dyna input file
#	Send job to mc2 cluster
# 	Postprocess job to extract load-displacement data
#	Iterate parameters using off-the-shelf optimization

import xlattice as xlt
import dynautil as util
import slurmscheduler as sch

# Generate a few lattices
INCLINATION = [10, 15, 20, 25]
EDGE_LENGTH = 10
WALL_HEIGHT = 1
WALL_GRID_SIZE = (2, 3)
LSCARDS = util.importDynaCardsList("defaultcards.k")

for angle in INCLINATION:
	lattice, movingNodes, fixedNodes = xlt.snap_through_lattice(angle, EDGE_LENGTH, WALL_HEIGHT, WALL_GRID_SIZE)
	util.writeKeyFile(lattice, "snap_through_" + str(angle) + ".k", size=1, movingNodes=movingNodes, fixedNodes=fixedNodes, cards=LSCARDS)