import sys
import pickle

# rounds up to next camera angle at e->f

# camera favored angles that end in f 
# will actually go to the next camera favored
# you can chain these together with ess up + targets
# until you hit a non xxxF camera angle

def ess(angle, left, amt):
    return (((angle + 0x0708*amt) if left else (angle - 0x0708*amt)) & 0xffff)

def turn(angle, left):
    angle = ess_up(angle)
    if not angle: return False
    return ((angle + 0x4000 if left else angle - 0x4000) & 0xffff)

def sidehop_roll(angle, left):
    return ((angle + 0x1cd8 if left else angle - 0x1cd8) & 0xffff)

def kokiri_spin(angle):
    return (angle - 0x0ccd) & 0xffff 

def biggoron_spin(angle):
    return (angle + 0x1219) & 0xffff

def biggoron_spin_shield(angle):
    return (angle + 0x04f5) & 0xffff

def back_roll(angle):
    left = True
    camera_angle = ess_up(angle)
    if not camera_angle:
        left = False
    elif camera_angle >= angle:
        left = False
    return ((angle + 0x3a98 if left else angle - 0x3a98) & 0xffff)

def backflip_roll(angle):
    return (angle - 0x3a98) & 0xffff

def shield_topright(angle):
    angle = ess_up(angle)
    if not angle: return False
    return (angle - 0x2000) & 0xffff

def shield_topleft(angle):
    angle = ess_up(angle)
    if not angle: return False
    return (angle + 0x2000) & 0xffff

def shield_bottomleft(angle):
    angle = ess_up(angle)
    if not angle: return False
    return (angle + 0x6000) & 0xffff

def shield_bottomright(angle):
    angle = ess_up(angle)
    if not angle: return False
    return (angle - 0x6000) & 0xffff

def ess_up(angle):

    # camera bullshit good lord 

    if ((angle >= 0x385f and angle < 0x4000) or
       (angle >= 0x794f and angle < 0x8000)):
       return False

    if (angle >= 0xff5f and angle < 0xff8f):
        return 0xff91

    if (angle >= 0xbe4f and angle < 0xbe7f):
        return 0xbe81

    if (angle >= 0xbe7f and angle < 0xbebf):
        return 0xbec1

    if (angle >= 0xbebf and angle < 0xc001):
        return False

    if (angle >= 0xff8f): 
        return False

    global camera_angles
    angle_hex = "{0:#0{1}x}".format(angle, 6) # 0xabcd
    for index in range(len(camera_angles)):
        camera_angle_hex = "{0:#0{1}x}".format(camera_angles[index], 6)
        if camera_angle_hex[:5] >= angle_hex[:5]:
            # more camera bullshit go to hell
            if angle >= 0xf55f and angle < 0xf8bf and angle_hex[5:] == "f":
                index += 1
            if angle >= 0xf8bf:
                index += 1
            if angle >= 0xb43f and angle < 0xb85f and angle_hex[5:] == "f":
                index += 1
            if angle >= 0xb85f and angle < 0xc001:
                index += 1
            if angle_hex[5:] == "f":
                return camera_angles[index+1] & 0xffff
            return camera_angles[index] & 0xffff
        index += 1

