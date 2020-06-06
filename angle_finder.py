import sys
import pickle
import math
import io
import shutil
import heapq
import csv

def hexhw(value):
    return "{0:#0{1}x}".format(value, 6)

# basic movement options

def ess(angle, left, amt):
    return (((angle + 0x0708*amt) if left else (angle - 0x0708*amt)) & 0xffff)

# generally just ess up, but also considered adjusting
# the camera when turning left / right / 180
def ess_up_adjust(angle):

    # camera bullshit as determined by manual testing

    # don't bother, these just snap to 0x4000 and 0x8000
    if ((angle >= 0x385f and angle < 0x4000) or
       (angle >= 0x794f and angle < 0x8000)):
       return False

    # these gravitate towards 0xff91
    if (angle >= 0xff5f and angle < 0xff8f):
        return 0xff91

    # these gravitate towards 0xbe81
    if (angle >= 0xbe4f and angle < 0xbe7f):
        return 0xbe81

    # these gravitate towards 0xbec1
    if (angle >= 0xbe7f and angle < 0xbebf):
        return 0xbec1

    # these snap to 0xc001
    if (angle >= 0xbebf and angle < 0xc001):
        return False

    # these snap to 0x0000
    if (angle >= 0xff8f): 
        return False

    global camera_angles
    angle_hex = hexhw(angle) # 0xabcd
    for index in range(len(camera_angles)):
        camera_angle_hex = hexhw(camera_angles[index]) # 0xabcd
        if camera_angle_hex[:5] >= angle_hex[:5]:
            # more camera bullshit go to hell
            if angle >= 0xf55f and angle < 0xf8bf and angle_hex[5:] == "f":
                index += 1 # if we're in the above range and last char is f
            if angle >= 0xf8bf:
                index += 1 # however this happens automatically when above 0xf8bf
            if angle >= 0xb43f and angle < 0xb85f and angle_hex[5:] == "f":
                index += 1 # samething but for another value range
            if angle >= 0xb85f and angle < 0xc001:
                index += 1 # automatic again
            if angle_hex[5:] == "f":
                # snapping up happens on the f threshold apparently
                return camera_angles[index+1] & 0xffff 
            return camera_angles[index] & 0xffff
        index += 1

def turn(angle, left):
    angle = ess_up_adjust(angle) # camera auto adjusts similar to ess up
    if not angle: return False
    return ((angle + 0x4000 if left else angle - 0x4000) & 0xffff)

def turn_180(angle):
    angle = ess_up_adjust(angle) # camera auto adjusts similar to ess up
    if not angle: return False
    return (angle + 0x8000) & 0xffff

# no_carry movement options. these can be 
# executed when Link isn't holding anything

def sidehop_sideroll(angle, left):
    return ((angle + 0x1cd8 if left else angle - 0x1cd8) & 0xffff)

def ess_down_sideroll(angle):
    left = True
    camera_angle = ess_up_adjust(angle)
    # link always rolls right when the camera is auto snapping
    if not camera_angle:
        left = False
    elif camera_angle >= angle: # left / right depends on camera
        left = False
    return ((angle + 0x3a98 if left else angle - 0x3a98) & 0xffff)

# forces a right roll even if ess down roll goes left
def backflip_sideroll(angle):
    return (angle - 0x3a98) & 0xffff

# sword-related movement

def kokiri_spin(angle):
    return (angle - 0x0ccd) & 0xffff 

def biggoron_spin(angle):
    return (angle + 0x1219) & 0xffff

def biggoron_spin_shield(angle):
    return (angle + 0x04f5) & 0xffff

# perfect corner shield turns (n64 only) 
def shield_topright(angle):
    angle = ess_up_adjust(angle)
    if not angle: return False
    return (angle - 0x2000) & 0xffff

def shield_topleft(angle):
    angle = ess_up_adjust(angle)
    if not angle: return False
    return (angle + 0x2000) & 0xffff

def shield_bottomleft(angle):
    angle = ess_up_adjust(angle)
    if not angle: return False
    return (angle + 0x6000) & 0xffff

def shield_bottomright(angle):
    angle = ess_up_adjust(angle)
    if not angle: return False
    return (angle - 0x6000) & 0xffff

