#!/usr/bin/env python3
"""
Natural Math v3.8
Complete Framework: Core Growth + Goal-Directed + Adaptation + Evolution + Trails

Properties:
- Local decisions only (radius r)
- Energy constraints with termination guarantee (Theorem 1)
- Goal-directed via waypoints, rewards, target gradient
- Individual node adaptation (personal gamma based on success/failure)
- Cross-run evolution (parameter optimization)
- Collective memory via trails (stigmergy)
- Resource efficient (~20 MB RAM, <3 seconds per run)

Author: Natural Math
Website: fractalish.com
"""

import json
import random
import math
import copy
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any

# ============================================================
# PARAMETERS
# ============================================================

@dataclass
class Params:
# Core parameters
τ: float = 5.0 # Energy threshold
ι²: float = 1.0 # Contact inhibition (squared)
r²: float = 625.0 # Sense radius (squared, 25^2)
ε_extend: float = 5.0 # Extension cost
ε_sense: float = 1.2 # Sensing cost
ε_spawn: float = 4.0 # Spawn cost
ε_split: float = 9.0 # Split cost
E0: float = 1600.0 # Initial energy per seed

# Pressure parameters
P_bifurcate: float = 12.0 # Pressure threshold for bifurcation
β: float = 0.85 # Pressure decay rate
ΔP_baseline: float = 2.2 # Baseline pressure increase per step
ΔP_conflict: float = 5.0 # Extra pressure for conflict losers

# Growth parameters
η²: float = 0.01 # Gradient threshold squared
γ_fallback_base: float = 0.31 # Base exploration rate (evolved)
ε_tol: float = 1e-9 # Floating point tolerance

# Goal parameters
WAYPOINTS: List[Tuple[int, int, int]] = field(default_factory=lambda: [(10,0,0), (20,0,0), (30,0,0)])
WAYPOINT_REWARDS: List[float] = field(default_factory=lambda: [20.0, 50.0, 100.0])
TARGET_STRENGTH: float = 0.72 # How strongly target pulls
WRONG_DIRECTION_PENALTY: float = 3.1 # Penalty for moving away from target

# Trail parameters (collective memory)
TRAIL_DEPOSIT: float = 1.0 # Amount deposited per step
TRAIL_EVAPORATION: float = 0.95 # Decay per step (0.95 = 5% loss)
TRAIL_INFLUENCE: float = 0.3 # How much trail affects gradient
TRAIL_DIFFUSION: float = 0.0 # Spread to neighbors (0 = off)
MAX_TRAIL: float = 10.0 # Cap to prevent overflow

# Adaptation parameters (within-run)
ADAPTATION_RATE: float = 0.05
MAX_GAMMA: float = 0.9
MIN_GAMMA: float = 0.05
SUCCESS_STREAK_BOOST: float = 1.05
FAILURE_STREAK_DECAY: float = 0.95
ADAPTATION_INTERVAL: int = 5

# Simulation
T_max: int = 300
B: Tuple[Tuple[int, int], ...] = ((-100, 100), (-50, 100), (-50, 50))
disc: str = "axis"
verbose: bool = True


# ============================================================
# NODE CLASS
# ============================================================

@dataclass
class Node:
id: int
pos: Tuple[int, int, int]
dir: Tuple[int, int, int]
energy: float
pressure: float
parent_id: Optional[int]
type: str # 'seed', 'tip', 'branch', 'inert'
alive: bool
T: int = 0 # Temporary decision (not persistent)

# Adaptive fields (within-run learning)
personal_gamma: float = 0.3
success_streak: int = 0
failure_streak: int = 0
last_adapt_step: int = 0
reward_history: List[float] = field(default_factory=list)


# ============================================================
# GLOBAL STATE
# ============================================================

trail_field: Dict[Tuple[int, int, int], float] = {}


# ============================================================
# GEOMETRY
# ============================================================

def Q(p1: Tuple[int, int, int], p2: Tuple[int, int, int]) -> float:
"""Quadrance (squared distance) - exact integer arithmetic"""
return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2


