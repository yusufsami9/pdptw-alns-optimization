# PDPTW (Pickup & Delivery Problem with Time Windows) – ALNS (Adaptive Large Neighborhood Search)

Python implementation of an **Adaptive Large Neighborhood Search (ALNS)** framework for the  
**Pickup and Delivery Problem with Time Windows (PDPTW)**.

This repo is based on an original course template (Rolf van Lieshout) and extended with:
- multiple destroy/repair operators,
- simulated annealing acceptance,
- adaptive operator weighting (decay + score-based updates),
- and basic visualizations for analysis.

---

## Problem Overview (PDPTW)

In PDPTW, each request consists of:
- a **pickup node** and a **delivery node**
- **precedence constraint**: pickup must happen before delivery
- **time windows** for service at nodes
- **vehicle capacity** constraints
- routes must start/end at a **depot**

Objective: **minimize total travel distance** while keeping routes feasible.

---

## Method: ALNS

ALNS iteratively improves a current solution by:
1. **Destroy**: remove a subset of requests (neighborhood size is randomized)
2. **Repair**: reinsert removed requests using a heuristic
3. **Accept/Reject** using **Simulated Annealing**
4. **Update operator weights** based on how good the move was

### Initial Solution
- Built using **random insertion** until all requests are served
- New routes are created if insertion into existing routes is infeasible

---

## Destroy Operators (4)

The code supports the following destroy operators:

1. **Random Removal**
   - Removes random served requests.

2. **Worst Removal**
   - Removes requests with the highest “distance saving” when removed (largest contribution).

3. **Shaw (Related) Removal**
   - Removes “related” requests based on spatial closeness and time-window similarity.

4. **Time-Oriented Removal**
   - Removes requests with the tightest pickup time windows (smallest width).

---

## Repair Operators (3)

1. **Random Insertion**
   - Tries to insert each unserved request randomly into feasible routes (or creates a new route).

2. **Greedy Insertion**
   - Chooses the request + insertion producing the **smallest increase in distance**.

3. **Regret-k Insertion (default k=2)**
   - Inserts the request with the largest regret value first  
     (difference between best and k-th best insertion).

---

## Acceptance: Simulated Annealing

Move acceptance uses simulated annealing:

- Always accept if a **new global best** is found
- Accept if **improves current solution**
- Otherwise accept a worse solution with probability:

\[
P = \exp\left(-\frac{\Delta}{T}\right)
\]

Temperature decreases each iteration:

- `temperature *= cooling_rate`

---

## Adaptive Operator Weights

Destroy/repair operators are chosen via **weighted random selection**.

After each iteration:
- a **score criterion** is assigned:
  1. New global best
  2. Improved current solution
  3. Accepted worse solution
  4. Rejected worse solution

Weights are updated using decay:

\[
w \leftarrow decay \cdot w + (1 - decay) \cdot score
\]

Then weights are normalized to sum to 1.

---

## Visualizations / Logging

The solver tracks a `datalog` with:
- iteration number
- current & best distance
- temperature
- chosen operators + weights
- neighborhood size
- feasibility flag

At the end, it plots:
- destroy operator weights over time
- repair operator weights over time
- current vs best distance over time

It also prints feasibility statistics (percentage of feasible temporary solutions).

---

## Repository Structure

```text
pdptw-alns-optimization/
├─ Instances/
│  ├─ .gitkeep
│  ├─ c202C16.txt
│  ├─ lc102.txt
│  ├─ lc108.txt
│  ├─ lc207.txt
│  ├─ lr112.txt
│  ├─ lr205.txt
│  ├─ lrc104.txt
│  ├─ lrc206.txt
│  ├─ r102C18.txt
│  ├─ rc204C16.txt
│  └─ readme.txt
├─ outputs/
│  ├─ .gitkeep
│  ├─ destroy_operator_weights_over_time.png
│  ├─ repair_operator_weights_over_time.png
│  └─ route_distance_over_time.png
├─ src/
│  ├─ ALNS.py
│  ├─ Main.py
│  ├─ Problem.py
│  ├─ Route.py
│  └─ Solution.py
├─ .gitignore
├─ LICENSE
├─ PDPTW_Report.pdf
└─ README.md
```


---

## How to Run

### Requirements
- Python 3.x
- numpy, matplotlib

Install dependencies:
```bash
pip install numpy matplotlib
```
Run:
```
python Main.py
```

## Selecting an instance

In Main.py, pick an instance using:
test = instances[6]


