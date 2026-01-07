# -*- coding: utf-8 -*-


import Problem, Solution, Route
from ALNS import ALNS
import time

# List of instances to solve
instances = ["instances/c202C16.txt",
             "instances/lc102.txt",
             "instances/lc108.txt",
             "instances/lc207.txt",
             "instances/lr112.txt",
             "instances/lr205.txt",
             "instances/lrc104.txt",
             "instances/lrc206.txt",
             "instances/r102C18.txt",
             "instances/rc204C16.txt"]

# Number of destroy and repair operators
nDestroyOps = 4
nRepairOps = 3

# Select the instance(s) to solve
test = instances[6]

# Solve the instance(s) and track the total runtime
starttime = time.time()
print(f"Solving instance {test}")
problem = Problem.PDPTW.readInstance(test)
print(problem)
alns = ALNS(problem, nDestroyOps, nRepairOps)
alns.execute()
endtime = time.time()

print(f"Total time: {endtime - starttime} seconds")