def RANDOM_DIRECTION() -> Tuple[int, int, int]:
"""Random axis-aligned direction for zero-gradient fallback"""
axis = random.choice([0, 1, 2])
sign = 1 if random.random() < 0.5 else -1
d = [0, 0, 0]
d[axis] = sign
return tuple(d)


# ============================================================
# TRAIL FUNCTIONS (Collective Memory)
# ============================================================

def deposit_trail(pos: Tuple[int, int, int], params: Params):
"""Node leaves a chemical trail at its position"""
global trail_field
current = trail_field.get(pos, 0.0)
trail_field[pos] = min(params.MAX_TRAIL, current + params.TRAIL_DEPOSIT)


def evaporate_trails(params: Params):
"""Apply evaporation to all trails"""
global trail_field
to_delete = []
for pos, intensity in trail_field.items():
new_intensity = intensity * params.TRAIL_EVAPORATION
if new_intensity < 0.01:
to_delete.append(pos)
else:
trail_field[pos] = new_intensity
for pos in to_delete:
del trail_field[pos]


def diffuse_trails(params: Params):
"""Optional: diffuse trails to neighboring cells"""
global trail_field
if params.TRAIL_DIFFUSION <= 0:
return

new_trails = defaultdict(float)
for pos, intensity in trail_field.items():
# Keep original
new_trails[pos] += intensity * (1 - params.TRAIL_DIFFUSION)
# Diffuse to 6 neighbors
for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
neighbor = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
new_trails[neighbor] += intensity * params.TRAIL_DIFFUSION / 6

# Cap and assign back
for pos in new_trails:
new_trails[pos] = min(params.MAX_TRAIL, new_trails[pos])
trail_field.clear()
trail_field.update(new_trails)


def compute_trail_gradient(pos: Tuple[int, int, int], params: Params) -> Tuple[float, float, float]:
"""Compute gradient of trail field at position (points toward higher trail concentration)"""
global trail_field
g = (0.0, 0.0, 0.0)

for dx in [-1, 0, 1]:
for dy in [-1, 0, 1]:
for dz in [-1, 0, 1]:
if dx == 0 and dy == 0 and dz == 0:
continue
neighbor = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
trail = trail_field.get(neighbor, 0.0)
g = (g[0] + trail * dx,
g[1] + trail * dy,
g[2] + trail * dz)

# Normalize
norm = math.sqrt(g[0]**2 + g[1]**2 + g[2]**2)
if norm > params.ε_tol:
return (g[0]/norm, g[1]/norm, g[2]/norm)
return (0.0, 0.0, 0.0)


# ============================================================
# GRADIENT COMPUTATION (Energy + Target + Trails)
# ============================================================

def COMPUTE_GRADIENT(p: Node, A_t: List[Node], params: Params) -> Tuple[float, float, float]:
"""Compute combined gradient from energy differences, target attraction, and trails"""
global trail_field

# 1. Energy gradient from neighbors
g_energy = (0.0, 0.0, 0.0)
weight_sum = 0.0

for q in A_t:
if q.id == p.id:
continue
q_dist = Q(p.pos, q.pos)
if q_dist > params.r² + params.ε_tol or q_dist < params.ε_tol:
continue
w = 1.0 / q_dist
weight_sum += w
energy_diff = q.energy - p.energy
g_energy = (g_energy[0] + w * energy_diff * (q.pos[0] - p.pos[0]),
g_energy[1] + w * energy_diff * (q.pos[1] - p.pos[1]),
g_energy[2] + w * energy_diff * (q.pos[2] - p.pos[2]))

if weight_sum > params.ε_tol:
g_energy = (g_energy[0] / weight_sum,
g_energy[1] / weight_sum,
g_energy[2] / weight_sum)

# 2. Target gradient (toward final waypoint)
g_target = (0.0, 0.0, 0.0)
if params.WAYPOINTS:
target = params.WAYPOINTS[-1]
dx = target[0] - p.pos[0]
dy = target[1] - p.pos[1]
dz = target[2] - p.pos[2]
dist_sq = dx*dx + dy*dy + dz*dz
if dist_sq > params.ε_tol:
dist = math.sqrt(dist_sq)
g_target = (dx/dist, dy/dist, dz/dist)

