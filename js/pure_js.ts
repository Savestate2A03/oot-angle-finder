let ESS_COUNT = 8;
let SWORD_ENABLED = true;
let BIGGORON_ENABLED = false;
let NO_CARRY_ENABLED = true;
let SHIELD_CORNER_ENABLED = false;

import {FAVORED_ANGLES} from './camera_favored.js';

/**
 * generally just ess up, but also considered adjusting
 * the camera when turning left / right / 180
 */
function ess_up_adjust(a: number): number {
    // camera bullshit as determined by manual testing

    // don't bother, these just snap to 0x4000 and 0x8000
    if ((a >= 0x385f && a < 0x4000) ||
        (a >= 0x794f && a < 0x8000)) {
        return null;
    }

    // these gravitate towards 0xff91
    if (a >= 0xff5f && a < 0xff8f) {
        return 0xff91;
    }

    // these gravitate towards 0xbe81
    if (a >= 0xbe4f && a < 0xbe7f) {
        return 0xbe81;
    }

    // these gravitate towards 0xbec1
    if (a >= 0xbe7f && a < 0xbebf) {
        return 0xbec1;
    }

    //these snap to 0xc001
    if (a >= 0xbebf && a < 0xc001) {
        return null;
    }

    // these snap to 0x0000
    if (a >= 0xff8f) {
        return null;
    }

    for (let i = 0; i < FAVORED_ANGLES.length; i++) {
        let camera_angle = FAVORED_ANGLES[i];
        if ((camera_angle & 0xFFF0) >= (a & 0xFFF0)) {
            // more camera bullshit go to hell
            if (a >= 0xF55F && a < 0xF8BF && (a & 0xF) === 0xF) {
                i++; // if we're in the above range and last char is f
            }
            if (a >= 0xF8BF) {
                i++; // however this happens automatically when above 0xf8bf
            }
            if (a >= 0xB43F && a < 0xB85F && (a & 0xF) === 0xF) {
                i++; // same thing but for another value range
            }
            if (a >= 0xB85F && a < 0xC001) {
                i++; // automatic again
            }
            if ((a & 0xF) === 0xF) {
                //snapping up happens on the f threshold apparently
                return FAVORED_ANGLES[i + 1];
            }
            return FAVORED_ANGLES[i];
        }
    }
    return null;
}

function ess_left(a, n): number {
    return (a + 0x0708 * n) & 0xFFFF;
}

function ess_right(a: number, n: number): number {
    return (a - 0x0708 * n) & 0xFFFF;
}

function turn_left(a: number): number {
    const cam = ess_up_adjust(a);
    if (cam === null) return null;
    return (cam + 0x4000) & 0xFFFF;
}

function turn_right(a) {
    // camera auto adjusts similar to ess up
    const cam = ess_up_adjust(a);
    if (cam === null) return null;
    return (cam - 0x4000) & 0xFFFF;
}

function turn_180(a) {
    // camera auto adjusts similar to ess up
    const cam = ess_up_adjust(a);
    if (cam === null) return null;
    return (cam + 0x8000) & 0xFFFF;
}

// No carry
function sidehop_roll_left(a) {
    return (a + 0x1CD8) & 0xFFFF;
}

function sidehop_roll_right(a) {
    return (a - 0x1CD8) & 0xFFFF;
}

function ess_down_sideroll(a) {
    let left = true;
    let camera_angle = ess_up_adjust(a);
    if (camera_angle === null) {
        left = false;
    } else if (camera_angle >= a) {
        left = false;
    }
    if (left) {
        return (a + 0x3A98) & 0xFFFF;
    } else {
        return (a - 0x3A98) & 0xFFFF;
    }
}

function backflip_roll(a) {
    return (a - 0x3A98) & 0xFFFF;
}

// Sword movement

function kokiri_spin(a) {
    return (a - 0x0CCD) & 0xFFFF;
}

