# Written by Ruiqi Chen and Abhishek Tapadar
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
import random

DELAY = 5 # seconds; time between scans for completed jobs
TOLERANCE = 1e-2 # the tolerance for the lattice costs

# Postprocess data
def postprocess(directory):
	bndout = util.parseDynaBndout(directory + "bndout")
	nodout = util.parseDynaNodout(directory + "nodout")
	Fz = bndout[37][:,3]
	uz = nodout[37][:,3]
	plt.plot(-uz, -Fz)
	plt.savefig(directory + "load-displacement.png")

# Generate a few lattices
EDGE_LENGTH = 10
WALL_HEIGHT = 1
WALL_GRID_SIZE = (2, 3)
MAX_MONTE_CARLO_ITER=20
MIN_INCL=0
MAX_INCL=90
LSCARDS = util.importDynaCardsList("defaultcards.k")

# Initialize new Scheduler
mc2 = sch.Scheduler()

HOMEDIRECTORY = "/me329/rchensix/automation_test/workflow_test_V1/"

submittedJobs = set()
completedJobs = set()

jobData = dict() # this will be built into slurmscheduler later

cost_min_lattice=9999999

while cost_min_lattice > tolerance:
    
    for iteration in range(MAX_MONTE_CARLO_ITER):
        angle=random.randint(MIN_INCL,MAX_INCL)
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
                plt.figure()
                plt.plot(-uz, -Fz)
                plt.savefig(directory + "load-displacement.png")
                plt.close()
          # print queue
        print(sch.squeue()[0])
        print(completedJobs)
        time.sleep(DELAY) # wait
    
    
    costs=[]
    while completedJob in completedJobs:
    
        directory = jobData[completedJob]
        bndout = util.parseDynaBndout(directory + "bndout")
        nodout = util.parseDynaNodout(directory + "nodout")
    
        Fz = bndout[37][:,3]
        uz = nodout[37][:,3]
    
        cost_lattice=util.objectiveFunction([[f,u] for f,u in zip(Fz,uz)],target_array)
    
        costs.add[(directory,cost_lattice)]
        
    costs=sorted(costs, key=lambda x:x[1])
    
    cost_min_lattice=costs[0][0]
    
    angle1 = int(re.search('INCLINATION_(.+?)/', costs[0][0]).group(1))
    
    angle2 = int(re.search('INCLINATION_(.+?)/', costs[3][0]).group(1))
    
    MIN_INCL= angle1 if angle1<angle2 else angle2
    MAX_INCL=angle1+angle2-MIN_INCL
    
    