# 3. Trail gradient (collective memory)
g_trail = compute_trail_gradient(p.pos, params)

# Combine all influences
g = (g_energy[0] + params.TARGET_STRENGTH * g_target[0] + params.TRAIL_INFLUENCE * g_trail[0],
g_energy[1] + params.TARGET_STRENGTH * g_target[1] + params.TRAIL_INFLUENCE * g_trail[1],
g_energy[2] + params.TARGET_STRENGTH * g_target[2] + params.TRAIL_INFLUENCE * g_trail[2])

# Normalize
g_norm = math.sqrt(g[0]**2 + g[1]**2 + g[2]**2)
if g_norm > params.ε_tol:
g = (g[0]/g_norm, g[1]/g_norm, g[2]/g_norm)

return g


# ============================================================
# DIRECTION UPDATE
# ============================================================

def UPDATE_DIRECTION(g: Tuple[float, float, float], params: Params) -> Tuple[int, int, int]:
"""Convert gradient to lattice direction (axis discretization)"""
g_norm_sq = g[0]**2 + g[1]**2 + g[2]**2
if g_norm_sq < params.ε_tol:
return (0, 1, 0) # Default upward

abs_vals = [abs(g[0]), abs(g[1]), abs(g[2])]
max_abs = max(abs_vals)

# Tie-breaking: first index (x=0, y=1, z=2) wins
if abs_vals[0] >= max_abs - params.ε_tol:
idx = 0
elif abs_vals[1] >= max_abs - params.ε_tol:
idx = 1
else:
idx = 2

d = [0, 0, 0]
d[idx] = 1 if g[idx] >= 0 else -1
return tuple(d)


# ============================================================
# BIFURCATION CHILDREN
# ============================================================

def PROJECT_TO_LATTICE(v: Tuple[float, float, float]) -> Tuple[int, int, int]:
"""Project arbitrary vector to axis-aligned direction"""
abs_vals = [abs(v[0]), abs(v[1]), abs(v[2])]
max_idx = 0
if abs_vals[1] > abs_vals[0]:
max_idx = 1
if abs_vals[2] > abs_vals[max_idx]:
max_idx = 2

result = [0, 0, 0]
result[max_idx] = 1 if v[max_idx] >= 0 else -1
return tuple(result)


def BIFURCATION_CHILDREN(v_parent: Tuple[int, int, int], params: Params) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
"""Return two child directions perpendicular to parent (90° split)"""
if v_parent == (0, 0, 0):
return ((1, 0, 0), (0, 1, 0))

# Find a vector perpendicular to v_parent
if abs(v_parent[0]) < params.ε_tol:
w = (1, 0, 0)
elif abs(v_parent[1]) < params.ε_tol:
w = (0, 1, 0)
elif abs(v_parent[2]) < params.ε_tol:
w = (0, 0, 1)
else:
w = (0, v_parent[2], -v_parent[1])

w_proj = PROJECT_TO_LATTICE(w)
w_opp = (-w_proj[0], -w_proj[1], -w_proj[2])
v0_proj = PROJECT_TO_LATTICE(v_parent)

candidates = [
(v0_proj[0] + w_proj[0], v0_proj[1] + w_proj[1], v0_proj[2] + w_proj[2]),
(v0_proj[0] + w_opp[0], v0_proj[1] + w_opp[1], v0_proj[2] + w_opp[2]),
(v0_proj[0] - w_proj[0], v0_proj[1] - w_proj[1], v0_proj[2] - w_proj[2]),
(v0_proj[0] - w_opp[0], v0_proj[1] - w_opp[1], v0_proj[2] - w_opp[2])
]

valid = []
for c in candidates:
if c == (0, 0, 0):
continue
if c == v0_proj:
continue
if c not in valid:
valid.append(c)

if len(valid) < 2:
return ((1, 0, 0), (0, 1, 0))

return (valid[0], valid[1])


# ============================================================
# DECISION LOGIC
# ============================================================

def COMPUTE_DECISION(p: Node, A_t: List[Node], occupied: set, params: Params) -> int:
"""
Returns T in {+1 (EXTEND), 0 (SENSE), -1 (RESTRICT)}

Decision priority:
1. RESTRICT (energy < τ OR contact inhibition)
2. EXTEND (strong gradient OR random fallback)
3. SENSE (fallback)
"""