function biggoron_spin(a) {
    return (a + 0x1219) & 0xFFFF;
}

function biggoron_spin_shield(a) {
    return (a + 0x04F5) & 0xFFFF;
}


// perfect corner shield turns (n64 only)
function shield_topright(a) {
    const cam = ess_up_adjust(a);
    if (cam === null) return null;
    return (cam - 0x2000) & 0xFFFF;
}

function shield_topleft(a: number): number {
    const cam = ess_up_adjust(a);
    if (cam === null) return null;
    return (cam + 0x2000) & 0xFFFF;
}

function shield_bottomleft(a: number): number {
    const cam = ess_up_adjust(a);
    if (cam === null) return null;
    return (cam + 0x6000) & 0xFFFF;
}

function shield_bottomright(a: number): number {
    const cam = ess_up_adjust(a);
    if (cam === null) return null;
    return (cam - 0x6000) & 0xFFFF;
}

enum MovementType_Type {
    ess_up,
    ess_left,
    ess_right,
    turn_left,
    turn_right,
    turn_180,

    sidehop_roll_left,
    sidehop_roll_right,
    ess_down_sideroll,
    backflip_roll,

    kokiri_spin,

    biggoron_spin,
    biggoron_spin_shield,

    shield_topright,
    shield_topleft,
    shield_bottomleft,
    shield_bottomright
}

interface MovementType {
    type: MovementType_Type;
    count?: number;
}

function isAdjustment(type: MovementType_Type): boolean {
    switch (type) {
        case MovementType_Type.ess_up:
        case MovementType_Type.turn_left:
        case MovementType_Type.turn_right:
        case MovementType_Type.turn_180:
        case MovementType_Type.shield_topright:
        case MovementType_Type.shield_topleft:
        case MovementType_Type.shield_bottomleft:
        case MovementType_Type.shield_bottomright:
            return true;
        case MovementType_Type.ess_left:
        case MovementType_Type.ess_right:
        case MovementType_Type.sidehop_roll_left:
        case MovementType_Type.sidehop_roll_right:
        case MovementType_Type.kokiri_spin:
        case MovementType_Type.biggoron_spin:
        case MovementType_Type.biggoron_spin_shield:
        case MovementType_Type.ess_down_sideroll:
        case MovementType_Type.backflip_roll:
            return false;
    }
}

function nameForType(type: MovementType_Type) {
    switch (type) {
        case MovementType_Type.ess_up:
            return "ess up";
        case MovementType_Type.ess_left:
            return "ess left";
        case MovementType_Type.ess_right:
            return "ess right";
        case MovementType_Type.turn_left:
            return "turn left";
        case MovementType_Type.turn_right:
            return "turn right";
        case MovementType_Type.sidehop_roll_left:
            return "sidehop roll left";
        case MovementType_Type.sidehop_roll_right:
            return "sidehop roll right";
        case MovementType_Type.kokiri_spin:
            return "kokori/master spin";
        case MovementType_Type.biggoron_spin:
            return "biggoron spin";
        case MovementType_Type.biggoron_spin_shield:
            return "biggoron spin shield cancel";
        case MovementType_Type.ess_down_sideroll:
            return "ess down sideroll";
        case MovementType_Type.backflip_roll:
            return "backflip roll";
        case MovementType_Type.shield_topright:
            return "shield top right";
        case MovementType_Type.shield_topleft:
            return "shield top left";
        case MovementType_Type.shield_bottomleft:
            return "shield bottom left";
        case MovementType_Type.shield_bottomright:
            return "shield bottom right";
        case MovementType_Type.turn_180:
            return "turn 180";
    }
}

interface Neighbor {
    movementType: MovementType;
    value: number;
}

interface GraphNode {
    value: number;
    neighbors: Neighbor[];
    distance: number;
}

class Heap {
    private heap: GraphNode[] = [];

    constructor() {
    }

