import collections
import heapq

import motions


# QUICK USAGE:
#
# BASIC_COSTS --- How to rank each motion.
#      "ess up": 0.5,
#      "turn left": 1.0,
#    means that "turn left" is 2x faster/easier than "ess up".
#
# COST_CHAINS --- Sequential motions that are faster/slower.
#      ("ess left", "ess left"): 0.5,
#    means that every "ess left" preceded by an "ess left" costs 0.5.
#
#    e.g. "ess left / turn left / ess left" = 1.0 + 1.0 + 1.0
#    but  "ess left / ess left  / ess left" = 1.0 + 0.5 + 0.5
#
# COST_FLEX --- When returning multiple possible motion sequences, how much the
# total cost can deviate from optimal before it's not worth considering.
#
# Go to the bottom of this file to select angles and run the search.


COST_FLEX = 3.0
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
COST_CHAINS = {
    ("ess left", "ess left"): 0.5,
    ("ess right", "ess right"): 0.5,
}


# ALGORITHM OVERVIEW
#
# There are 65536 angles possible, ranging 0x0000-0xFFFF.  There are several
# motions available that change the angle in different ways.
#
# The state of Link's angle is represented by a directed graph.  The nodes are
# angles; the edges are motions between angles.  We want to navigate the graph
# from one node to another in a way that minimizes the cost.
#
#     0x0000 -----(ess left)---------> 0x0708
#        \
#         --(sidehop sideroll left)--> 0xF070
#      ...
#
# The camera is pretty complicated, so some motions don't just "rotate Link
# X units clockwise".  In other words, they're not linear, or even invertible.
# We treat individual motions as opaque functions from angles to angles.  Those
# functions are located in "motions.py".
#
# The algorithm is:
#    1. Construct an empty graph.
#    2. Mark edges in the graph, exploring the fastest nodes first.
#    3. Walk backwards through the graph, starting from the final angle.
#
# Angles can be reached from many motion sequences.  The scoring we use won't
# be perfect for everyone, so to allow some variation we record multiple
# motions into each angle.  Specifically, at each node, we record the best
# edge into it for a given motion, treating our scoring as perfect.  Then, at
# the end, we return paths that are roughly as fast as the best path.  This
# seems to work well.


# Node
#   edges_in   - list of edges into this node
#   best       - float cost of the fastest path to this node; 'None' if the
#                node hasn't been encountered yet
# Edge
#   from_angle - integer angle (not a node object) this edge comes from
#   motion     - string, e.g. "ess up"
#   cost       - float cost of the fastest path to this edge, plus the cost of
#                the motion - could be different from the destination node's
#                'best' if this edge isn't on the fastest path to the node
Node = collections.namedtuple("Node", ["edges_in", "best"])
Edge = collections.namedtuple("Edge", ["from_angle", "motion", "cost"])

empty_node = lambda: Node(edges_in={}, best=None)


def maybe_add_edge(graph, edge, to_angle):
    """
    Add an edge to an angle, but only if the edge is the fastest way to get to
    the node for a given motion.

    Returns True if the edge was added, False if it wasn't.
    """

    def min_none(x, y):
        return x if (x is not None and x < y) else y

    to_node = graph[to_angle]
    edges_in = to_node.edges_in

    def add_edge():
        edges_in[edge.motion] = edge
        best = min_none(to_node.best, edge.cost)
        graph[to_angle] = Node(edges_in, best)

    if to_node.best == None:
        add_edge()  # first edge to the node
        return True

    if edge.cost > to_node.best + COST_FLEX:
        # edge costs too much
        return False

    if (edge.motion not in edges_in) or (edge.cost < edges_in[edge.motion].cost):
        # first edge via this motion, or cheaper than the previous edge via this motion
        add_edge()
        return True

    # have already found this node, via this motion, at least as quickly
    return False


def edges_out(graph, angle, last_motion, last_cost):
    """
    Iterator of edges out of an angle, given some particular previous motion and
    cost.  Needs the previous motion to calculate the cost of a chained motion.
    """

    if graph[angle].best < last_cost:
        # skip all edges if this edge isn't the cheapest way out
        # misses some valid edges, but it doesn't seem to matter much
        return

    for (motion, cost_increase) in COST_TABLE[last_motion].items():
        new_angle = motions.table[motion](angle)

        if new_angle is None:
            continue

        to_angle = new_angle & 0xFFFF
        from_angle = angle
        cost = last_cost + cost_increase

        yield (to_angle, Edge(from_angle, motion, cost))