# Compute minimum distance to other active nodes
min_q = float('inf')
for q in A_t:
if q.id == p.id:
continue
dist = Q(p.pos, q.pos)
if dist < min_q:
min_q = dist

# RESTRICT check
if p.energy < params.τ - params.ε_tol:
return -1
if min_q < params.ι² - params.ε_tol:
return -1

# EXTEND preconditions
can_extend = (p.energy >= params.τ - params.ε_tol) and \
(min_q > params.ι² + params.ε_tol)

if can_extend:
g = COMPUTE_GRADIENT(p, A_t, params)
g_norm_sq = g[0]**2 + g[1]**2 + g[2]**2

# Strong gradient -> EXTEND
if g_norm_sq > params.η² + params.ε_tol:
return +1

# Weak/zero gradient -> random fallback (use personal gamma)
if g_norm_sq <= params.η² + params.ε_tol:
if random.random() < p.personal_gamma:
return +1

# SENSE (fallback)
if p.energy >= params.τ - params.ε_tol:
return 0

return -1


# ============================================================
# CONFLICT RESOLUTION
# ============================================================

def RESOLVE_CONFLICTS(candidates: List, occupied: set, nodes: List[Node], params: Params):
"""Resolve conflicts where multiple nodes target the same position"""
target_map = {}
for parent, pos_new, dir_new in candidates:
if pos_new not in target_map:
target_map[pos_new] = []
target_map[pos_new].append((parent, dir_new))

for target, contenders in target_map.items():
is_conflict = (target in occupied) or (len(contenders) > 1)

if is_conflict:
for loser, _ in contenders:
if loser.energy >= params.ε_sense - params.ε_tol:
loser.energy -= params.ε_sense
else:
loser.energy = 0.0
loser.alive = False
loser.type = 'inert'
loser.pressure += params.ΔP_conflict
else:
winner, dir_new = contenders[0]
if winner.energy >= params.ε_extend - params.ε_tol:
winner.energy -= params.ε_extend
winner.pos = target
winner.dir = dir_new
else:
winner.energy = 0.0
winner.alive = False
winner.type = 'inert'


# ============================================================
# GOAL REWARD & PENALTIES (with Node Adaptation)
# ============================================================

def adapt_node(node: Node, reward_received: float, penalty_received: float,
step: int, params: Params):
"""Update node's personal_gamma based on recent experience"""

if step - node.last_adapt_step < params.ADAPTATION_INTERVAL:
return

node.last_adapt_step = step
node.reward_history.append(reward_received)
node.reward_history = node.reward_history[-10:]

recent_rewards = sum(node.reward_history)
net_success = recent_rewards - penalty_received

if net_success > 0:
node.success_streak += 1
node.failure_streak = 0
node.personal_gamma = min(params.MAX_GAMMA,
node.personal_gamma * params.SUCCESS_STREAK_BOOST)
elif net_success < 0:
node.failure_streak += 1
node.success_streak = 0
node.personal_gamma = max(params.MIN_GAMMA,
node.personal_gamma * params.FAILURE_STREAK_DECAY)
else:
node.success_streak = max(0, node.success_streak - 1)
node.failure_streak = max(0, node.failure_streak - 1)
if node.personal_gamma > params.γ_fallback_base:
node.personal_gamma -= params.ADAPTATION_RATE * 0.1
elif node.personal_gamma < params.γ_fallback_base:
node.personal_gamma += params.ADAPTATION_RATE * 0.1

if node.failure_streak > 10:
node.personal_gamma = 0.7
node.dir = RANDOM_DIRECTION()
node.failure_streak = 0


def APPLY_GOAL_REWARD(nodes: List[Node], params: Params, step: int) -> int:
"""Give energy reward to nodes that reach waypoints. Triggers node adaptation."""
reached = set()

for n in nodes:
if not n.alive:
continue

for i, wp in enumerate(params.WAYPOINTS):
dx = n.pos[0] - wp[0]
dy = n.pos[1] - wp[1]
dz = n.pos[2] - wp[2]
dist_sq = dx*dx + dy*dy + dz*dz