current_idx = 0
def search_for(graph, types, max_ess, starting_angles, destination_angles, stop_after_first_match, full_search, csv_out):
    seen_heap = []

    def push(angle):
        global current_idx
        heapq.heappush(seen_heap, (angle['distance'], current_idx, angle))
        current_idx = current_idx + 1

    def pop():
        if len(seen_heap) == 0:
            return None
        dist, id, top = heapq.heappop(seen_heap)
        return top

    for starting_angle in starting_angles:
        graph[starting_angle]['distance']    = 0
        graph[starting_angle]['parent']      = None
        graph[starting_angle]['methodology'] = 'base angle'
        graph[starting_angle]['seen']        = 'True'
        push(graph[starting_angle])

    searching     = True
    instructions  = {}
    solved_angles = {}
    visited       = 0
    lastDistance  = -1

    while searching:
        # select unvisited node with smallest distance
        current_node = pop()
        if current_node is None:
            print("Ran out of nodes. Done!")
            break
        visited += 1
        distance = current_node['distance']

        if distance != lastDistance:
            lastDistance = distance
            print(f"visiting {hexhw(graph.index(current_node))}..." + 
                    f" visited {visited}/{len(graph)}, seen {len(seen_heap)}, distance: {current_node['distance']} ({len(destination_angles)} left to find)")

        current_node['visited'] = True

        # look at each neighbor a node has, the neighbors are read from the current graph
        for neighbor in current_node['neighbors']:
            if graph[neighbor['value']]['seen']: continue # don't bother if we've seen the node
            if 'ess left' in neighbor['description'] or 'ess right' in neighbor['description']:
                # if we're essing left or right, grab the amount of turns for max check
                start = neighbor['description'].index('x') + 1
                if int(neighbor['description'][start:]) > max_ess:
                    continue
            # only check neighbors who are configured to be allowed
            if neighbor['type'] in types or neighbor['type'] == '':
                if 'ess up' in neighbor['description']:
                    graph[neighbor['value']]['distance'] = current_node['distance'] + 0.5
                elif 'turn' in neighbor['description']:
                    graph[neighbor['value']]['distance'] = current_node['distance'] + 0.5
                elif 'spin' in neighbor['description']:
                    graph[neighbor['value']]['distance'] = current_node['distance'] + 1.5
                else:
                    graph[neighbor['value']]['distance'] = current_node['distance'] + 1

                graph[neighbor['value']]['parent']       = current_node
                graph[neighbor['value']]['methodology']  = neighbor['description']
                graph[neighbor['value']]['seen']         = True
                push(graph[neighbor['value']]) # add to seen nodes for later visiting

                # no need to check for specific destination angles if doing a full search
                if full_search: 
                    continue

                # if the node we're looking at (not visiting) is one of the destination angles
                # we're looking for, go ahead and make note of it, and stop if we're just looking
                # for a single angle. otherwise, add it to the instructions array and carry on
                if neighbor['value'] in destination_angles:
                    # traverse parents until you reach a root node
                    traverse_node = graph[neighbor['value']]
                    print(f"found {hexhw(neighbor['value'])}! distance: {traverse_node['distance']} (visited {visited}, {len(destination_angles)} left to find)")
                    instructions[hexhw(neighbor['value'])] = []
                    while traverse_node:
                        instructions[hexhw(neighbor['value'])].append(f"{traverse_node['methodology']} to " + hexhw(graph.index(traverse_node)))
                        traverse_node = traverse_node['parent']
                    instructions[hexhw(neighbor['value'])].reverse()
                    destination_angles.remove(neighbor['value'])
                    if stop_after_first_match:
                        searching = False
                        break

                # no more angles, finish up
                if len(destination_angles) == 0:
                    searching = False
                    break

    if not full_search:
        # print out results to user
        print("finished searching for all destinations! visited " + str(visited) + " nodes")
        dest_vals = sorted(instructions)

        if csv_out:
            print("writing csv ...")
            with open('searched.csv', 'w', newline='') as csvfile:
                fieldnames = ['angle', 'distance', 'instructions']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for dest_val in dest_vals:
                    writer.writerow({
                        'angle': dest_val,
                        'distance': graph[int(dest_val, 16)]['distance'],
                        'instructions': ", ".join(instructions[dest_val])
                    })

        with io.StringIO() as sio:
            print("--------------")
            for dest_val in dest_vals:
                for instruction in instructions[dest_val]:
                    print(instruction)
                    sio.write(instruction + "\n")
                print("--------------")
                sio.write("--------------\n")
            return sio.getvalue()
    else:
        # write full search to a file
        with io.StringIO() as sio:
            sio.write(f"full angle dump\n")
            sio.write(f"            types: {types}\n")
            sio.write(f"          max ess: {max_ess}\n")
            sio.write(f"  starting angles: {', '.join(hexhw(angle) for angle in starting_angles)}\n")
            # dumping all angles ...
            for angle in range(0x10000):
                if (angle % 512 == 0): # only show ocassional progress
                    print(f"writing {hexhw(angle)} ... ")
                sio.write(f"{hexhw(angle)}:\n")
                instructions = [] # clear out instructions array
                traverse_node = graph[angle]
                while traverse_node:
                    instructions.append(f"{traverse_node['methodology']} to " + hexhw(graph.index(traverse_node)))
                    traverse_node = traverse_node['parent']
                instructions.reverse()
                for instruction in instructions:
                    # write instructions in reverse order
                    sio.write(f"    {instruction}\n")
            # write string buffer to file
            with open('full_search.txt', 'w') as f:
                sio.seek(0)
                shutil.copyfileobj(sio, f)

