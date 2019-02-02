import subprocess

class Scheduler:
  # contains a database of submitted jobs
  # provides methods to submit job using SLURM and get status of submitted jobs
  
  # Written by Ruiqi Chen
  # Version 1.0
  # February 1, 2019
  
  def __init__(self):
  # this creates a new Scheduler object with initially empty database
    self.database = dict() # this stores jobID:status pairs where jobID is a unique identifier to a submitted job, and status is 1 (completed) or 0 (else)
    
  def sbatch(self, file, flags=""):
  # submits file using sbatch and returns (jobID, out, err); adds jobID:0 to database
  # if submission encounters an error, jobID is set to None
  # additional arguments can be specified by the flags string
  # this method will send "sbatch file flags" to the shell
  # NOTE: a space is automatically added between file and flags, but any spaces in flags must be specified in flags itself
    popen = subprocess.Popen("sbatch " + file + flags, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = popen.communicate()
    if len(out) != 0:
      jobID = out.split()[-1] # NOTE: this may need to be updated in a future version to be truly unique (not sure exactly how SLURM assigns jobIDs)
      self.database[jobID] = 0
    else:
      jobID = None
    return (jobID, out, err)
  
  def squeue(self, flags=""):
  # calls "squeue flags" in shell and returns output
  # NOTE: a space is automatically added between squeue and flags, but any spaces in flags must be specified in flags itself
    popen = subprocess.Popen("squeue " + flags, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = popen.communicate()
    return out
    
  def update(self):
  # updates the status for all submitted jobs by calling squeue
    out = self.squeue()
    enqueued = self.parseQueue(out)
    for jobID  in self.database:
      if jobID not in enqueued and self.database[jobID] == 0:
        self.database[jobID] = 1 # job is completed
        
  def status(self, jobID=None):
  # returns status of jobID if given, otherwise returns database
  # if invalid jobID given, returns None
    if jobID != None: jobID = str(jobID) # convert to string
    if jobID != None and jobID in self.database and self.database[jobID] == 1:
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
    # f = open("out.out", "w+") # debugging
    # f.write(out) # debugging
    # f.close() # debugging
    enqueued = set()
    for line in out:
      # print(len(line)) # debugging
      if len(line) > 1: # there's some weird bug with one character blank line
        jobID = line.split()[0]
        if jobID != "JOBID":
          enqueued.add(jobID)
    return enqueued