    push(node: GraphNode) {
        this.heap.push(node)
        this.trickleUp();
    }

    pop(): GraphNode {
        let res = this.heap[0];
        if (this.heap.length > 1) {
            this.heap[0] = this.heap.pop();
        } else {
            this.heap.pop();
        }
        this.trickleDown();
        return res;
    }

    private trickleUp() {
        let current = this.heap.length - 1
        // Traversing up the parent node until the current node (current) is greater than the parent (current/2)
        while (true) {
            if (current < 1) {
                break;
            }
            const parent = Math.floor(current / 2);
            if (this.heap[parent].distance <= this.heap[current].distance) {
                break;
            }
            // swap
            [this.heap[parent], this.heap[current]] = [this.heap[current], this.heap[parent]];
            current = parent;
        }
    }

    private trickleDown() {
        let parent = 0;
        const last = this.heap.length - 1;
        while (true) {
            let leftChild = parent * 2 + 1;
            let rightChild = parent * 2 + 2;
            if (leftChild > last) break;
            if (rightChild > last) break;
            if (this.heap[leftChild].distance < this.heap[parent].distance) {
                // swap
                [this.heap[parent], this.heap[leftChild]] = [this.heap[leftChild], this.heap[parent]];
                parent = leftChild;
            } else if (this.heap[rightChild].distance < this.heap[parent].distance) {
                // swap
                [this.heap[parent], this.heap[rightChild]] = [this.heap[rightChild], this.heap[parent]];
                parent = rightChild;
            } else {
                break;
            }
        }
    }

    empty() {
        return this.heap.length == 0;
    }

    size() {
        return this.heap.length;
    }
}

function sort_nodes(a: GraphNode, b: GraphNode) {
    return a.distance > b.distance;
}

interface GenerationResults {
    longestPath: number;
    longestAngle: number;
    backPath: Uint16Array;
}

export function generateGraph(): GraphNode[] {
    const nodes: GraphNode[] = [];
    for (let i = 0; i <= 0xFFFF; i++) {
        nodes.push(generateNode(i));
    }
    console.log("Finished generating graph\n");
    return nodes;
}

function generateNode(a: number): GraphNode {
    let n: GraphNode = {
        distance: 0,
        value: a,
        neighbors: []
    };

    // it's so fast this isn't relevant
//    if (i % 0x1000 == 0) {
//      printf("Angle %x\n", i);
//    }
    // Stuff you can always do
    let _ess_up = ess_up_adjust(a);
    if (_ess_up !== null) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.ess_up},
            value: _ess_up
        });
    }

    for (let count = 1; count <= ESS_COUNT; count++) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.ess_left, count: count},
            value: ess_left(a, count)
        });
        n.neighbors.push({
            movementType: {type: MovementType_Type.ess_right, count: count},
            value: ess_right(a, count)
        });
    }
    let _turn_left = turn_left(a);
    if (_turn_left !== null) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.turn_left},
            value: _turn_left
        });
    }
    let _turn_right = turn_right(a);
    if (_turn_right !== null) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.turn_right},
            value: _turn_right
        });
    }
    let _turn_180 = turn_180(a);
    if (_turn_180 !== null) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.turn_180},
            value: _turn_180
        });
    }

    // Stuff you can do if you're not carrying anything
    if (NO_CARRY_ENABLED) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.sidehop_roll_left},
            value: sidehop_roll_left(a)
        });
        n.neighbors.push({
            movementType: {type: MovementType_Type.sidehop_roll_right},
            value: sidehop_roll_right(a)
        });
        n.neighbors.push({
            movementType: {type: MovementType_Type.ess_down_sideroll},
            value: ess_down_sideroll(a)
        });
        n.neighbors.push({
            movementType: {type: MovementType_Type.backflip_roll},
            value: backflip_roll(a)
        });
    }

    if (SWORD_ENABLED) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.kokiri_spin},
            value: kokiri_spin(a)
        });
    }

    if (BIGGORON_ENABLED) {
        n.neighbors.push({
            movementType: {type: MovementType_Type.biggoron_spin},
            value: biggoron_spin(a)
        });
        n.neighbors.push({
            movementType: {type: MovementType_Type.biggoron_spin_shield},
            value: biggoron_spin_shield(a)
        });
    }

    if (SHIELD_CORNER_ENABLED) {
        let _shield_topright = shield_topright(a);
        if (_shield_topright !== null) {
            n.neighbors.push({
                movementType: {type: MovementType_Type.shield_topright},
                value: _shield_topright
            });
        }
        let _shield_topleft = shield_topleft(a);
        if (_shield_topleft !== null) {
            n.neighbors.push({
                movementType: {type: MovementType_Type.shield_topleft},
                value: _shield_topleft
            });
        }
        let _shield_bottomright = shield_bottomright(a);
        if (_shield_bottomright !== null) {
            n.neighbors.push({
                movementType: {type: MovementType_Type.shield_bottomright},
                value: _shield_bottomright
            });
        }
        let _shield_bottomleft = shield_bottomleft(a);
        if (_shield_bottomleft !== null) {
            n.neighbors.push({
                movementType: {type: MovementType_Type.shield_bottomleft},
                value: _shield_bottomleft
            });
        }
    }
    return n;
}

