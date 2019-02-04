# Written by Ruiqi Chen
# February 4, 2019
# This module contains a collection of functions to automate the PrePost process

import math
import networkx

def writeKeyFile(G, outputFile, size=1, movingNodes=None, fixedNodes=None, cards=None):
	# Creates a LS-Dyna outputFile.k file with elements found in lattice G, 
	# predefined velocity conditions on movingNodes, spc boundary conditions on fixedNodes,
	# and appends any additional inputcards at the end
	# cards is a list of strings
	
	file = open(outputFile, "w")

	# mesh the lattice
	elements, allNodes = meshBeamEdges(G, size)

	# write nodes
	file.write("*NODES\n")
	file.write("$#   nid               x               y               z      tc      rc\n")
	writeNodes(file, allNodes)

	# write elements
	file.write("*ELEMENT_BEAM\n")
	file.write("$#   eid     pid      n1      n2      n3     rt1     rr1     rt2     rr2   local\n")
	writeElements(file, elements)

	# write prescribed velocity (moving nodes)
	file.write("*BOUNDARY_PRESCRIBED_MOTION_NODE\n")
	file.write("$#     nid       dof       vad      lcid        sf       vid     death     birth\n")
	writePrescribedVelocity(file, movingNodes)

	# write spc boundary conditions (fixed nodes)
	file.write("*BOUNDARY_SPC_NODE\n")
	file.write("$#     nid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz\n")
	writeSPC(file, fixedNodes)

	# write cards
	if cards != None and len(cards) != 0:
		for card in cards:
			file.write(card + "\n")

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
	for e in G.edges:
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