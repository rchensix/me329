import subprocess
import os

class Scheduler:
  # contains a database of submitted jobs
  # provides methods to submit job using SLURM and get status of submitted jobs
  
  # Written by Ruiqi Chen
  # Version 1.0
  # February 1, 2019
  
  def __init__(self):
  # this creates a new Scheduler object with initially empty database
    self.database = dict() # this stores jobID:status pairs where jobID is a unique identifier to a submitted job, and status is 1 (completed) or 0 (else)
    
  def submit(self, file, flags=""):
  # submits file using sbatch and returns (jobID, out, err); adds jobID:0 to database
  # if submission encounters an error, jobID is set to None
  # additional arguments can be specified by the flags string
  # this method will send "sbatch file flags" to the shell
  # NOTE: a space is automatically added between file and flags, but any spaces in flags must be specified in flags itself
    jobID, out, err = sbatch(file, flags)
    if jobID != None: self.database[jobID] = 0
    return (jobID, out, err)

  def update(self):
  # updates the status for all submitted jobs by calling squeue
    out = squeue()[0]
    enqueued = self.parseQueue(out)
    for jobID  in self.database:
      if jobID not in enqueued and self.database[jobID] == 0:
        self.database[jobID] = 1 # job is completed
        
  def status(self, jobID=None):
  # returns status of jobID if given, otherwise returns database
  # if invalid jobID given, returns None
    if jobID != None: jobID = str(jobID) # convert to string
    if (jobID != None) and (jobID in self.database) and (self.database[jobID] == 1):
      return 1
    self.update()
    if jobID != None:
      if jobID in self.database: return self.database[jobID]
      return None
    else:
      return self.database
    
  def clear():
  # clears the database of all jobs
    self.database = dict()
    
  ### HELPER METHODS ###
  
  def parseQueue(self, out):
    # returns of set of all jobIDs in the queue (including ones not submitted by Scheduler)
    enqueued = set()
    for line in out.split("\n"):
      if len(line) > 1: # there's some weird bug with one character blank line
        jobID = line.split()[0]
        if jobID != "JOBID":
          enqueued.add(jobID)
    return enqueued
  
def sbatch(file, flags=""):
# submits file using sbatch and returns (jobID, out, err); adds jobID:0 to database
# if submission encounters an error, jobID is set to None
# additional arguments can be specified by the flags string
# this method will send "sbatch file flags" to the shell
# NOTE: a space is automatically added between file and flags, but any spaces in flags must be specified in flags itself
  out, err = shell("sbatch " + file + " " + flags)
  if len(out) != 0:
    jobID = out.split()[-1] # NOTE: this may need to be updated in a future version to be truly unique (not sure exactly how SLURM assigns jobIDs)
  else:
    jobID = None
  return (jobID, out, err)
  
def squeue(flags=""):
# calls "squeue flags" in shell and returns output
# NOTE: a space is automatically added between squeue and flags, but any spaces in flags must be specified in flags itself
  return shell("squeue " + flags)

def cd(flags=""):
  # calls "cd flags" in shell and returns output
  # NOTE: a space is automatically added between squeue and flags, but any spaces in flags must be specified in flags itself
  return shell("cd " + flags)

def mkdir(flags=""):
  # calls "cd flags" in shell and returns output
  # NOTE: a space is automatically added between squeue and flags, but any spaces in flags must be specified in flags itself
  return shell("mkdir " + flags)

def shell(input):
  # generic shell call used by other methods
  # calls input from shell and returns output
  popen = subprocess.Popen(input, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = popen.communicate()
  return out.decode("utf8"), err.decode("utf8") # WARNING: the decode part is needed for Python 3

def createScript(script, outputFileName):
  # creates a script file out of input script
  # input can be either string or list of strings
  # if input is string, function will take string and directly create a bash file using it (you need to include \n yourself)
  # if input is a list of strings, function will put each element on its own line before writing to bash file (you don't need to include \n yourself)
  # output file name is outputFileName (will automatically overwrite existing!)
  # NOTE: no shebangs are included--put everything in script!
  file = open(outputFileName, "w")
  if isinstance(script, str): # WARNING: This will NOT work on Python 2! Need to change type to basestring
    file.write(script)
  elif isinstance(script, list):
    for line in script:
      file.write(line + "\n")
  else:
    raise Exception("Unsupported input variable type used for script")
  file.close()

def createLSDynaBashScript(keyFile, directory=None, outputFile=None, outputDirectory=None, jobName=None, maxTime=None, numNode=None, numCPU=None):
  # creates a LSDyna bash script to run on mc2 cluster
  # if directory is not specified, current working directory is assumed
  # if outputFile is not specified, output will be keyFile.sh
  # if outputDirectory is not specified, directory will be used
  # if jobName is not specified, keyFile is also used as the jobName
  # to specify maxTime, use HH:MM:SS string format
  # if maxTime is not specified, default maxTime will be 02:00:00 (2 hours)
  # default numNode = 1
  # default numCPU = 24
  DEFAULT_MAX_TIME = "02:00:00"
  if directory == None:
    directory = os.getcwd()
  if outputFile == None:
    outputFile = keyFile + ".sh"
  if outputDirectory == None:
    outputDirectory = directory
  if jobName == None:
    jobName = keyFile
  if maxTime == None:
    maxTime = DEFAULT_MAX_TIME
  if numNode == None:
    numNode = 1
  if numCPU == None:
    numCPU = 24
  fullPath = os.path.join(outputDirectory, outputFile)
  script = ["#!/bin/bash",
    "#SBATCH -J " + jobName,
    "#SBATCH -o " + jobName + ".out",
    "#SBATCH -t " + maxTime,
    "#SBATCH -N " + str(numNode),
    "#SBATCH -n " + str(numCPU),
    "#SBATCH -D " + outputDirectory,
    "module purge",
    "module load intel/Developer-2018.1",
    "module load apps/ls-dyna/9.1.0",
    "echo The master node of this job is `hostname`",
    "echo This job runs on the following nodes:",
    "echo `cat $SLURM_JOB_NODELIST `",
    "ls-dyna_smp_s_r910_x64_redhat56_ifort131 I= " + os.path.join(directory, keyFile) + " NCPU= " + str(numCPU)]
  createScript(script, fullPath)
  return fullPath, os.path.dirname(fullPath)