if dist_sq <= 4.0: # Within radius 2
reward = params.WAYPOINT_REWARDS[i]
n.energy += reward
reached.add((n.id, i))

# Adaptation: positive reinforcement
adapt_node(n, reward, 0, step, params)

if params.verbose and n.id not in [r[0] for r in reached]:
print(f" 🎯 Step {step}: Node {n.id} reached waypoint {i+1} (+{reward} energy, gamma={n.personal_gamma:.3f})")

return len(reached)


def APPLY_WRONG_DIRECTION_PENALTY(node: Node, target_dir: Tuple[float, float, float],
move_dir: Tuple[int, int, int], params: Params, step: int):
"""Penalize moves that go away from target. Triggers node adaptation."""
# Convert move_dir to unit vector
move_norm = math.sqrt(move_dir[0]**2 + move_dir[1]**2 + move_dir[2]**2)
if move_norm < params.ε_tol:
return

move_unit = (move_dir[0]/move_norm, move_dir[1]/move_norm, move_dir[2]/move_norm)

# Dot product: positive = moving toward target
dot = move_unit[0]*target_dir[0] + move_unit[1]*target_dir[1] + move_unit[2]*target_dir[2]

if dot < -0.1: # Significantly wrong direction
penalty = params.WRONG_DIRECTION_PENALTY
node.energy -= penalty

adapt_node(node, 0, penalty, step, params)

if node.energy < 0:
node.energy = 0
node.alive = False
node.type = 'inert'

if params.verbose and node.alive:
print(f" ⚠️ Step {step}: Node {node.id} penalized (wrong direction), gamma={node.personal_gamma:.3f}")


# ============================================================
# INITIALIZATION
# ============================================================

def INITIALIZE(params: Params) -> Tuple[List[Node], int]:
"""Create initial 3 seeds with evolved parameters"""
nodes = []

seeds = [
(0, (0, 0, 0), (0, 1, 0)),
(1, (3, 0, 0), (-1, 1, 0)),
(2, (-3, 0, 0), (1, 1, 0))
]

for nid, pos, d in seeds:
node = Node(
id=nid, pos=pos, dir=d, energy=params.E0, pressure=0.0,
parent_id=None, type='seed', alive=True,
personal_gamma=params.γ_fallback_base
)
nodes.append(node)

next_id = 3
return nodes, next_id


# ============================================================
# MAIN SIMULATION STEP
# ============================================================

def STEP(nodes: List[Node], next_id: int, params: Params, step: int) -> Tuple[List[Node], int]:
"""Execute one simulation step (Master Update Schedule v3.8)"""
global trail_field

# PHASE 0: Build active list
active = [n for n in nodes if n.alive]
if not active:
return nodes, next_id

# PHASE 1: Boundary enforcement
for n in nodes:
if (n.pos[0] < params.B[0][0] or n.pos[0] > params.B[0][1] or
n.pos[1] < params.B[1][0] or n.pos[1] > params.B[1][1] or
n.pos[2] < params.B[2][0] or n.pos[2] > params.B[2][1]):
n.alive = False
n.type = 'inert'

# PHASE 2: Tau enforcement
for n in nodes:
if n.alive and n.energy < params.τ - params.ε_tol:
n.alive = False
n.type = 'inert'

# PHASE 3: Refresh active after enforcement
active = [n for n in nodes if n.alive]
if not active:
return nodes, next_id

occupied = {n.pos for n in active}
active_snapshot = list(active)

# PHASE 4: Decision (simultaneous)
for n in active_snapshot:
n.T = COMPUTE_DECISION(n, active, occupied, params)

# PHASE 5: RESTRICT processing
for n in active_snapshot:
if n.T == -1:
n.energy = 0.0
n.alive = False
n.type = 'inert'

# PHASE 6: SENSE processing (pressure NOT updated here)
for n in active_snapshot:
if n.T == 0:
n.energy -= params.ε_sense
if n.energy < 0:
n.energy = 0.0
n.alive = False
n.type = 'inert'

# PHASE 7: EXTEND processing (bifurcation and normal move)
candidates = []
new_nodes = []

