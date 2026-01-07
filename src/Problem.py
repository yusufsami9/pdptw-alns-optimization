# -*- coding: utf-8 -*-


import numpy as np
import math


class Request:
    """
    Class that represents a request

    Attributes
    ----------
    pickUpLoc : Location
        The pick-up location.
    deliveryLoc : Location
        The delivery location.
    ID : int
        id of request.

    """

    def __init__(self, pickUpLoc, deliveryLoc, ID):
        self.pickUpLoc = pickUpLoc
        self.deliveryLoc = deliveryLoc
        self.ID = ID


class Location:
    """
    Class that represents either (i) a location where a request should be picked up
    or delivered or (ii) the depot
    Attributes
    ----------
    requestID : int
        id of request.
    xLoc : int
        x-coordinate.
    yLoc : int
        y-coordinate.
    demand : int
        demand quantity, positive if pick-up, negative if delivery
    startTW : int
        start time of time window.
    endTW : int
        end time of time window.
    servTime : int
        service time.
    typeLoc : int
        1 if pick-up, -1 if delivery, 0 if depot, 2 if recharge station
    nodeID : int
        id of the node, used for the distance matrix
    """

    def __init__(self, requestID, xLoc, yLoc, demand, startTW, endTW, servTime, typeLoc, nodeID):
        self.requestID = requestID
        self.xLoc = xLoc
        self.yLoc = yLoc
        self.demand = demand
        self.startTW = startTW
        self.endTW = endTW
        self.servTime = servTime
        self.typeLoc = typeLoc
        self.nodeID = nodeID

    def __str__(self):
        """
        Method that prints the location
        """
        return f"({self.requestID},{self.typeLoc})"

    def getDistance(l1, l2):
        """
        Method that computes the euclidian distance between two locations
        """
        dx = l1.xLoc - l2.xLoc
        dy = l1.yLoc - l2.yLoc
        return math.sqrt(dx ** 2 + dy ** 2)


class PDPTW:
    """
    Class that represents a pick-up and delivery problem with time windows
    Attributes
    ----------
    name : string
        name of the instance.
    requests : List of Requests
        The set containing all requests.
    depot : Location
        the depot where all vehicles must start and end.
    vehicleCapacity: int
        capacity of the vehicles.
    rechargeStations : List of Locations
        The set containing all recharge stations.
    electricComponents : List of floats
        List containing the electric vehicle components in the following order:
            - battery capacity : float
            - battery consumption rate (per distance unit) : float
            - charging rate (per time unit) : float
            - average velocity (distance units per time unit) : float
    nLines : int
        number of lines in the input file
    locations : Set of Locations
        The set containing all locations
     distMatrix : 2D array
         matrix with all distances between cities
    capacity : int
        capacity of the vehicles

    """

    def __init__(self, name, requests, depot, vehicleCapacity, rechargeStations, electricComponents, nLines, isEV=True):
        self.name = name
        self.requests = requests
        self.depot = depot
        self.capacity = vehicleCapacity
        ##construct the set with all locations
        self.locations = set()
        self.locations.add(depot)
        for r in self.requests:
            self.locations.add(r.pickUpLoc)
            self.locations.add(r.deliveryLoc)

        self.rechargeStations = set()
        for s in rechargeStations:
            self.locations.add(s)

        self.batteryCapacity = electricComponents[0]
        self.batteryConsumptionRate = electricComponents[1]
        self.chargingRate = electricComponents[2]
        self.averageVelocity = electricComponents[3]
        self.nLines = nLines
        self.isEV = isEV

        # compute the distance matrix
        self.distMatrix = np.zeros((len(self.locations), len(self.locations)))  # init as nxn matrix
        for i in self.locations:
            for j in self.locations:
                distItoJ = Location.getDistance(i, j)
                self.distMatrix[i.nodeID, j.nodeID] = distItoJ

    def __str__(self):
        return f" PDPTW problem {self.name} with {len(self.requests)} requests and a vehicle capacity of {self.capacity}"

    def readInstance(fileName):
        """
        Method that reads an instance from a file and returns the instancesf

        Implement option to read electric vehicle data
        """
        f = open(fileName)
        lines = f.readlines()

        rechargeStations = list()
        requests = list()
        unmatchedPickups = dict()
        unmatchedDeliveries = dict()
        nodeCount = 0
        requestCount = 1

        for line in lines[1:-6]:
            asList = []

            n = 13  # columns start every 13 characters
            for index in range(0, len(line), n):
                asList.append(line[index: index + n].strip())

            lID = asList[0]
            x = int(asList[2][:-2])  # need to remove ".0" from the string
            y = int(asList[3][:-2])
            if lID.startswith("D"):
                # it is the depot
                depot = Location(0, x, y, 0, 0, 0, 0, 0, nodeCount)
                nodeCount += 1
            elif lID.startswith("C"):
                # it is a location
                lType = asList[1]
                demand = int(asList[4][:-2])
                startTW = int(asList[5][:-2])
                endTW = int(asList[6][:-2])
                servTime = int(asList[7][:-2])
                partnerID = asList[8]
                if lType == "cp":
                    # it is a pick-up
                    if partnerID in unmatchedDeliveries:
                        deliv = unmatchedDeliveries.pop(partnerID)
                        pickup = Location(deliv.requestID, x, y, demand, startTW, endTW, servTime, 1, nodeCount)
                        nodeCount += 1
                        req = Request(pickup, deliv, deliv.requestID)
                        requests.append(req)
                    else:
                        pickup = Location(requestCount, x, y, demand, startTW, endTW, servTime, 1, nodeCount)
                        nodeCount += 1
                        requestCount += 1
                        unmatchedPickups[lID] = pickup
                elif lType == "cd":
                    # it is a delivery
                    if partnerID in unmatchedPickups:
                        pickup = unmatchedPickups.pop(partnerID)
                        deliv = Location(pickup.requestID, x, y, demand, startTW, endTW, servTime, -1, nodeCount)
                        nodeCount += 1
                        req = Request(pickup, deliv, pickup.requestID)
                        requests.append(req)
                    else:
                        deliv = Location(requestCount, x, y, demand, startTW, endTW, servTime, -1, nodeCount)
                        nodeCount += 1
                        requestCount += 1
                        unmatchedDeliveries[lID] = deliv
            elif lID.startswith("S"):
                # It is a recharge station, WIP
                rechargeStation = Location(0, x, y, 0, 0, 0, 0, 2, nodeCount)
                rechargeStations.append(rechargeStation)
                nodeCount += 1
                pass
                # sanity check: all pickups and deliveries should be matched
        if len(unmatchedDeliveries) + len(unmatchedPickups) > 0:
            raise Exception("Not all matched")

        # read the vehicle capacity
        vehicleLines = lines[-5:]
        batteryCapacity = float(vehicleLines[0][-6:].strip())
        capacity = int(vehicleLines[1][-7:-3].strip())
        batteryConsumptionRate = float(vehicleLines[2][-5:].strip())
        chargingRate = float(vehicleLines[3][-5:].strip())
        averageVelocity = float(vehicleLines[4][-5:].strip())

        electricComponents = [batteryCapacity, batteryConsumptionRate, chargingRate, averageVelocity]

        nLines = len(lines)

        return PDPTW(fileName, requests, depot, capacity, rechargeStations, electricComponents, nLines, False)
