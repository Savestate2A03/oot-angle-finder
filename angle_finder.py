import collections
import heapq

import movements

COST_FUDGE = 3.0
COST_TABLE = {}
FILTERED_MOVEMENTS = []

MOVEMENT_OPTIONS = {
    "basic": [
        "ess up",
        "ess left",
        "ess right",
    ],
    "target enabled": [
        "turn left",
        "turn right",
        "turn 180",
    ],
    "no carry": [
        "sidehop sideroll left",
        "sidehop sideroll right",
        "ess down sideroll",
        "backflip sideroll",
    ],
    "sword": [
        "sword spin shield cancel",
    ],
    "biggoron": [
        "biggoron slash shield cancel",
        "biggoron spin shield cancel",
    ],
    "hammer": [
        "hammer shield cancel",
    ],
    "shield corners": [
        "shield top-right",
        "shield top-left",
        "shield bottom-left",
        "shield bottom-right",
    ],
}
BASIC_COSTS = {
    "ess up": 0.5,
    "ess left": 0.75,
    "ess right": 0.75,
    "turn left": 1.0,
    "turn right": 1.0,
    "turn 180": 1.0,
    "sidehop sideroll left": 1.5,
    "sidehop sideroll right": 1.5,
    "ess down sideroll": 1.5,
    "backflip sideroll": 1.5,
    "sword spin shield cancel": 2.0,
    "biggoron slash shield cancel": 2.0,
    "biggoron spin shield cancel": 2.0,
    "hammer shield cancel": 2.0,
    "shield top-right": 2.0,
    "shield top-left": 2.0,
    "shield bottom-left": 2.0,
    "shield bottom-right": 2.0,
}
COST_OVERRIDES = {
    ("ess left", "ess left"): 0.25,
    ("ess right", "ess right"): 0.25,
}


Node = collections.namedtuple("Node", ["edges_in", "best"])
Edge = collections.namedtuple("Edge", ["from_angle", "movement", "cost"])

empty_node = lambda: Node(edges_in={}, best=None)


def maybe_add_edge(graph, edge, to_angle):
    def min_none(x, y):
        return min(x, y) if x is not None else y

    to_node = graph[to_angle]
    edges_in = to_node.edges_in

    def add_edge():
        edges_in[edge.movement] = edge
        best = min_none(to_node.best, edge.cost)
        graph[to_angle] = Node(edges_in, best)

    if to_node.best == None:
        add_edge()
        return True

    if edge.cost > to_node.best + COST_FUDGE:
        return False

    if (edge.movement not in edges_in) or (edge.cost < edges_in[edge.movement].cost):
        add_edge()
        return True

    # have already found this node, via this movement, at least as quickly
    return False


def edges_out(graph, angle, last_movement, last_cost):
    for (movement, cost_increase) in COST_TABLE[last_movement].items():
        if movement not in FILTERED_MOVEMENTS:
            continue

        new_angle = movements.table[movement](angle)

        if new_angle is None:
            continue

        to_angle = new_angle & 0xFFFF
        from_angle = angle
        cost = last_cost + cost_increase

        yield (to_angle, Edge(from_angle, movement, cost))


def explore(starting_angles):
    graph = [empty_node() for _ in range(0xFFFF + 1)]
    queue = []

    for angle in starting_angles:
        edges_in = {None: Edge(from_angle=None, movement=None, cost=0)}
        best = 0

        graph[angle] = Node(edges_in, best)
        heapq.heappush(queue, (0.0, angle, None))

    should_print = 0
    while len(queue) > 0:
        if should_print == 0:
            print(f"Exploring ({len(queue)})...", end="\r")
            should_print = 100
        should_print -= 1

        (cost, angle, movement) = heapq.heappop(queue)

        for to_angle, edge in edges_out(graph, angle, movement, cost):
            if maybe_add_edge(graph, edge, to_angle):
                heapq.heappush(queue, (edge.cost, to_angle, edge.movement))
                # print(f"added {edge} to {to_angle}")

    print("\nDone.")
    return graph


def navigate_best(graph, to):
    path = []

    while to is not None:
        edges = graph[to].edges_in
        best_edge = min(edges.values(), key=lambda edge: edge.cost)

        path.append((best_edge.movement, to))
        to = best_edge.from_angle

    path.reverse()
    return path


def print_path(path):
    for motion, angle in path:
        if motion == None:
            print(f"start at {hex(angle)}")
        else:
            print(f"{motion} to {hex(angle)}")
    print("") # newline


def set_movements(movements):
    global FILTERED_MOVEMENTS
    FILTERED_MOVEMENTS = []
    for movement in movements:
        FILTERED_MOVEMENTS.extend(MOVEMENT_OPTIONS[movement])

set_movements(["basic", "no carry", "target enabled", "hammer"])

COST_TABLE[None] = BASIC_COSTS.copy()
for movement, cost in BASIC_COSTS.items():
    if movement in FILTERED_MOVEMENTS:
        COST_TABLE[movement] = BASIC_COSTS.copy()
for (first, then), cost in COST_OVERRIDES.items():
    if first in FILTERED_MOVEMENTS:
        COST_TABLE[first][then] = cost

print(FILTERED_MOVEMENTS)

graph = explore([0x0000, 0x4000, 0x8000, 0xc000])

print_path(navigate_best(graph, 0x1234))