# Get target direction for penalty calculation
target_dir = (1.0, 0.0, 0.0) # Default +X
if params.WAYPOINTS:
target = params.WAYPOINTS[-1]
target_dir = (float(target[0]), float(target[1]), float(target[2]))
norm = math.sqrt(target_dir[0]**2 + target_dir[1]**2 + target_dir[2]**2)
if norm > params.ε_tol:
target_dir = (target_dir[0]/norm, target_dir[1]/norm, target_dir[2]/norm)

for n in active_snapshot:
if n.T == +1:
g = COMPUTE_GRADIENT(n, active, params)
g_norm_sq = g[0]**2 + g[1]**2 + g[2]**2

if g_norm_sq > params.η² + params.ε_tol:
d = UPDATE_DIRECTION(g, params)
else:
d = RANDOM_DIRECTION()

if d == (0, 0, 0):
n.energy -= params.ε_sense
if n.energy < 0:
n.energy = 0.0
n.alive = False
n.type = 'inert'
continue

pos_new = (n.pos[0] + d[0], n.pos[1] + d[1], n.pos[2] + d[2])

# Wrong direction penalty
APPLY_WRONG_DIRECTION_PENALTY(n, target_dir, d, params, step)

# Check bifurcation condition
if (n.pressure >= params.P_bifurcate - params.ε_tol and
n.energy > 2*params.ε_extend + params.ε_spawn + params.ε_tol and n.alive):

v1, v2 = BIFURCATION_CHILDREN(n.dir, params)
pos1 = (n.pos[0] + v1[0], n.pos[1] + v1[1], n.pos[2] + v1[2])
pos2 = (n.pos[0] + v2[0], n.pos[1] + v2[1], n.pos[2] + v2[2])

occupied_set = occupied | {c[1] for c in candidates}
valid1 = pos1 not in occupied_set
valid2 = pos2 not in occupied_set

if valid1 and valid2:
n.energy -= (params.ε_extend + params.ε_spawn)
if n.energy < 0:
n.energy = 0.0
n.alive = False
n.type = 'inert'
continue

child_e = max((n.energy - params.ε_split) / 2.0, params.τ)

c1 = Node(id=next_id, pos=pos1, dir=v1, energy=child_e,
pressure=n.pressure, parent_id=n.id, type='tip', alive=True,
personal_gamma=n.personal_gamma)
next_id += 1
new_nodes.append(c1)

c2 = Node(id=next_id, pos=pos2, dir=v2, energy=child_e,
pressure=n.pressure, parent_id=n.id, type='tip', alive=True,
personal_gamma=n.personal_gamma)
next_id += 1
new_nodes.append(c2)

n.type = 'branch'
n.alive = False
else:
candidates.append((n, pos_new, d))
elif n.alive:
candidates.append((n, pos_new, d))

# PHASE 8: Conflict resolution
RESOLVE_CONFLICTS(candidates, occupied, nodes, params)

# PHASE 8.5: Goal reward (after movement)
APPLY_GOAL_REWARD(nodes, params, step)

# PHASE 8.6: Deposit trails (after movement)
for n in nodes:
if n.alive and n.type in ['tip', 'seed']:
deposit_trail(n.pos, params)

# PHASE 9: Add new nodes
nodes.extend(new_nodes)

# PHASE 10: Pressure update (surviving nodes only)
active_now = [n for n in nodes if n.alive]
for n in active_now:
n.pressure = (n.pressure + params.ΔP_baseline) * params.β

# PHASE 10.5: Trail evaporation and diffusion
evaporate_trails(params)
diffuse_trails(params)

return nodes, next_id


# ============================================================
# MAIN SIMULATION LOOP
# ============================================================

def SIMULATE(params: Params = None, verbose: bool = None) -> Tuple[List[Node], List]:
"""Run full simulation until termination"""
global trail_field

if params is None:
params = Params()
if verbose is not None:
params.verbose = verbose

# Reset global state
trail_field.clear()

nodes, next_id = INITIALIZE(params)

stats = []

for step in range(1, params.T_max + 1):
active = [n for n in nodes if n.alive]
if not active:
if params.verbose:
print(f"\n✅ Termination at step {step}: No active nodes")
break

