# Written by Ruiqi Chen
# February 4, 2019
# This module contains a collection of functions to automate the PrePost process

import math
import networkx
import numpy as np

def writeKeyFile(G, outputFile, size=1, movingNodes=None, fixedNodes=None, cards=None):
	# Creates a LS-Dyna outputFile.k file with elements found in lattice G, 
	# predefined velocity conditions on movingNodes, spc boundary conditions on fixedNodes,
	# and appends any additional inputcards at the end
	# cards is a list of strings
	
	file = open(outputFile, "w")

	# write any optional cards at top of file
	if cards != None and len(cards) != 0:
		for card in cards:
			file.write(card)

	# mesh the lattice
	elements, allNodes = meshBeamEdges(G, size)

	# write nodes
	file.write("\n*NODES\n")
	file.write("$#   nid               x               y               z      tc      rc\n")
	writeNodes(file, allNodes)

	# write elements
	file.write("*ELEMENT_BEAM\n")
	file.write("$#   eid     pid      n1      n2      n3     rt1     rr1     rt2     rr2   local\n")
	writeElements(file, elements)

	# write prescribed velocity (moving nodes)
	file.write("*BOUNDARY_PRESCRIBED_MOTION_NODE\n")
	file.write("$#     nid       dof       vad      lcid        sf       vid     death     birth\n")
	writePrescribedVelocity(file, movingNodes, dof=3)

	# write spc boundary conditions (fixed nodes)
	file.write("*BOUNDARY_SPC_NODE\n")
	file.write("$#     nid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz\n")
	writeSPC(file, fixedNodes)

	# Write *END keyword
	file.write("*END")

	file.close()

def writePrescribedVelocity(openedFile, movingNodes, dof=1, vad=0, lcid=1, sf=1, vid=0, death="1.0E28", birth=0.0):
	for node in movingNodes:
		openedFile.write(setLengthStr(node))
		openedFile.write(setLengthStr(dof))
		openedFile.write(setLengthStr(vad))
		openedFile.write(setLengthStr(lcid))
		openedFile.write(setLengthStr(sf))
		openedFile.write(setLengthStr(vid))
		openedFile.write(setLengthStr(death))
		openedFile.write(setLengthStr(birth))
		openedFile.write("\n")

def writeSPC(openedFile, fixedNodes, cid=0, dofx=1, dofy=1, dofz=1, dofrx=0, dofry=0, dofrz=0):
	for node in fixedNodes:
		openedFile.write(setLengthStr(node))
		openedFile.write(setLengthStr(cid))
		openedFile.write(setLengthStr(dofx))
		openedFile.write(setLengthStr(dofy))
		openedFile.write(setLengthStr(dofz))
		openedFile.write(setLengthStr(dofrx))
		openedFile.write(setLengthStr(dofry))
		openedFile.write(setLengthStr(dofrz))
		openedFile.write("\n")

def setLengthStr(input, length=10):
	# takes an input and converts to right-aligned LS-Dyna input format
	# appends spaces or truncates as necessary
	# WARNING: does NOT work with scientific notation currently
	# default length of 10 characters used
	input = str(input)
	if len(input) <= length:
		return " "*(length-len(input)) + input
	else:
		return input[0:length]

def detailedNodeList(G, simpleNodeList):
	detailedList = list()
	for n in simpleNodeList:
		detailedList.append((n, G.node[n]["pos"][0], G.node[n]["pos"][1], G.node[n]["pos"][2]))
	return detailedList

def writeNodes(openedFile, nodes, header=None):
	# openedFile must be opened already (as the name suggests!)
	# assumes 0 tc and rc (maybe will be changed in future?)
	if header != None:
		openedFile.write(header + "\n")
	for n in nodes:
		openedFile.write(setLengthStr(n[0], 8))
		openedFile.write(setLengthStr(n[1], 16))
		openedFile.write(setLengthStr(n[2], 16))
		openedFile.write(setLengthStr(n[3], 16))
		openedFile.write(setLengthStr(0, 8)) # tc
		openedFile.write(setLengthStr(0, 8)) # rc
		openedFile.write("\n")

