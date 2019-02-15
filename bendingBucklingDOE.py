# Written by Ruiqi Chen
# February 13, 2019
# This code generates a DoE for a combined bending/buckling structure

import sys
sys.path.insert(1, '/me329/rchensix/.local/lib/python3.6/site-packages/')
import networkx as nx
import xlattice as xlt
import dynautil as util
import slurmscheduler as sch
import matplotlib.pyplot as plt
import time
import math
import numpy as np


HOMEDIRECTORY = "/me329/rchensix/bending_buckling/V1/"
LSCARDS = util.importDynaCardsList("defaultcards.k")
DELAY = 60 # seconds; time between scans for completed jobs
THETA_SWEEP = [30, 45, 60, 75, 90, 105, 120, 135, 150]
THETA_SWEEP_BABY = [40, 95]
AR_SWEEP = [5, 7.5, 10, 12.5, 15, 17.5, 20]
AR_SWEEP_BABY = [12, 16]
NCPU = 2

SUBMIT_DELAY = 60 # not used currently

def postProcess(directory):
	bndout = util.parseDynaBndout(directory + "bndout")
	nodout = util.parseDynaNodout(directory + "nodout")
	Fz = bndout[1][:,3]
	uz = nodout[1][:,3]
	plt.figure()
	plt.plot(-uz, -Fz)
	plt.xlabel("Displacement (m)")
	plt.ylabel("Force (N)")
	plt.savefig(directory + "load-displacement.png")
	plt.close()

def bendingBucklingLattice(theta12, theta23, AR1, AR2, AR3, length=10):
	# Angles are defined in degrees!
	# AR is defined as length/diameter
	# beams are numbered left (-x) to right (+x)
	theta12 = theta12*math.pi/180
	theta23 = theta23*math.pi/180
	G = nx.Graph()
	G.add_node(1, pos=(0, 0, length))
	G.add_node(2, pos=(0, 0, 0))
	G.add_node(3, pos=(-length*math.sin(theta12), 0, length - length*math.cos(theta12)))
	G.add_node(4, pos=(length*math.sin(theta23), 0, length - length*math.cos(theta23)))
	G.add_edge(1, 2, diameter=length/AR2) # center beam
	G.add_edge(1, 3, diameter=length/AR1) # left beam
	G.add_edge(1, 4, diameter=length/AR3) # right beam
	return xlt.Lattice(G)

def workflow(thetaSweep, ARSweep, length=10, verbose=2):
	mc2 = sch.Scheduler()
	submittedJobs = set()
	completedJobs = set()
	jobData = dict()
	for theta12 in thetaSweep:
		for theta23 in thetaSweep:
			for AR1 in ARSweep:
				for AR2 in ARSweep:
					for AR3 in ARSweep:
						directory = HOMEDIRECTORY + "T12_" + str(theta12) + "_T23_" + str(theta23) + "_AR1_" + str(AR1) + "_AR2_" + str(AR2) + "_AR3_" + str(AR3) + "/"
						sch.mkdir(directory)
						lattice = bendingBucklingLattice(theta12, theta23, AR1, AR2, AR3, length)
						keyFile = directory + "bendingBucklingLattice_" + "T12_" + str(theta12) + "_T23_" + str(theta23) + "_AR1_" + str(AR1) + "_AR2_" + str(AR2) + "_AR3_" + str(AR3) + ".k"
						SPCNodesAndDOF = [[set(list(range(5, 32))), (0, 1, 0, 1, 0, 1)]]
						util.generateKeyFile(lattice, keyFile, movingNodes=[1], fixedNodes=[2, 3, 4], SPCNodesAndDOF=SPCNodesAndDOF, cards=LSCARDS)
						fullPath = sch.createLSDynaBashScript(keyFile, outputDirectory=directory, numCPU=NCPU)[0]
						jobID = mc2.submit(fullPath)[0]
						submittedJobs.add(jobID)
						jobData[jobID] = directory
	# Process any completed jobs
	print("Submitted jobs: " + str(submittedJobs) + "\n")
	while(len(submittedJobs) != len(completedJobs)):
		runningJobs = submittedJobs - completedJobs
		if verbose >= 2: 
			print("Completed jobs: " + str(completedJobs) + "\n")
			print("Running jobs: " + str(runningJobs) + "\n")
		if verbose >= 3:
			print(sch.squeue()[0])
		# check if any jobs have completed
		for job in runningJobs:
			if verbose >= 4: print("Status of job " + str(job) + ": " + str(mc2.status(job)) + "\n")
			if mc2.status(job) == 1:
				completedJobs.add(job)
				directory = jobData[job]
				postProcess(jobData[job])
		# print queue
		time.sleep(DELAY) # wait

workflow(THETA_SWEEP_BABY, AR_SWEEP_BABY, length=10) # use the BABY SWEEPS to test
# workflow(THETA_SWEEP, AR_SWEEP, length=10)