export function generateFastestPaths(graph: GraphNode[], src: number): GenerationResults {
    const backPath = new Uint16Array(0x10000);
    const found = new Uint8Array(0x10000);
    let remaining = backPath.length - 1; // we found us, after all

    const heap = new Heap();

    heap.push(graph[src]);
    graph[src].distance = 0;

    backPath[src] = src;
    found[src] = 1;
    let visited = 0;
    let lastDistance = 0;
    let last: GraphNode | null = null;
    while (!heap.empty() && remaining > 0) {
        // Get the top of the heap
        let current = heap.pop();
        last = current;
        // Check the current distance
        let distance = current.distance;
        if (distance != lastDistance) {
            lastDistance = distance;
            console.log(`Distance: ${distance}, visited: ${visited}, found: ${0x10000 - remaining}, remaining: ${remaining}, heap size ${heap.size()}`);
        }
        if (distance > 100) {
            throw "BADd";
        }
        visited++;

        // For each neighbor
        for (let neighbor of current.neighbors) {
            if (found[neighbor.value] == 1) continue; // We don't care anymore, we already found a path tho this
            // Yay, someone new
            let node = graph[neighbor.value];
            node.distance = distance + 1;
            heap.push(node);
            found[node.value] = 1;
            backPath[node.value] = current.value;
            remaining--;
        }
    }

    return {
        longestPath: lastDistance,
        longestAngle: last.value,
        backPath: backPath
    };
}

export function pathForDest(backPath: Uint16Array, dest: number) {
    let stack: number[] = [];

    // Backtrace
    let a = dest;
    while (true) {
        let prev = backPath[a];
        if (prev == a) {
            stack.push(a);
            console.log("Done %04x to %04x!\n", prev, dest);
            break;
        }
        stack.push(a);
        a = prev;
    }
    stack.reverse();

    // Print
    let res = []

    function formatHex(n: number): string {
        return n.toString(16).padStart(4, '0');
    }

    res.push(`start angle ${formatHex(stack[0])}`);
    let previousAngle = stack[0];
    for (let i = 1; i < stack.length; i++) {
        let currentAngle = stack[i];
        let n = generateNode(previousAngle);
        let t: MovementType_Type;
        let count = 1;
        for (let neighbor of n.neighbors) {
            if (neighbor.value == currentAngle) {
                t = neighbor.movementType.type;
                count = neighbor.movementType.count;
            }
        }
        res.push(`${nameForType(t)} x${count} to ${formatHex(currentAngle)}`);
        previousAngle = currentAngle;
    }

    return res;
}