def writeElements(openedFile, elements, header=None):
	# elements is a list of (eid, pid, n1, n2) tuples
	# openedFile must be opened already (as the name suggests!)
	# assumes a lot of constants currently (will be fixed if necessary)
	if header != None:
		openedFile.write(header + "\n")
	for e in elements:
		eid, pid, n1, n2 = e
		openedFile.write(setLengthStr(eid, 8))
		openedFile.write(setLengthStr(pid, 8))
		openedFile.write(setLengthStr(n1, 8))
		openedFile.write(setLengthStr(n2, 8))
		openedFile.write(setLengthStr(0, 8)) # n3
		openedFile.write(setLengthStr(0, 8)) # rt1
		openedFile.write(setLengthStr(0, 8)) # rr1
		openedFile.write(setLengthStr(0, 8)) # rt2
		openedFile.write(setLengthStr(0, 8)) # rr2
		openedFile.write(setLengthStr(2, 8)) # local
		openedFile.write("\n")

def meshBeamEdges(G, size=1, eidStart=1, nidStart=None):
	# meshes all edges in G with elements of size size
	# assigns element numbers in order starting from eidStart (default = 1)
	# creates extra nodes starting from nidStart (if set to None, will start at numberNodesInG + 1)
	# if size > edge, then the entire edge will be one element
	if nidStart == None:
		nidStart = networkx.classes.function.number_of_nodes(G) + 1
	elements = list()
	allNodes = list()
	for n in list(G):
		allNodes.append((n, G.node[n]["pos"][0], G.node[n]["pos"][1], G.node[n]["pos"][2]))
	nextNode = nidStart
	for e in G.edges_iter(): # this is a networkx 1.11 statement; will need to change depending on version
		edgeLength = float(getEdgeLength(G, e))
		nElements = int(math.ceil(edgeLength/size)) # round up
		elementLength = edgeLength/nElements
		prevNode = e[0]
		x0, y0, z0 = G.node[e[0]]["pos"]
		x1, y1, z1 = G.node[e[1]]["pos"]
		for i in range(nElements):
			if i == nElements - 1:
				# don't create new node
				nid = e[1]
			else:
				# create new node (nid, x, y, z)
				unitv = unitVec((x0, y0, z0), (x1, y1, z1))
				nid = nextNode
				nextNode += 1 # increment if you create new node
				x = x0 + unitv[0]*elementLength*(i+1)
				y = y0 + unitv[1]*elementLength*(i+1)
				z = z0 + unitv[2]*elementLength*(i+1)
				allNodes.append((nid, x, y, z))
			elements.append((eidStart, 1, prevNode, nid)) # assumes pid = 1
			prevNode = nid
			eidStart += 1
	return elements, allNodes

def getEdgeLength(G, e):
	n0, n1 = e
	return math.sqrt((G.node[n0]["pos"][0]-G.node[n1]["pos"][0])**2 + (G.node[n0]["pos"][1]-G.node[n1]["pos"][1])**2 + (G.node[n0]["pos"][2]-G.node[n1]["pos"][2])**2)

def unitVec(a, b):
	# returns normalized vector (u, v, w) representing unit vector from point a to point b
	l = math.sqrt((b[0]-a[0])**2 + (b[1]-a[1])**2 + (b[2]-a[2])**2)
	vec = ((b[0]-a[0])/l, (b[1]-a[1])/l, (b[2]-a[2])/l)
	return vec

def parseDynaBndout(file):
	# file can either be filename or full file path + name
	results = dict() # nid:numpy array N x 5 with (t, Fx, Fy, Fz, E) as elements
	bndout = open(file, "r")
	t = None
	for line in bndout:
		if " n o d a l   f o r c e/e n e r g y    o u t p u t  t=" in line:
			t = float(line.split()[-1]) # get current timestep
		elif " nd#" in line:
			splitLine = line.split()
			nid = int(splitLine[1])
			Fx = float(splitLine[3])
			Fy = float(splitLine[5])
			Fz = float(splitLine[7])
			E = float(splitLine[9])
			if nid in results:
				results[nid] = np.append(results[nid], np.array([t, Fx, Fy, Fz, E], ndmin=2), axis=0)
			else:
				results[nid] = np.array([t, Fx, Fy, Fz, E], ndmin=2)
	bndout.close()
	return results