def search_for(graph, types, max_ess, starting_angles, destination_angles, stop_after_first_match):
    seen = []

    for starting_angle in starting_angles:
        graph[starting_angle]['distance'] = 0
        graph[starting_angle]['parent'] = None
        graph[starting_angle]['methodology'] = 'base angle'
        graph[starting_angle]['seen'] = 'True'
        seen.append(graph[starting_angle])

    searching = True
    instructions = []

    while searching:
        # select unvisited node with smallest distance
        current_node = min(seen, key=lambda node: node['distance'])

        print("visiting {0:#0{1}x}...".format(graph.index(current_node), 6) + f" distance: {current_node['distance']} ({len(destination_angles)} left to find)")

        current_node['visited'] = True
        seen.remove(current_node)

        for neighbor in current_node['neighbors']:
            if graph[neighbor['value']]['seen']: continue
            if neighbor['description'].startswith('ess left') or neighbor['description'].startswith('ess right'):
                start = neighbor['description'].index('x') + 1
                if int(neighbor['description'][start:]) > max_ess:
                    continue
            if neighbor['type'] in types or neighbor['type'] == '':
                try:
                    graph[neighbor['value']]['distance']    = current_node['distance'] + 1
                    graph[neighbor['value']]['parent']      = current_node
                    graph[neighbor['value']]['methodology'] = neighbor['description']
                    graph[neighbor['value']]['seen']        = True
                    seen.append(graph[neighbor['value']])
                except:
                    pass

                # if neighbor['value'] in [0xbb20, 0xbb30, 0x2080, 0x2088, 0x9108]:
                #     traverse_node = graph[neighbor['value']]
                #     print(f"found prelim:  {traverse_node['distance']} !")
                #     instructions = []
                #     while traverse_node:
                #         instructions.append(f"{traverse_node['methodology']} to " + "{0:#0{1}x}".format(graph.index(traverse_node), 6))
                #         traverse_node = traverse_node['parent']
                #     for instruction in instructions[::-1]:
                #         print(instruction)

                if neighbor['value'] in destination_angles:
                    traverse_node = graph[neighbor['value']]
                    print(f"found ! distance: {traverse_node['distance']}")
                    instructions.append(f"--------------")
                    while traverse_node:
                        instructions.append(f"{traverse_node['methodology']} to " + "{0:#0{1}x}".format(graph.index(traverse_node), 6))
                        traverse_node = traverse_node['parent']
                    destination_angles.remove(neighbor['value'])
                    if stop_after_first_match:
                        searching = False
                        instructions.append(f"--------------")
                        break

                if len(destination_angles) == 0:
                    searching = False
                    instructions.append(f"--------------")
                    break

    print("finished searching for all destinations !")
    for instruction in instructions[::-1]:
        print(instruction)

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
            'value': ess_up(angle),
            'type': ''
        })
        for ess_amt in range(29):
            node['neighbors'].append({
                'description': f"ess left x{ess_amt}",
                'value': ess(angle, True, ess_amt),
                'type': ''
            })
            node['neighbors'].append({
                'description': f"ess right x{ess_amt}",
                'value': ess(angle, False, ess_amt),
                'type': ''
            })
        node['neighbors'].append({
            'description': "turn left",
            'value': turn(angle, True),
            'type': ''
        })
        node['neighbors'].append({
            'description': "turn right",
            'value': turn(angle, False),
            'type': ''
        })
        node['neighbors'].append({
            'description': "sidehop roll left",
            'value': sidehop_roll(angle, True),
            'type': 'no_carry'
        })
        node['neighbors'].append({
            'description': "sidehop roll right",
            'value': sidehop_roll(angle, False),
            'type': 'no_carry'
        })
        node['neighbors'].append({
            'description': "kokiri/master spin shield cancel",
            'value': kokiri_spin(angle),
            'type': 'sword'
        })
        node['neighbors'].append({
            'description': "biggoron spin",
            'value': biggoron_spin(angle),
            'type': 'biggoron'
        })
        node['neighbors'].append({
            'description': "biggoron spin shield cancel",
            'value': biggoron_spin_shield(angle),
            'type': 'biggoron'
        })
        node['neighbors'].append({
            'description': "ess down sideroll",
            'value': back_roll(angle),
            'type': 'no_carry'
        })
        node['neighbors'].append({
            'description': "backflip roll",
            'value': backflip_roll(angle),
            'type': 'no_carry'
        })
        node['neighbors'].append({
            'description': 'top right shield turn',
            'value': shield_topright(angle),
            'type': 'shield_corner'
        })
        node['neighbors'].append({
            'description': 'top left shield turn',
            'value': shield_topleft(angle),
            'type': 'shield_corner'
        })
        node['neighbors'].append({
            'description': 'bottom right shield turn',
            'value': shield_bottomright(angle),
            'type': 'shield_corner'
        })
        node['neighbors'].append({
            'description': 'bottom left shield turn',
            'value': shield_bottomleft(angle),
            'type': 'shield_corner'
        })
        graph.append(node)
        print(hex(angle))
    with open('graph.pickle', 'wb') as f:
        pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)

starting_angles    = [
    0x1111, 0x2222, 0x3333, 0x4444
]

destination_angles = [
    0x1234, 0x5678, 0x9abc, 0xdef0, 0xacab
]

stop_after_first_match = False
max_ess = 8
types   = ['sword', 'no_carry']
# types = ['sword', 'biggoron', 'no_carry', 'shield_corner']

search_for(graph, types, max_ess, starting_angles, destination_angles, stop_after_first_match)