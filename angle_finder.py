import collections
import heapq

import movements

COST_FUDGE = 3.0
COST_TABLE = {}

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

    print("\nDone.")
    return graph


def cost_of_path(path):
    cost = 0
    last = None
    for next in path:
        cost += COST_TABLE[last][next]
    return cost


def navigate_all(graph, angle, path=None, seen=None, flex=COST_FUDGE):
    if path is None:
        path = []
        seen = set()

    node = graph[angle]

    if None in node.edges_in:
        yield angle, list(reversed(path))

    elif angle in seen:
        pass

    else:
        seen.add(angle)

        edges = sorted(node.edges_in.values(), key=lambda e: e.cost)
        for edge in edges:
            new_flex = (node.best - edge.cost) + flex

            if new_flex < 0:
                break

            path.append(edge.movement)
            yield from navigate_all(graph, edge.from_angle, path, seen, new_flex)
            path.pop()

        seen.remove(angle)


def print_path(angle, path):
    print(f"start at {hex(angle)}")

    for movement in path:
        angle = movements.table[movement](angle) & 0xFFFF
        print(f"{movement} to {hex(angle)}")


def collect_paths(graph, angle, sample_size=20, number=10):
    paths = []

    for angle, path in navigate_all(graph, angle):
        paths.append((cost_of_path(path), angle, path))

        if len(paths) == sample_size:
            break

    paths.sort()
    return paths[:number]


COST_TABLE[None] = BASIC_COSTS.copy()
for movement, cost in BASIC_COSTS.items():
    COST_TABLE[movement] = BASIC_COSTS.copy()
for (first, then), cost in COST_OVERRIDES.items():
    COST_TABLE[first][then] = cost


if __name__ == "__main__":
    graph = explore([0x0000, 0xF546])
    print()

    for cost, angle, path in collect_paths(graph, 0x1234, sample_size=20, number=10):
        print(f"cost: {cost}\n-----")
        print_path(angle, path)
        print("-----\n")
