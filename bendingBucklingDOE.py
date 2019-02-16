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
import os

KILL_FILE = "terminate.txt"
LOG_FILE = "log.txt"

HOMEDIRECTORY = "/me329/rchensix/bending_buckling/V3/"
LSCARDS = util.importDynaCardsList("defaultcards.k")
DELAY = 5 # seconds; time between scans for completed jobs
PRINT_EVERY = 600 # every 10 minutes; for verbose mode 1
THETA_SWEEP = [30, 45, 60, 75, 90, 105, 120, 135, 150]
THETA_SWEEP_BABY = [40, 95]
AR_SWEEP = [10, 12, 14, 16, 18, 20]
AR_SWEEP_BABY = [12, 16]
NCPU = 24
NCPU_MAX = 100 # mc2 cluster limit (plus safety factor)
MAX_JOBS_SIMULTANEOUS = 3

THETA_12_SWEEP = [75, 80, 85, 90, 95, 100, 105]
THETA_23_SWEEP = [30, 35, 40, 45, 50, 55, 60]

POSTPROCESS_DELAY = 10 # to try to limit cases where postProcess is called before LS-Dyna can write the output files

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

def serializedWorkflow(theta12Sweep, theta23Sweep, ARSweep, length=10, verbose=1):
	mc2 = sch.Scheduler()
	for theta12 in theta12Sweep:
		for theta23 in theta23Sweep:
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
						if verbose == 1: 
							with open(HOMEDIRECTORY + LOG_FILE, "a") as myfile:
								myfile.write("Submitted job " + str(jobID) + ": " + keyFile + "\n")
						while(True):
							# Check termination file
							if os.path.isfile(HOMEDIRECTORY + KILL_FILE):
								with open(HOMEDIRECTORY + LOG_FILE, "a") as myfile:
									myfile.write("Termination file found! Execution forcefully terminated!")
								raise Exception("Termination file found! Execution forcefully terminated!")
							# Holding pattern loop
							# get status of job
							if mc2.status(jobID) == 1:
								break
							time.sleep(DELAY)
						# post process completed job
						time.sleep(POSTPROCESS_DELAY)
						try:
							postProcess(directory)
						except:
							with open(HOMEDIRECTORY + LOG_FILE, "a") as myfile:
									myfile.write("Could not extract data from " + keyFile + "\n")
						else:
							with open(HOMEDIRECTORY + LOG_FILE, "a") as myfile:
									myfile.write("Successfully extracted data from " + keyFile + "\n")
						


"""	
	print("Created jobs: " + str([x[0] for x in createdJobs]) + "\n")
	printCounter = 0
	# Submit first job so while loop runs
	jobPath, directory = createdJobs.pop()
	jobID = mc2.submit(jobPath)[0]
	submittedJobs.add(jobID)
	jobData[jobID] = directory

	# Submit created jobs and process any completed jobs
	while(len(submittedJobs) != len(completedJobs)):
		# check if a job can be submitted
		runningJobs = submittedJobs - completedJobs
		if len(runningJobs) < MAX_JOBS_SIMULTANEOUS and len(createdJobs) > 0:
			jobPath, directory = createdJobs.pop()
			jobID = mc2.submit(jobPath)[0]
			submittedJobs.add(jobID)
			jobData[jobID] = directory

		# print statements
		if int(ceil(PRINT_EVERY/DELAY)) - 1 == printCounter:
			if verbose == 1:
				print("Submitted jobs: " + str(submittedJobs) + "\n")
				print("Completed jobs: " + str(completedJobs) + "\n")
				print("Running jobs: " + str(runningJobs) + "\n")
			printCounter = 0
		if verbose >= 2: 
			print("Submitted jobs: " + str(submittedJobs) + "\n")
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

		time.sleep(DELAY) # wait
		printCounter += 1
"""

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
	printCounter = 0
	while(len(submittedJobs) != len(completedJobs)):
		runningJobs = submittedJobs - completedJobs
		if verbose == 1 and int(ceil(PRINT_EVERY/DELAY)) - 1 == printCounter:
			print("Completed jobs: " + str(completedJobs) + "\n")
			print("Running jobs: " + str(runningJobs) + "\n")
			printCounter = 0
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
		printCounter += 1

# workflow(THETA_SWEEP_BABY, AR_SWEEP_BABY, length=10) # use the BABY SWEEPS to test
# workflow(THETA_SWEEP, AR_SWEEP, length=10)
serializedWorkflow(THETA_12_SWEEP, THETA_23_SWEEP, AR_SWEEP, length=10)