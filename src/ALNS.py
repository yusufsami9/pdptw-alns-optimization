# -*- coding: utf-8 -*-

from Solution import Solution
import random, time
import numpy as np
import matplotlib.pyplot as plt
import sys


class Parameters:
    """
    Class that holds all the parameters for ALNS
    """
    nIterations = 100  # number of iterations of the ALNS
    minSizeNBH = 1  # minimum neighborhood size
    maxSizeNBH = 45  # maximum neighborhood size
    randomSeed = 1  # value of the random seed
    temperature = 1000  # starting temperature
    cooling_rate = 0.95  # cooling rate, adjust to control speed of cooling
    decay = 0.75  # decay factor for weights of operators
    scoreWeights = [1, 0.5, 0.3, 0.1]  # weights for the different score criterions
    # can add parameters such as cooling rate etc.


class ALNS:
    """
    Class that models the ALNS algorithm.

    Parameters
    ----------
    problem : PDPTW
        The problem instance that we want to solve.
    nDestroyOps : int
        number of destroy operators.
    nRepairOps : int
        number of repair operators.
    randomGen : Random
        random number generator
    currentSolution : Solution
        The current solution in the ALNS algorithm
    bestSolution : Solution
        The best solution currently found
    bestDistance : int
        Distance of the best solution

    """

    def __init__(self, problem, nDestroyOps, nRepairOps):
        self.problem = problem
        self.nDestroyOps = nDestroyOps
        self.nRepairOps = nRepairOps
        self.randomGen = random.Random(Parameters.randomSeed)  # used for reproducibility

        # Initialize parameters for operator selection
        self.destroyOperatorWeights = [1 / self.nDestroyOps] * self.nDestroyOps
        self.repairOperatorWeights = [1 / self.nRepairOps] * self.nRepairOps

        # Initialize temperature and cooling rate
        self.temperature = Parameters.temperature
        self.coolingRate = Parameters.cooling_rate

        # Initialize values relevant for updating operator weights
        self.decay = Parameters.decay
        self.scoreWeights = Parameters.scoreWeights

        self.nLines = problem.nLines

        self.iterations = Parameters.nIterations

        # Create datalog dictionary to store relevant data for later analysis
        self.datalog = {
            "Iteration": [],
            "CurrentDistance": [],
            "BestDistance": [],
            "Temperature": [],
            "DestroyOpNr": [],
            "RepairOpNr": [],
            "DestroyWeights": [],
            "RepairWeights": [],
            "SizeNBH": [],
            "ScoreCriterion": [],
            "Feasibility": []
        }

    def constructInitialSolution(self):
        """
        Method that constructs an initial solution using random insertion
        """

        self.currentSolution = Solution(self.problem, list(), list(), list(self.problem.requests.copy()))
        self.currentSolution.executeRandomInsertion(self.randomGen)
        self.currentSolution.computeDistance()
        self.bestSolution = self.currentSolution.copy()
        self.bestDistance = self.currentSolution.distance
        print("Created initial solution with distance: " + str(self.bestDistance))

    def execute(self):
        """
        Method that executes the ALNS
        """

        starttime = time.time()  # get the start time
        self.constructInitialSolution()
        for i in range(self.iterations):
            # copy the current solution
            self.tempSolution = self.currentSolution.copy()

            # decide on the size of the neighbourhood
            sizeNBH = self.randomGen.randint(Parameters.minSizeNBH, Parameters.maxSizeNBH)

            # decide on the destroy and repair operator numbers
            destroyOpNr = self.determineDestroyOpNr()
            repairOpNr = self.determineRepairOpNr()

            # execute the destroy and the repair and evaluate the result
            self.destroyAndRepair(destroyOpNr, repairOpNr, sizeNBH);
            self.tempSolution.computeDistance()
            print("Iteration " + str(i) + ": Found solution with distance: " + str(self.tempSolution.distance))
            # self.tempSolution.print()

            # determine if the new solution is accepted
            self.checkIfAcceptNewSol()

            # Store data for later analysis
            if self.tempSolution.distance >= 0.1 * sys.maxsize:
                self.updateDatalog(destroyOpNr, repairOpNr, sizeNBH, False)
            else:
                self.updateDatalog(destroyOpNr, repairOpNr, sizeNBH, True)
            # update the ALNS weights
            self.updateWeights(destroyOpNr, repairOpNr)

        endtime = time.time()  # get the end time
        cpuTime = round(endtime - starttime)
        print("Terminated. Final distance: " + str(self.bestSolution.distance) + ", cpuTime: " + str(
            cpuTime) + " seconds")

        self.createVisualizations()

    def checkIfAcceptNewSol(self):
        """
        Method that checks if we accept the newly found solution
        """

        # if we found a global best solution, we always accept
        if self.tempSolution.distance < self.bestDistance:
            self.bestDistance = self.tempSolution.distance
            self.bestSolution = self.tempSolution.copy()
            self.currentSolution = self.tempSolution.copy()
            self.scoreCriterion = 1
            print("Found new global best solution.")

        # Simulated annealing acceptance criterion
        elif self.tempSolution.distance < self.currentSolution.distance:
            self.currentSolution = self.tempSolution.copy()
            self.scoreCriterion = 2
            print("Improved new current solution.")

        else:
            # Determine acceptance probability
            difference = self.tempSolution.distance - self.currentSolution.distance
            acceptanceProbability = np.exp(-difference / self.temperature)

            # Draw a random number between 0 and 1
            randomValue = self.randomGen.random()
            if randomValue < acceptanceProbability:
                self.currentSolution = self.tempSolution.copy()
                self.scoreCriterion = 3
                print("Accepted worse solution.")
            else:
                self.scoreCriterion = 4
                print("Rejected worse solution.")

        # Decrease temperature according to cooling schedule
        self.temperature *= self.coolingRate

    def updateWeights(self, destroyOpNr, repairOpNr):
        """
        Method that updates the weights of the destroy and repair operators

        Parameters
        ----------
        destroyOpNr : int
            number of the destroy operator that was applied.
        repairOpNr : int
            number of the repair operator that was applied.
        """
        selectedScoreWeight = self.scoreWeights[self.scoreCriterion - 1]

        self.repairOperatorWeights[repairOpNr - 1] = self.decay * self.repairOperatorWeights[repairOpNr - 1] + (
                    1 - self.decay) * selectedScoreWeight
        self.destroyOperatorWeights[destroyOpNr - 1] = self.decay * self.destroyOperatorWeights[destroyOpNr - 1] + (
                    1 - self.decay) * selectedScoreWeight

        # Normalize weights to avoid unwanted bias
        self.normalizeWeights()

        # print(f"Updated weights: Destroy {self.destroyOperatorWeights}, Repair {self.repairOperatorWeights}")
        print(f"Used operators: Destroy {destroyOpNr}, Repair {repairOpNr}")
        print(f"Score criterion: {self.scoreCriterion} with weight {selectedScoreWeight}")

    def normalizeWeights(self):
        """
        Method that normalizes the weights of the destroy and repair operators
        to ensure they sum to 1.
        """

        self.destroyOperatorWeights = [weight / sum(self.destroyOperatorWeights) for weight in
                                       self.destroyOperatorWeights]
        self.repairOperatorWeights = [weight / sum(self.repairOperatorWeights) for weight in self.repairOperatorWeights]

    def updateDatalog(self, destroyOpNr, repairOpNr, sizeNBH, feasibility):
        """
        Method that stores relevant data for later analysis. Data that is being stored:

        Parameters
        ----------
        destroyOpNr : int
            number of the destroy operator that was applied.
        repairOpNr : int
            number of the repair operator that was applied.
        sizeNBH : int
            size of the neighborhood.
        feasibility : boolean
            True if the temporary solution is feasible, else False.
        """

        self.datalog["Iteration"].append(len(self.datalog["Iteration"]) + 1)
        self.datalog["CurrentDistance"].append(self.currentSolution.distance)
        self.datalog["BestDistance"].append(self.bestSolution.distance)
        self.datalog["Temperature"].append(self.temperature)
        self.datalog["DestroyOpNr"].append(destroyOpNr)
        self.datalog["RepairOpNr"].append(repairOpNr)
        self.datalog["DestroyWeights"].append(self.destroyOperatorWeights.copy())
        self.datalog["RepairWeights"].append(self.repairOperatorWeights.copy())
        self.datalog["SizeNBH"].append(sizeNBH)
        self.datalog["ScoreCriterion"].append(self.scoreCriterion)
        self.datalog["Feasibility"].append(feasibility)

    def determineDestroyOpNr(self):
        """
        Method that determines the destroy operator that will be applied.
        Initial version: we just pick a random one with equal probabilities.
        Updated version: weighted random selection, based on operator weights

        Returns
        -------
        choice : int
            Number of the destroy operator chosen, between 1 and nDestroyOps.
        """
        # Initial version: equal probabilities
        # return self.randomGen.randint(1, self.nDestroyOps)

        # Updated version: weighted random selection
        totalWeight = sum(self.destroyOperatorWeights)
        probabilities = [weight / totalWeight for weight in self.destroyOperatorWeights]
        return self.randomGen.choices(range(1, self.nDestroyOps + 1), weights=probabilities, k=1)[0]

    def determineRepairOpNr(self):
        """
        Method that determines the repair operator that will be applied.
        Initial version: we just pick a random one with equal probabilities.
        Updated version: weighted random selection, based on operator weights

        Returns
        -------
        choice : int
            Number of the repair operator chosen, between 1 and nRepairOps.
        """
        # Initial version: equal probabilities
        # return self.randomGen.randint(1, self.nDestroyOps)

        # Updated version: weighted random selection
        totalWeight = sum(self.repairOperatorWeights)
        probabilities = [weight / totalWeight for weight in self.repairOperatorWeights]
        return self.randomGen.choices(range(1, self.nRepairOps + 1), weights=probabilities, k=1)[0]

    def destroyAndRepair(self, destroyHeuristicNr, repairHeuristicNr, sizeNBH):
        """
        Method that performs the destroy and repair. More destroy and/or
        repair methods can be added

        Parameters
        ----------
        destroyHeuristicNr : int
            number of the destroy operator.
        repairHeuristicNr : int
            number of the repair operator.
        sizeNBH : int
            size of the neighborhood.
        """

        # perform the destroy
        if destroyHeuristicNr == 1:
            self.tempSolution.executeRandomRemoval(sizeNBH, self.randomGen)
        elif destroyHeuristicNr == 2:
            self.tempSolution.executeWorstRemoval(sizeNBH)
        elif destroyHeuristicNr == 3:
            self.tempSolution.executeShawRemoval(sizeNBH)
        else:
            self.tempSolution.executeTimeOrientedRemoval(sizeNBH)

        # perform the repair
        if repairHeuristicNr == 1:
            self.tempSolution.executeRandomInsertion(self.randomGen)
        elif repairHeuristicNr == 2:
            self.tempSolution.executeGreedyInsertion()
        else:
            self.tempSolution.executeRegretKInsertion()

    def createVisualizations(self):
        """
        Method that creates visualizations of the best solution found

        Possible plots:
        - Plot destroy/repair operator weights over time
        - Plot temperature evolution over time
        - Plot the total cost of the solution over time, together with the best cost found
        """

        # Weight adjustment over time - needs adjustments
        plt.figure(figsize=(10, 6))
        for i in range(self.nDestroyOps):
            values = [weights[i] for weights in self.datalog["DestroyWeights"]]
            plt.plot(self.datalog["Iteration"], values, label=f'Destroy Op {i + 1}')
        plt.title('Destroy operator weights over time')
        plt.xlabel('Iteration [-]')
        plt.ylabel('Weight [-]')
        plt.legend()
        plt.show()

        plt.figure(figsize=(10, 6))
        for i in range(self.nRepairOps):
            values = [weights[i] for weights in self.datalog["RepairWeights"]]
            plt.plot(self.datalog["Iteration"], values, label=f'Repair Op {i + 1}')
        plt.title('Repair operator weights over time')
        plt.xlabel('Iteration [-]')
        plt.ylabel('Weight [-]')
        plt.legend()
        plt.show()

        # # Temperature evolution
        # plt.figure(figsize=(10, 6))
        # plt.plot(self.datalog["Temperature"], label='Temperature')
        # plt.title('Temperature over time')
        # plt.xlabel('Iteration [-]')
        # plt.ylabel('Temperature [*C]')
        # plt.legend()
        # plt.show()

        # Cost evolution and best cost over time
        plt.figure(figsize=(10, 6))
        plt.plot(self.datalog["CurrentDistance"], label='Current Distance')
        plt.plot(self.datalog["BestDistance"], label='Best Distance')
        plt.title('Route distance over time')
        plt.xlabel('Iteration [-]')
        plt.ylabel('Distance [m]')
        plt.legend()
        plt.show()

        # Determine feasibility percentage
        numberFeasible = 0
        for value in self.datalog["Feasibility"]:
            if value == True:
                numberFeasible += 1
        print(
            f"Number of feasible temporary solutions: {numberFeasible} out of {len(self.datalog['Feasibility'])} iterations.")
        feasibility_percentage = (numberFeasible / len(self.datalog["Feasibility"])) * 100
        print(f"Feasibility percentage of temporary solutions: {feasibility_percentage:.2f}%")

