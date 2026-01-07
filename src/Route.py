# -*- coding: utf-8 -*-

import sys


class Route:
    """
    Class used to represent a route

    Parameters
    ----------
    locations : list of locations
        the route sequence of locations.
    requests : list of requests
        the requests served by the route
    problem : PDPTW
        the problem instance, used to compute distances.
    feasible : boolean
        true if route respects time windows, capacity and precedence
    distance : int
        total distance driven, extremely large number if infeasible
    """

    def __init__(self, locations, requests, problem):
        self.locations = locations
        self.requests = requests
        self.problem = problem
        # check the feasibility and compute the distance
        self.feasible = self.isFeasible()
        if self.feasible:
            self.distance = self.computeDistance()
        else:
            self.distance = sys.maxsize  # extremely large number

    def computeDistance(self):
        """
        Method that computes and returns the distance of the route
        """
        totDist = 0
        for i in range(1, len(self.locations) - 1):
            prevNode = self.locations[i - 1]
            curNode = self.locations[i]
            dist = self.problem.distMatrix[prevNode.nodeID][curNode.nodeID]
            totDist += dist
        return totDist

    def __str__(self):
        """
        Method that prints the route
        """
        toPrint = "Route "
        for loc in self.locations:
            toPrint += loc.__str__()
        toPrint += f" dist={self.distance}"
        return toPrint

    def isFeasible(self):
        """
        Method that checks feasbility. Returns True if feasible, else False

        Add component for electric vehicles later
        """
        # route should start and end at the depot
        if self.locations[0] != self.problem.depot or self.locations[-1] != self.problem.depot:
            return False

        curTime = 0  # current time
        curLoad = 0  # current load in vehicle
        curNode = self.locations[0]  # current node
        pickedUp = set()  # set with all requests that we picked up, used to check precedence
        batteryLevel = self.problem.batteryCapacity  # battery consumed so far
        batteryRecharged = False  # flag to indicate if we recharged during the route

        # iterate over route and check feasibility of time windows, capacity and precedence
        for i in range(1, len(self.locations) - 1):
            prevNode = self.locations[i - 1]
            curNode = self.locations[i]
            dist = self.problem.distMatrix[prevNode.nodeID][curNode.nodeID]
            curTime = max(curNode.startTW, curTime + prevNode.servTime + dist)
            batteryLevel -= dist * self.problem.batteryConsumptionRate

            # check if time window is respected
            if curTime > curNode.endTW:
                return False

            # check if capacity not exceeded
            curLoad += curNode.demand
            if curLoad > self.problem.capacity:
                return False

            # check if we don't do a delivery before a pickup
            if curNode.typeLoc == 1:
                # it is a pickup
                pickedUp.add(curNode.requestID)
            else:
                # it is a delivery
                # check if we picked up the request
                if curNode.requestID not in pickedUp:
                    return False
                pickedUp.remove(curNode.requestID)

            # Check if battery capacity is not exceeded
            if batteryLevel < 0 and self.problem.isEV:
                # Check if we are at a recharge station
                if curNode.typeLoc == 2:
                    chargeTime = (self.problem.batteryCapacity - batteryLevel) * self.problem.chargingRate
                    curTime += chargeTime
                    batteryLevel = self.problem.batteryCapacity

                # Find nearest recharge station
                else:
                    nearestStation = None
                    minDistToStation = sys.maxsize
                    for station in self.problem.rechargeStations:
                        distToStation = self.problem.distMatrix[prevNode.nodeID][station.nodeID]
                        if distToStation < minDistToStation:
                            minDistToStation = distToStation
                            nearestStation = station

                    # Check if we can reach the nearest recharge station
                    if batteryLevel - (minDistToStation * self.problem.batteryConsumptionRate) < 0:
                        return False

                    # Move to the recharge station from previous node
                    curTime += minDistToStation
                    batteryLevel -= minDistToStation * self.problem.batteryConsumptionRate

                    # Recharge at the station
                    chargeTime = (self.problem.batteryCapacity - batteryLevel) * self.problem.chargingRate
                    curTime += chargeTime
                    batteryLevel = self.problem.batteryCapacity

                    # Insert the recharge station into the route
                    self.locations.insert(i, nearestStation)
                    batteryRecharged = True

                    # # Move back to the current node
                    # curTime += self.problem.distMatrix[prevNode.nodeID][station.nodeID]
                    # batteryLevel -= self.problem.distMatrix[prevNode.nodeID][station.nodeID] * self.problem.batteryConsumptionRate
        # finally, check if all pickups have been delivered
        if len(pickedUp) > 0:
            return False

        if batteryRecharged:
            print("Battery recharged during route")
        return True

    def removeRequest(self, request):
        """
        Method that removes a request from the route.
        """
        # remove the request, the pickup and the delivery
        self.requests.remove(request)
        self.locations.remove(request.pickUpLoc)
        self.locations.remove(request.deliveryLoc)
        # the distance changes, so update
        self.distance = self.computeDistance()

    def copy(self):
        """
        Method that returns a copy of the route
        """
        locationsCopy = self.locations.copy()
        requestsCopy = self.requests.copy()
        return Route(locationsCopy, requestsCopy, self.problem)

    def greedyInsert(self, request):
        """
        Method that inserts the pickup and delivery of a request at the positions
        that give the shortest total distance. Returns best route.

        Parameters
        ----------
        request : Request
            the request that should be inserted.

        Returns
        -------
        bestInsert : Route
            Route with the best insertion.

        """
        requestsCopy = self.requests.copy()
        requestsCopy.append(request)

        minDist = sys.maxsize  # initialize as extremely large number
        bestInsert = None
        # iterate over all possible insertion positions for pickup and delivery
        for i in range(1, len(self.locations)):
            for j in range(i + 1, len(self.locations) + 1):  # delivery after pickup
                locationsCopy = self.locations.copy()
                locationsCopy.insert(i, request.pickUpLoc)
                locationsCopy.insert(j, request.deliveryLoc)
                afterInsertion = Route(locationsCopy, requestsCopy, self.problem)
                # check if insertion is feasible
                if afterInsertion.feasible:
                    # check if cheapest
                    if afterInsertion.distance < minDist:
                        bestInsert = afterInsertion
                        minDist = afterInsertion.distance

        return bestInsert
