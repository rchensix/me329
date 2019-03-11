import xlattice as xlt
import dynautil as util
import slurmscheduler as sch
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import latticeDatabase as db
import os
import time

DELAY = 5
POSTPROCESS_DELAY = 10

def defaultSimParams():
	simParams = dict()
	simParams["ncpu"] = 24
	simParams["logFile"] = "log.txt"
	simParams["killFile"] = "terminate.txt"
	simParams["cardFile"] = "defaultcards.k"
	simParams["directory"] = os.getcwd()
	simParams["velocity"] = 0.05
	return simParams

def fullFactorialSimulation(latticeGenerator, homeDirectory=None, **kwargs):
	# creates and submits a design of experiments simulation using all variables in *args and **kwargs
	# for example, suppose we want to make a cubic lattice with function signature
	# cubicLattice(length, width, height)
	# and we want to set length to [1, 3, 5], width to [2, 4, 6], and hold height constant at 10
	# we could call doeSimulation(cubicLattice, length=[1, 3, 5], width=[2, 4, 6], height=10)

	# some helper methods

	def backtrack(keys, i, parameters):
		# i is which index of kwargs currently iterating through
		# parameters is a dict of currently chosen lattice parameters

		# base case: i == len(kwargs); submit the job, analyze, and return
		if i == len(kwargs):
			simulateLattice(latticeGenerator, parameters, simParams=simParams, scheduler=mc2)
		# recursive case: 
		else:
			key = keys[i] # this is the i-th key in kwargs
			for val in kwargs[key]:
				# val is a particular lattice parameter of key
				parameters[key] = val # add to dict
				backtrack(keys, i + 1, parameters)
				# note: no need to pop the old key (as in typical backtracking) because setting a new value will do the same thing

	if homeDirectory == None:
		homeDirectory = os.getcwd()
	parameters = dict()
	mc2 = sch.Scheduler()
	simParams = defaultSimParams()
	simParams["directory"] = homeDirectory
	backtrack(list(kwargs.keys()), 0, parameters)

def simulateLattice(latticeGenerator, latticeParameters, simParams=None, scheduler=None):
		if simParams == None:
			simParams = defaultSimParams()
		l = latticeGenerator(**latticeParameters)
		latticeParameterString = ""
		for key in latticeParameters:
			latticeParameterString += str(key) + "_" + str(latticeParameters[key]) + "__"
		simDirectory = os.path.join(simParams["directory"], latticeParameterString)
		sch.mkdir(simDirectory)
		keyFile = os.path.join(simDirectory, latticeParameterString + ".k")
		cards = util.importDynaCardsList(simParams["cardFile"])
		util.generateKeyFile(l, keyFile, cards=cards)
		simPath = sch.createLSDynaBashScript(keyFile, outputDirectory=simDirectory, numCPU=simParams["ncpu"])[0]
		print("simPath: " + str(simPath))
		jobID = scheduler.submit(simPath)[0]
		with open(os.path.join(simParams["directory"], simParams["logFile"]), "a") as file:
			file.write("Submitted job " + str(jobID) + ": " + keyFile + "\n")
		while(True):
			# Check termination file
			if os.path.isfile(os.path.join(simParams["directory"], simParams["killFile"])):
				with open(os.path.join(simParams["directory"], simParams["logFile"]), "a") as file:
					file.write("Termination file found! Execution forcefully terminated!")
				raise Exception("Termination file found! Execution forcefully terminated!")
			# Holding pattern loop
			# get status of job
			if scheduler.status(jobID) == 1:
				break
			time.sleep(DELAY)
		# post process completed job
		time.sleep(POSTPROCESS_DELAY)
		try:
			postProcess(simDirectory, simParams["velocity"])
		except:
			with open(os.path.join(simParams["directory"], simParams["logFile"]), "a") as file:
					file.write("Could not extract data from " + keyFile + "\n")
		else:
			with open(os.path.join(simParams["directory"], simParams["logFile"]), "a") as file:
					file.write("Successfully extracted data from " + keyFile + "\n")

def postProcess(directory, velocity, outputData=False):
	bndout = util.parseDynaBndout(os.path.join(directory, "bndout"))
	firstRunFlag = True
	simTime = None
	for node in bndout:
		if firstRunFlag:
			Fz = bndout[node][:, 3]
			simTime = bndout[node][:, 0]
			firstRunFlag = False
		else:
			Fz += bndout[node][:, 3]
	plt.figure()
	plt.plot(velocity*simTime, -Fz)
	plt.xlabel("Displacement (m)")
	plt.ylabel("Force (N)")
	plt.savefig(os.path.join(directory, "load-displacement.png"))
	plt.close()
	if outputData:
		return (velocity*simTime, -Fz)