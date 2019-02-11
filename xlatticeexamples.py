"""
### XLattice Examples ###
Written by Ruiqi Chen
February 11, 2019

This module contains a set of examples using the xlattice module
"""

import xlattice as xlt

### TESSELLATIONS ###
def tessellationExample():
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

tessellationExample()