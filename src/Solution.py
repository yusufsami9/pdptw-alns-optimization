# -*- coding: utf-8 -*-

from Route import Route
import random


class Solution:
    """
    Method that represents a solution tot the PDPTW

    Attributes
    ----------
    problem : PDPTW
        the problem that corresponds to this solution
    routes : List of Routes
         Routes in the current solution
    served : List of Requests
        Requests served in the current solution
    notServed : List of Requests
         Requests not served in the current solution
    distance : int
        total distance of the current solution
    """

    def __init__(self, problem, routes, served, notServed):
        self.problem = problem
        self.routes = routes
        self.served = served
        self.notServed = notServed

    def computeDistance(self):
        """
        Method that computes the distance of the solution
        """
        self.distance = 0
        for route in self.routes:
            self.distance += route.distance

    def __str__(self):
        """
        Method that prints the solution
        """
        nRoutes = len(self.routes)
        nNotServed = len(self.notServed)
        toPrint = f"Solution with {nRoutes} routes and {nNotServed} unserved requests: "
        for route in self.routes:
            toPrint += route.__str__()

    def executeRandomRemoval(self, nRemove, random):
        """
        Method that executes a random removal of requests

        This is destroy method number 1 in the ALNS

        Parameters
        ----------
        nRemove : int
            number of requests that is removed.

        Parameters
        ----------
        randomGen : Random
            Used to generate random numbers

        """
        for i in range(nRemove):
            # terminate if no more requests are served
            if len(self.served) == 0:
                break
            # pick a random request and remove it from the solutoin
            req = random.choice(self.served)
            self.removeRequest(req)

    def removeRequest(self, request):
        """
        Method that removes a request from the solution
        """
        # iterate over routes to find in which route the request is served
        for route in self.routes:
            if request in route.requests:
                # remove the request from the route and break from loop
                route.removeRequest(request)
                break
        # update lists with served and unserved requests
        self.served.remove(request)
        self.notServed.append(request)

    def copy(self):
        """
        Method that creates a copy of the solution and returns it
        """
        # need a deep copy of routes because routes are modifiable
        routesCopy = list()
        for route in self.routes:
            routesCopy.append(route.copy())
        copy = Solution(self.problem, routesCopy, self.served.copy(), self.notServed.copy())
        copy.computeDistance()
        return copy

    def executeRandomInsertion(self, randomGen):
        """
        Method that randomly inserts the unserved requests in the solution

        This is repair method number 1 in the ALNS

        Parameters
        ----------
        randomGen : Random
            Used to generate random numbers

        """

        # iterate over the list with unserved requests
        while len(self.notServed) > 0:
            # pick a random request
            req = randomGen.choice(self.notServed)

            # keep track of routes in which req could be inserted
            potentialRoutes = self.routes.copy()
            inserted = False
            while len(potentialRoutes) > 0:
                # pick a random route
                randomRoute = randomGen.choice(potentialRoutes)

                afterInsertion = randomRoute.greedyInsert(req)
                if afterInsertion == None:
                    # insertion not feasible, remove route from potential routes
                    potentialRoutes.remove(randomRoute)
                else:
                    # insertion feasible, update routes and break from while loop
                    inserted = True
                    # print("Possible")
                    self.routes.remove(randomRoute)
                    self.routes.append(afterInsertion)
                    break

            # if we were not able to insert, create a new route
            if not inserted:
                # create a new route with the request
                locList = [self.problem.depot, req.pickUpLoc, req.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, [req], self.problem)
                self.routes.append(newRoute)
            # update the lists with served and notServed requests
            self.served.append(req)
            self.notServed.remove(req)

    def executeWorstRemoval(self, nRemove):
        """
        Worst Removal:
        remove the nRemove requests that contribute the most to the distance.
        """
        if len(self.served) == 0:
            return

        # store (req, saving) pairs
        savings = []

        # compute cost saving for each served request
        for req in self.served:
            # make a copy of the solution
            tempSol = self.copy()
            tempSol.removeRequest(req)
            tempSol.computeDistance()

            # saving = distance improvement after removing req
            saving = self.distance - tempSol.distance
            savings.append((req, saving))

        # sort by saving, descending
        savings.sort(key=lambda x: x[1], reverse=True)

        # remove top nRemove requests
        for i in range(min(nRemove, len(savings))):
            req = savings[i][0]
            if req in self.served:
                self.removeRequest(req)

    def executeShawRemoval(self, nRemove):
        """
        Related (Shaw) Removal:
        remove nRemove requests that are most related to each other,
        based on pickup distance and time window similarity.
        """
        if len(self.served) == 0:
            return

        # weights for relatedness
        w1 = 1.0  # weight for spatial distance
        w2 = 0.5  # weight for time window difference

        # pick a random seed request from served

        seedReq = random.choice(self.served)

        # compute relatedness of all other requests to the seed
        relatedness = []
        for req in self.served:
            if req == seedReq:
                continue
            # distance between pickup locations
            dx = req.pickUpLoc.xLoc - seedReq.pickUpLoc.xLoc
            dy = req.pickUpLoc.yLoc - seedReq.pickUpLoc.yLoc
            dist = (dx ** 2 + dy ** 2) ** 0.5

            # time window difference between pickups
            timeDiff = abs(req.pickUpLoc.startTW - seedReq.pickUpLoc.startTW)

            # relatedness score (lower = more related)
            score = w1 * dist + w2 * timeDiff
            relatedness.append((req, score))

        # sort by relatedness score (smallest first = most related)
        relatedness.sort(key=lambda x: x[1])

        # remove the seed and the most related nRemove-1 requests
        self.removeRequest(seedReq)
        count = 1
        for (req, score) in relatedness:
            if count >= nRemove:
                break
            if req in self.served:
                self.removeRequest(req)
                count += 1

    def executeGreedyInsertion(self):
        """
        Greedy Insertion:
        Iteratively insert requests from notServed by always choosing
        the request+route combination that gives the smallest increase in distance.
        """
        while len(self.notServed) > 0:
            bestDelta = float("inf")
            bestReq = None
            bestRoute = None
            bestRouteAfter = None

            # loop over all unserved requests
            for req in self.notServed:
                # try to insert req in every existing route
                for route in self.routes:
                    afterInsertion = route.greedyInsert(req)
                    if afterInsertion is not None:
                        delta = afterInsertion.distance - route.distance
                        if delta < bestDelta:
                            bestDelta = delta
                            bestReq = req
                            bestRoute = route
                            bestRouteAfter = afterInsertion

                # also consider creating a new route
                locList = [self.problem.depot, req.pickUpLoc, req.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, [req], self.problem)
                if newRoute.feasible and newRoute.distance < bestDelta:
                    bestDelta = newRoute.distance
                    bestReq = req
                    bestRoute = None
                    bestRouteAfter = newRoute

            # apply the best insertion found
            if bestReq is None:
                # nothing feasible found → just break
                break
            if bestRoute is None:
                # create new route
                self.routes.append(bestRouteAfter)
            else:
                # replace the old route with updated one
                self.routes.remove(bestRoute)
                self.routes.append(bestRouteAfter)

            # update served/notServed lists
            self.served.append(bestReq)
            self.notServed.remove(bestReq)

    def executeRegretKInsertion(self, k=2):
        """
        Regret-k Insertion:
        Iteratively insert requests from notServed based on regret values.
        Regret value of a request = (k-th best insertion cost) - (best insertion cost).
        The request with the largest regret is inserted first, at its best position.
        """
        while len(self.notServed) > 0:
            bestReq = None
            bestRoute = None
            bestRouteAfter = None
            bestDelta = float("inf")
            bestRegret = -1

            # loop over all unserved requests
            for req in self.notServed:
                insertionCosts = []  # store possible insertion costs for this req
                insertionRoutes = []  # store corresponding new routes

                # try inserting into all existing routes
                for route in self.routes:
                    afterInsertion = route.greedyInsert(req)
                    if afterInsertion is not None:
                        delta = afterInsertion.distance - route.distance
                        insertionCosts.append(delta)
                        insertionRoutes.append((route, afterInsertion))

                # also try new route
                locList = [self.problem.depot, req.pickUpLoc, req.deliveryLoc, self.problem.depot]
                newRoute = Route(locList, [req], self.problem)
                if newRoute.feasible:
                    insertionCosts.append(newRoute.distance)
                    insertionRoutes.append((None, newRoute))

                if len(insertionCosts) == 0:
                    continue  # no feasible place for this request

                # sort insertion costs
                sortedPairs = sorted(zip(insertionCosts, insertionRoutes), key=lambda x: x[0])
                sortedCosts = [p[0] for p in sortedPairs]

                # regret value = (k-th best) - (best), if fewer than k insertions, use last one
                if len(sortedCosts) >= k:
                    regret = sortedCosts[k - 1] - sortedCosts[0]
                else:
                    regret = sortedCosts[-1] - sortedCosts[0]

                # choose request with largest regret (tie-break: smallest best cost)
                if regret > bestRegret or (regret == bestRegret and sortedCosts[0] < bestDelta):
                    bestRegret = regret
                    bestReq = req
                    bestDelta = sortedCosts[0]
                    bestRoute, bestRouteAfter = sortedPairs[0][1]

            # apply best insertion
            if bestReq is None:
                break
            if bestRoute is None:
                self.routes.append(bestRouteAfter)
            else:
                self.routes.remove(bestRoute)
                self.routes.append(bestRouteAfter)

            # update served/notServed lists
            self.served.append(bestReq)
            self.notServed.remove(bestReq)

    def executeTimeOrientedRemoval(self, nRemove):
        """
        Time oriented removal:
        remove nRemove requests with the tightest time windows
        (smallest [DueDate-ReadyTime]
        """
        if len(self.served) == 0:
            return
        # compute window with for each served request
        widths = []
        for req in self.served:
            width = req.pickUpLoc.endTW - req.pickUpLoc.startTW
            widths.append((req, width))
        # sort by width ascending (tightest first)
        widths.sort(key=lambda x: x[1])

        # remove the top nRemove requests
        for i in range(min(nRemove, len(widths))):
            req = widths[i][0]
            if req in self.served:
                self.removeRequest(req)
