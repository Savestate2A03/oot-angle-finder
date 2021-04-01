import collections
import heapq
import sys
from decimal import *

import motions


# QUICK USAGE:
#
# MOVEMENT_OPTIONS --- Motions grouped by the game state required to perform them.
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

getcontext().prec = 4 # Decimal to 4 places
sys.setrecursionlimit(5000) # basic searches can get a lil' wild

COST_FLEX = Decimal(3.0)
COST_TABLE = {}

MOVEMENT_OPTIONS = {
    "basic": [
        "ess right",
        "ess left",
    ],
    "target enabled": [
        "ess up",
        "turn right",
        "turn left",
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
        "biggoron quickspin shield cancel",
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
    "c-up frame turn": [
        "c-up frame turn left",
        "c-up frame turn right",
    ],
}
BASIC_COSTS = {
    "ess up": Decimal(0.75),
    "ess left": Decimal(0.75),
    "ess right": Decimal(0.75),
    "turn left": Decimal(1.0),
    "turn right": Decimal(1.0),
    "turn 180": Decimal(1.0),
    "sidehop sideroll left": Decimal(1.0),
    "sidehop sideroll right": Decimal(1.0),
    "ess down sideroll": Decimal(1.0),
    "backflip sideroll": Decimal(1.0),
    "sword spin shield cancel": Decimal(1.25),
    "biggoron slash shield cancel": Decimal(1),
    "biggoron quickspin shield cancel": Decimal(1.25),
    "hammer shield cancel": Decimal(1.25),
    "shield top-right": Decimal(1.0),
    "shield top-left": Decimal(1.0),
    "shield bottom-left": Decimal(1.0),
    "shield bottom-right": Decimal(1.0),
    "c-up frame turn left": Decimal(1.25),
    "c-up frame turn right": Decimal(1.25),
}
COST_CHAINS = {
    ("ess left", "ess left"): Decimal(0.075),
    ("ess right", "ess right"): Decimal(0.075),
    ("c-up frame turn left", "c-up frame turn left"): Decimal(0.25),
    ("c-up frame turn right", "c-up frame turn right"): Decimal(0.25),
}
TARGET_BEFORE = {
    "ess up": True,
    "ess left": False,
    "ess right": False,
    "turn left": True,
    "turn right": True,
    "turn 180": True,
    "sidehop sideroll left": False,
    "sidehop sideroll right": False,
    "ess down sideroll": False,
    "backflip sideroll": False,
    "sword quickspin shield cancel": False,
    "biggoron slash shield cancel": False,
    "biggoron spin shield cancel": False,
    "hammer shield cancel": False,
    "shield top-right": True,
    "shield top-left": True,
    "shield bottom-left": True,
    "shield bottom-right": True,
    "c-up frame turn left": False,
    "c-up frame turn right": False,
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


def maybe_add_edge(graph, edge, to_angle, avoid_angles):
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

    for avoid_range in avoid_angles:
        if avoid_range[0] <= edge.from_angle and avoid_range[1] >= edge.from_angle:
            if TARGET_BEFORE[edge.motion]:
                # not an allowed motion based on the avoid params
                return False

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


def explore(starting_angles, avoid_angles):
    """Produce a graph from the given starting angles."""

    graph = [empty_node() for _ in range(0xFFFF + 1)]
    queue = []  # priority queue of '(edge_cost, from_angle, last_motion)'
    seen = 0

    for angle in starting_angles:
        edges_in = {None: Edge(from_angle=None, motion=None, cost=0)}
        best = 0

        graph[angle] = Node(edges_in, best)
        heapq.heappush(queue, (Decimal(0.0), angle, None))
        seen += 1

    previous_cost = 0  # only print status when cost increases

    while len(queue) > 0:
        if seen == (0xFFFF + 1):
            # have encountered all nodes, exit early
            # misses some valid edges, but it doesn't seem to matter much
            break

        (cost, angle, motion) = heapq.heappop(queue)

        if cost > previous_cost + Decimal(1.0):
            print(f"Exploring ({len(queue)}), current cost at {cost}", end="\r")
            previous_cost = cost

        for to_angle, edge in edges_out(graph, angle, motion, cost):
            if graph[to_angle].best == None:
                seen += 1

            if maybe_add_edge(graph, edge, to_angle, avoid_angles):
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
        last = next
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
    # keep track of repeated motions to simplify the path reading
    prev_motion    = None
    iterations     = 1
    motions_output = []

    print("start at {:#06x}".format(angle))

    for motion in path:
        if prev_motion == motion:
            # keep track of how many times a motion is repeated
            iterations += 1
        elif prev_motion:
            # once it stops repeating, add it to the motion list
            motions_output.append({
                "motion": f"{iterations} {prev_motion}",
                "angle":  f"0x{angle:04x}"
            })
            iterations = 1

        # update the angle using the current motion and set prev_motion
        angle = motions.table[motion](angle) & 0xFFFF
        prev_motion = motion

    # finally, run one last time
    motions_output.append({
        "motion": f"{iterations} {prev_motion}",
        "angle":  f"0x{angle:04x}"
    })

    # get the padding amount based on the length for the largest motion string
    text_length = len(max([output["motion"] for output in motions_output], key=len))
    for motion in motions_output:
        # print out each motion
        print(f"{motion['motion']:<{text_length}} to {motion['angle']}")


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


def initialize_cost_table():
    COST_TABLE[None] = BASIC_COSTS.copy()

    for motion, cost in BASIC_COSTS.items():
        COST_TABLE[motion] = BASIC_COSTS.copy()
    for (first, then), cost in COST_CHAINS.items():
        COST_TABLE[first][then] = cost

    all_motions = set(BASIC_COSTS.keys())
    allowed_motions = {m for group in ALLOWED_GROUPS for m in MOVEMENT_OPTIONS[group]}
    disallowed_motions = all_motions - allowed_motions

    for motion in disallowed_motions:
        del COST_TABLE[motion]
    for first in COST_TABLE:
        for motion in disallowed_motions:
            del COST_TABLE[first][motion]


ALLOWED_GROUPS = ["basic", "target enabled", "no carry", "c-up frame turn"]

# ALLOWED_GROUPS = [
#     "basic",
#     "target enabled",
#     "no carry",
#     "sword",
#     "biggoron",
#     "hammer",
#     "shield corners",
#     "c-up frame turn"
# ]

initialize_cost_table()

if __name__ == "__main__":

    avoid = [
    #    examples, also note that when crossing
    #    0x0000 -> 0xffff, you have to split it up.
    #
    #    (0xdeb9, 0xffff),
    #    (0x0000, 0x6338)
    ]

    # Create a graph starting at the given angles.
    graph = explore([
        0x0000, 0x4000, 0x8000, 0xc000
    ], avoid)
    paths = []

    # Collect the 5 fastest sequences of the first 50 visited.  The fastest
    # sequence collected is at least tied as the fastest sequence overall.

    # PASTE IN YOUR HEX ANGLES BETWEEN angles = """ """
    # Example:
    #
    #     angles = """
    # 0100
    # 0124
    # 0144
    # 0205
    # 0333
    #     """
    #
    # make sure the first line (angles = """)
    # and last line (""") are indented properly!
    # four spaces to the left of each.

    angles = """
0bad
0dad
acab
1234
    """

    for line in angles.splitlines():
        line = line.strip()
        if not line:
            continue
        angle = int(line, 16)
        paths.extend(collect_paths(graph, angle, sample_size=35, number=4))

    paths.sort()

    for cost, angle, path in paths:
        print(f"cost: {cost}\n-----")
        print_path(angle, path)
        print("-----\n")

    if len(paths) == 0:
        print("No way to get to the desired angle!")
        print("Add some more motions.")
