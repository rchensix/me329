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
import matplotlib.pyplot as plt
import time

DELAY = 5 # seconds; time between scans for completed jobs

# Postprocess data
def postprocess(directory):
	bndout = util.parseDynaBndout(directory + "bndout")
	nodout = util.parseDynaNodout(directory + "nodout")
	Fz = bndout[37][:,3]
	uz = nodout[37][:,3]
	plt.plot(-uz, -Fz)
	plt.savefig(directory + "load-displacement.png")

# Generate a few lattices
INCLINATION = [10, 15, 20, 25]
EDGE_LENGTH = 10
WALL_HEIGHT = 1
WALL_GRID_SIZE = (2, 3)
LSCARDS = util.importDynaCardsList("defaultcards.k")

# Initialize new Scheduler
mc2 = sch.Scheduler()

HOMEDIRECTORY = "/me329/rchensix/automation_test/workflow_test_V1/"

submittedJobs = set()
completedJobs = set()

jobData = dict() # this will be built into slurmscheduler later

for angle in INCLINATION:
	lattice, movingNodes, fixedNodes = xlt.snap_through_lattice(angle, EDGE_LENGTH, WALL_HEIGHT, WALL_GRID_SIZE)
	directory = HOMEDIRECTORY + "INCLINATION_" + str(angle) + "/"
	sch.mkdir(directory)
	keyFile = directory + "snap_through_" + str(angle) + ".k"
	util.writeKeyFile(lattice, keyFile, size=1, movingNodes=movingNodes, fixedNodes=fixedNodes, cards=LSCARDS)
	fullPath = sch.createLSDynaBashScript(keyFile, outputDirectory=directory)[0]
	jobID = mc2.submit(fullPath)[0]
	submittedJobs.add(jobID)
	jobData[jobID] = directory

# Process any completed jobs
print(submittedJobs)
while(len(submittedJobs) != len(completedJobs)):
	runningJobs = submittedJobs - completedJobs
	# check if any jobs have completed
	for job in runningJobs:
		if mc2.status(job) == 1:
			completedJobs.add(job)
			directory = jobData[job]
			# postprocess(jobData[job]) # I think there's some bug in Python 3.6 where this does not work right
			bndout = util.parseDynaBndout(directory + "bndout")
			nodout = util.parseDynaNodout(directory + "nodout")
			Fz = bndout[37][:,3]
			uz = nodout[37][:,3]
			plt.plot(-uz, -Fz)
			plt.savefig(directory + "load-displacement.png")
	# print queue
	print(sch.squeue()[0])
	print(completedJobs)
	time.sleep(DELAY) # wait