# ----------------------------------------------------------------------

if __name__ == '__main__':
    # don't run on server
    with open('camera_favored.txt', 'r') as f:
        lines = f.readlines()
        camera_angles = []
        for line in lines:
            # process each camera angle as a hex number
            camera_angles.append(int(line.strip(), 16)) 

    generate_graph = False

    # generate graph
    graph = []
    if not generate_graph:
        with open('graph.pickle', 'rb') as f:
            graph = pickle.load(f)
    else:
        print("Generating graph up to 0xFFFF ...")
        for angle in range(0x10000):
            node = { 
                'neighbors': [],
                'visited': False,
                'seen': False,
                'distance': 10000,
                'parent': None,
                'methodology': ''
            }
            node['neighbors'].append({
                'description': "ess up",
                'value': ess_up_adjust(angle),
                'type': '',
                'adjustment': True
            })
            # search up to 28 left and right
            # any more won't seralize properly (but can be done for a single run)
            for ess_amt in range(29):
                node['neighbors'].append({
                    'description': f"ess left x{ess_amt}",
                    'value': ess(angle, True, ess_amt),
                    'type': '',
                    'adjustment': False
                })
                node['neighbors'].append({
                    'description': f"ess right x{ess_amt}",
                    'value': ess(angle, False, ess_amt),
                    'type': '',
                    'adjustment': False
                })
            node['neighbors'].append({
                'description': "turn left",
                'value': turn(angle, True),
                'type': '',
                'adjustment': True
            })
            node['neighbors'].append({
                'description': "turn right",
                'value': turn(angle, False),
                'type': '',
                'adjustment': True
            })
            node['neighbors'].append({
                'description': "turn 180",
                'value': turn_180(angle),
                'type': '',
                'adjustment': True
            })
            node['neighbors'].append({
                'description': "sidehop roll left",
                'value': sidehop_sideroll(angle, True),
                'type': 'no_carry',
                'adjustment': False
            })
            node['neighbors'].append({
                'description': "sidehop roll right",
                'value': sidehop_sideroll(angle, False),
                'type': 'no_carry',
                'adjustment': False
            })
            node['neighbors'].append({
                'description': "kokiri/master spin shield cancel",
                'value': kokiri_spin(angle),
                'type': 'sword',
                'adjustment': False
            })
            node['neighbors'].append({
                'description': "biggoron slash shield cancel",
                'value': biggoron_spin(angle),
                'type': 'biggoron',
                'adjustment': False
            })
            node['neighbors'].append({
                'description': "biggoron spin shield cancel",
                'value': biggoron_spin_shield(angle),
                'type': 'biggoron',
                'adjustment': False
            })
            node['neighbors'].append({
                'description': "ess down sideroll",
                'value': ess_down_sideroll(angle),
                'type': 'no_carry',
                'adjustment': False
            })
            node['neighbors'].append({
                'description': "backflip roll",
                'value': backflip_sideroll(angle),
                'type': 'no_carry',
                'adjustment': False
            })
            node['neighbors'].append({
                'description': 'top right shield turn',
                'value': shield_topright(angle),
                'type': 'shield_corner',
                'adjustment': True
            })
            node['neighbors'].append({
                'description': 'top left shield turn',
                'value': shield_topleft(angle),
                'type': 'shield_corner',
                'adjustment': True
            })
            node['neighbors'].append({
                'description': 'bottom right shield turn',
                'value': shield_bottomright(angle),
                'type': 'shield_corner',
                'adjustment': True
            })
            node['neighbors'].append({
                'description': 'bottom left shield turn',
                'value': shield_bottomleft(angle),
                'type': 'shield_corner',
                'adjustment': True
            })
            for neighbor in node['neighbors']:
                # alert about potential target + ess up in some cases
                if ((neighbor['value'] >= 0xf55f) or (neighbor['value'] >= 0xb43f and neighbor['value'] < 0xc000)) and neighbor['adjustment']:
                    neighbor['description'] = f"(may need target + tap up after) {neighbor['description']}"
            graph.append(node)
            if (angle % 512 == 0): # only print results ocassionally 
                print(hex(angle))
        try:
            with open('graph.pickle', 'wb') as f:
                pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)
        except:
            print("Failed to write graph") # can happen on large dumps

    starting_angles    = [
        0x0000, 0x4000, 0x8000, 0xc001
    ]

    destination_angles = [
        0x2342, 0xfff2, 0x7425, 0xacab, 0x1213, 0x1111
    ]

    max_ess = 8
    types   = ['sword', 'no_carry']
    # types = ['sword', 'biggoron', 'no_carry', 'shield_corner']

    stop_after_first_match = False
    full_search = False
    csv_out = True

    search_for(graph, types, max_ess, starting_angles, destination_angles, stop_after_first_match, full_search, csv_out)