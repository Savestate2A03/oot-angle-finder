import collections
import heapq

import movements

COST_FUDGE = 3.0
COST_TABLE = {}

BASIC_COSTS = {
    "ess up": 0.5,
    "ess left": 1.0,
    "ess right": 1.0,
    "turn left": 2.0,
    "turn right": 2.0,
    "turn 180": 2.0,
    "sidehop sideroll left": 2.0,
    "sidehop sideroll right": 2.0,
    "ess down sideroll": 2.0,
    "backflip sideroll": 2.0,
    "kokiri spin": 2.0,
    # "biggoron spin": 2.0,
    # "biggoron spin shield": 2.0,
    # "hammer shield cancel": 2.0,
    # "shield top-right": 2.0,
    # "shield top-left": 2.0,
    # "shield bottom-left": 2.0,
    # "shield bottom-right": 2.0,
}
COST_OVERRIDES = {
    ("ess left", "ess left"): 0.5,
    ("ess right", "ess right"): 0.5,
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
            print(f"start at {movements.hexhw(angle)}")
        else:
            print(f"{motion} to {movements.hexhw(angle)}")


COST_TABLE[None] = BASIC_COSTS.copy()
for movement, cost in BASIC_COSTS.items():
    COST_TABLE[movement] = BASIC_COSTS.copy()
for (first, then), cost in COST_OVERRIDES.items():
    COST_TABLE[first][then] = cost


graph = explore([0x0000, 0xF546])
print()
print_path(navigate_best(graph, 0x1234))