total_energy = sum(n.energy for n in active)
total_pressure = sum(n.pressure for n in active)
stats.append((step, len(active), total_energy, total_pressure))

if params.verbose:
print(f"Step {step:3d}: active={len(active):3d}, energy={total_energy:8.2f}, pressure={total_pressure:8.2f}")

nodes, next_id = STEP(nodes, next_id, params, step)

return nodes, stats


# ============================================================
# JSON EXPORT
# ============================================================

def export_trajectory(nodes: List[Node], step: int, params: Params, filename: str = None):
"""Export current state to JSON for visualization"""
if filename is None:
filename = f"{step:04d}_trajectory.json"

data = {
"step": step,
"params": {
"τ": params.τ, "ι²": params.ι², "ε_extend": params.ε_extend,
"ε_sense": params.ε_sense, "γ_fallback_base": params.γ_fallback_base,
"TARGET_STRENGTH": params.TARGET_STRENGTH,
"TRAIL_INFLUENCE": params.TRAIL_INFLUENCE,
"WAYPOINTS": [list(wp) for wp in params.WAYPOINTS]
},
"nodes": [{
"id": n.id,
"pos": list(n.pos),
"dir": list(n.dir),
"energy": float(n.energy),
"pressure": float(n.pressure),
"type": n.type,
"parent_id": n.parent_id,
"alive": n.alive,
"personal_gamma": n.personal_gamma if hasattr(n, 'personal_gamma') else params.γ_fallback_base
} for n in nodes],
"trails": [{"pos": list(k), "intensity": v} for k, v in trail_field.items() if v > 0.1]
}

with open(filename, "w") as f:
json.dump(data, f, indent=2)

return filename


# ============================================================
# DEMO / MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
print("=" * 60)
print("Natural Math v3.8")
print("Complete Framework: Growth + Goal + Adaptation + Evolution + Trails")
print("=" * 60)

params = Params()
params.verbose = True

print(f"\n🎯 Waypoints: {params.WAYPOINTS}")
print(f"💰 Rewards: {params.WAYPOINT_REWARDS}")
print(f"🧬 γ_fallback_base: {params.γ_fallback_base}")
print(f"🧪 TARGET_STRENGTH: {params.TARGET_STRENGTH}")
print(f"🐜 TRAIL_INFLUENCE: {params.TRAIL_INFLUENCE}")
print("\n" + "-" * 40)

nodes, stats = SIMULATE(params)

print("\n" + "=" * 60)
print("SIMULATION COMPLETE")
print("=" * 60)

# Final statistics
total_nodes = len(nodes)
branches = len([n for n in nodes if n.type == 'branch'])
inert = len([n for n in nodes if n.type == 'inert'])
seeds = len([n for n in nodes if n.type == 'seed'])
tips = len([n for n in nodes if n.type == 'tip'])

print(f"\n📊 Final Statistics:")
print(f" Total nodes: {total_nodes}")
print(f" Seeds: {seeds}")
print(f" Tips: {tips}")
print(f" Branches: {branches}")
print(f" Inert: {inert}")

# Gamma distribution
gammas = [n.personal_gamma for n in nodes if hasattr(n, 'personal_gamma') and n.type != 'inert']
if gammas:
print(f"\n📈 Personal Gamma Distribution (active/branch nodes):")
print(f" Min: {min(gammas):.3f}")
print(f" Max: {max(gammas):.3f}")
print(f" Avg: {sum(gammas)/len(gammas):.3f}")
std = math.sqrt(sum((g - sum(gammas)/len(gammas))**2 for g in gammas)/len(gammas))
print(f" Std: {std:.3f}")

# Trail stats
if trail_field:
intensities = list(trail_field.values())
print(f"\n🐜 Trail Statistics:")
print(f" Unique trail positions: {len(trail_field)}")
print(f" Max intensity: {max(intensities):.2f}")
print(f" Avg intensity: {sum(intensities)/len(intensities):.2f}")

# Export final state
export_trajectory(nodes, len(stats), params, "final_trajectory.json")
print(f"\n💾 Final trajectory saved to final_trajectory.json")