def parseDynaNodout(file):
	# file can either be filename or full file path + name
	results = dict() # nid:numpy array N x 4 with (t, ux, uy, uz) as elements
	nodout = open(file, "r")
	t = None
	isData = False # this is here bc of the weird file setup in nodout files
	for line in nodout:
		if " n o d a l   p r i n t   o u t   f o r   t i m e  s t e p" in line:
			t = float(line.split()[-2]) # get current timestep
		elif " nodal point  x-disp" in line:
			isData = True 
			continue # data is on next line; skip current line
		elif isData:
			# nodout file is delimited in very strange way
			# numbers seem to be delimited by 12 character increments
			# nid is 10 delimited?
			nid = int(line[0:10])
			ux = float(line[10:22])
			uy = float(line[22:34])
			uz = float(line[34:46])
			if nid in results:
				results[nid] = np.append(results[nid], np.array([t, ux, uy, uz], ndmin=2), axis=0)
			else:
				results[nid] = np.array([t, ux, uy, uz], ndmin=2)
			isData = False
	nodout.close()
	return results

def importDynaCardsList(file):
	# file can either be filename or full file path + name
	# reads a file full of LS-Dyna keyword cards and returns a list
	# cards are separated by *
	f = open(file)
	cards = list()
	currentCard = ""
	for line in f:
		if line[0] == "*" and len(currentCard) != 0:
			cards.append(currentCard)
			currentCard = ""
		currentCard += line
	cards.append(currentCard)
	f.close()
	return cards

def objectiveFunction(array, target, start=None, stop=None, step=0.01):
	# evaluates how "close" array and target are
	# array and target must both be two column ndarrays of any number of rows
	# first column is x, second column is y
	# first column must be in monotonically ascending order
	# start and stop are x values that define the domain
	# if start or stop are not provided, the most restrictive domain will be used
	# objective function is 1/nSteps*sum(|array(i)-target(i)|) for every point i defined by step size
	# linear interpolation will be used for intermediate points

	assert(step > 0)
	assert(array.shape[1] == 2)
	assert(target.shape[1] == 2)

	# determine domain
	minStartValue = max(array[0, 0], target[0, 0]) # min start value that user can specify
	maxStopValue = min(array[-1, 0], target[-1, 0]) # max stop value that user can specify
	if start != None:
		assert(start >= minStartValue)
	if stop != None:
		assert(stop <= maxStopValue)
	if start == None:
		start = minStartValue
	if stop == None:
		stop = maxStopValue

	assert(start <= stop)
	assert(stop - start >= step)

	# linearly interpolate both arrays
	arrayInterpolated = interpolateArray(array, start, stop, step)
	targetInterpolated = interpolateArray(target, start, stop, step)

	# calculate objective function (loss function)
	numSteps = int((stop - start)/float(step)) + 1
	return 1/float(numSteps)*np.sum(np.abs(arrayInterpolated[:, 1] - targetInterpolated[:, 1]))

# linearly interpolate an array within domain given by begin, end, and step
def interpolateArray(arr, begin, end, step):
	assert(step <= end - begin)
	assert(step > 0)
	assert(arr[0, 0] <= begin)
	assert(arr[-1, 0] >= end)
	numSteps = int((end - begin)/float(step)) + 1
	result = np.zeros((numSteps, 2))
	for i in range(numSteps):
		x = begin + i*step
		result[i, 0] = x
		# find points bounding x
		# search left to right to find upper bound
		# start from upper bound and search right to left to find lower bound
		x0 = None
		y0 = None
		x1 = None
		y1 = None
		index1 = None
		for j in range(arr.shape[0]):
			if arr[j, 0] >= x: # upper bound found
				x1 = arr[j, 0]
				y1 = arr[j, 1]
				index1 = j
				break
		for j in range(index1, -1, -1):
			if arr[j, 0] <= x: # lower found bound
				x0 = arr[j, 0]
				y0 = arr[j, 1]
				break
		result[i, 1] = linearInterpolate(x0, y0, x1, y1, x)
	return result		

def linearInterpolate(x0, y0, x1, y1, x):
	# given points (x0, y0) and (x1, y1) and point x, linearly interpolate to find y
	# x must lie between the two given x coordinates

	if x0 == x1:
		return (y1 + y0)/float(2)

	# determine order of points
	if x0 < x1:
		X0 = x0
		Y0 = y0
		X1 = x1
		Y1 = y1
	else:
		X0 = x1
		Y0 = y1
		X1 = x0
		Y1 = y0

	# apply linear interpolation formula
	y = Y0 + (x - X0)*(Y1 - Y0)/(X1 - X0)
	return y