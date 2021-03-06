"""
### XLattice Examples ###
Written by Ruiqi Chen
February 11, 2019

This module contains a set of examples using the xlattice module
"""

import xlattice as xlt
import networkx as nx

### TESSELLATIONS ###
def snapThroughTessellation():
	# Create a single sided snap-through lattice 
	snap = xlt.snapThroughLattice(30, 1, 0.1, (1, 1), both_side=False)
	snap.plot()
	# Tessellate in x and y directions
	# NOTE: the single sided snap-through lattice is NOT periodic in the z direction!
	# Attempting to tessellate in the z direction causes a crash
	snap.tessellate(2, 3, 1)
	snap.plot()

	# Create a double sided snap-through lattice
	doubleSnap = xlt.snapThroughLattice(30, 1, 0.1, (1, 1), both_side=True)
	doubleSnap.plot()
	# Tessellate in x, y, and z directions
	# Unlike the single sided version, the double sided snap-through lattice is periodic in x, y, and z!
	doubleSnap.tessellate(2, 3, 2)
	doubleSnap.plot()

def honeycombTessellation(sideLength=1, height=1):
	hexagonLattice = xlt.regularHexagonLattice(sideLength, height)
	hexagonLattice.plot()
	hexagonLattice.tessellate(6, 6, 2)
	hexagonLattice.plot()

def diamondTessellation(width=1, depth=1, height=1):
	diamondLattice = xlt.diamondLattice(width, depth, height)
	diamondLattice.plot()
	diamondLattice.tessellate(4, 4, 4)
	diamondLattice.plot()

def triangleTessellation(sideLength=1, thickness=0.1):
	triangleLattice = xlt.regularTriangleLattice(sideLength, thickness)
	triangleLattice.plot()
	triangleLattice.tessellate(3, 3, 2)
	triangleLattice.plot()

def doubleSnapThroughTessellation():
	dsnap = xlt.doubleSnapThroughLattice(10, 25, 1, 0.1, (1,1), False)
	dsnap.plot()
	dsnap.tessellate(2,2,1)
	dsnap.plot()
	dsnap2 = xlt.doubleSnapThroughLattice(10, 25, 1, 0.1, (1,1), True)
	dsnap2.plot()
	dsnap2.tessellate(2,2,2)
	dsnap2.plot()

diamondTessellation()