def explore(starting_angles):
    """Produce a graph from the given starting angles."""

    graph = [empty_node() for _ in range(0xFFFF + 1)]
    queue = []  # priority queue of '(edge_cost, from_angle, last_motion)'
    seen = 0

    for angle in starting_angles:
        edges_in = {None: Edge(from_angle=None, motion=None, cost=0)}
        best = 0

        graph[angle] = Node(edges_in, best)
        heapq.heappush(queue, (0.0, angle, None))
        seen += 1

    should_print = 0  # only print status every 100 iterations

    while len(queue) > 0:
        if should_print == 0:
            print(f"Exploring ({len(queue)})...", end="\r")
            should_print = 100
        should_print -= 1

        if seen == (0xFFFF + 1):
            # have encountered all nodes, exit early
            # misses some valid edges, but it doesn't seem to matter much
            break

        (cost, angle, motion) = heapq.heappop(queue)

        for to_angle, edge in edges_out(graph, angle, motion, cost):
            if graph[to_angle].best == None:
                seen += 1

            if maybe_add_edge(graph, edge, to_angle):
                # this is a new or cheaper edge, explore from here
                heapq.heappush(queue, (edge.cost, to_angle, edge.motion))

    print("\nDone.")
    return graph


# A path is a list of motions, e.g. ["ess up", "ess up", "turn left"].


def cost_of_path(path):
    cost = 0
    last = None
    for next in path:
        cost += COST_TABLE[last][next]
    return cost


def navigate_all(graph, angle, path=None, seen=None, flex=COST_FLEX):
    """
    Iterator of paths to a given angle, whose costs differ from the best
    path by no more than COST_FLEX.

    The first yielded path is guaranteed to be the cheapest (or tied with other
    equally cheapest paths), but the second path is NOT necessarily
    second-cheapest (or tied with the first).  The costs of yielded paths are
    not ordered except for the first.

    Yields values of the form
        (angle, path)
    where 'angle' is an integer 0x0000-0xFFFF, and 'path' is a list of motions.
    """

    # 'flex' starts at the maximum permissible deviation from the optimal path.
    # As the function recurses, 'flex' decreases by the deviation from optimal
    # at each node.

    if path is None:
        # instantiate new objects in case the function is called multiple times
        path = []
        seen = set()

    node = graph[angle]

    if None in node.edges_in:
        # this is a starting node
        yield angle, list(reversed(path))

    elif angle in seen:
        # found a cycle (possible by e.g. 'ess left'->'ess right', where 'flex'
        # lets the running cost increase a little)
        pass

    else:
        seen.add(angle)

        # explore the fastest edges first
        # note that this doesn't guarantee the ordering of paths; some paths
        #   through a slower edge at this step might be faster in the end
        # however, A fastest path will be yielded first
        edges = sorted(node.edges_in.values(), key=lambda e: e.cost)

        for edge in edges:
            new_flex = (node.best - edge.cost) + flex

            if new_flex < 0:
                # ran out of flex!  any paths from here will cost too much
                break

            path.append(edge.motion)
            yield from navigate_all(graph, edge.from_angle, path, seen, new_flex)
            path.pop()

        seen.remove(angle)


def print_path(angle, path):
    print("start at {:#06x}".format(angle))

    for motion in path:
        angle = motions.table[motion](angle) & 0xFFFF
        print("{:28} to {:#06x}".format(motion, angle))


def collect_paths(graph, angle, sample_size=20, number=10):
    """Sample 'sample_size' paths, returning the 'number' cheapest of those.

    Returns a list of
        (cost, angle, path)
    where 'cost' is the float cost, 'angle' is an integer 0x0000-0xFFFF,
    and 'path' is a list of motions.
    """

    paths = []

    for angle, path in navigate_all(graph, angle):
        paths.append((cost_of_path(path), angle, path))

        if len(paths) == sample_size:
            break

    paths.sort()
    return paths[:number]


COST_TABLE[None] = BASIC_COSTS.copy()
for motion, cost in BASIC_COSTS.items():
    COST_TABLE[motion] = BASIC_COSTS.copy()
for (first, then), cost in COST_CHAINS.items():
    COST_TABLE[first][then] = cost


if __name__ == "__main__":
    # Create a graph starting at the given angles.
    graph = explore([0x0000, 0xF546])
    print()

    # Collect the 10 fastest sequences of the first 20 visited.  The fastest
    # sequence collected is at least tied as the fastest sequence overall.
    paths = collect_paths(graph, 0x1234, sample_size=20, number=10)

    for cost, angle, path in paths:
        print(f"cost: {cost}\n-----")
        print_path(angle, path)
        print("-----\n")

    if len(paths) == 0:
        print("No way to get to the desired angle!")
        print("Add some more motions.")
