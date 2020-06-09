import gzip



def hexhw(value):
    return "{0:#0{1}x}".format(value, 6)

# generally just ess up, but also considered adjusting
# the camera when turning left / right / 180
def ess_up_adjust_noncached(angle):

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

CAMERA_SNAPS = []

try:
    with gzip.open("camera_snaps.txt.gz", "rt") as cam:
        for line in cam:
            if line.strip() == "False":
                CAMERA_SNAPS.append(False)
            else:
                CAMERA_SNAPS.append(int(line))
except:
    camera_angles = []
    with open('camera_favored.txt', 'r') as f:
        for line in f:
            camera_angles.append(int(line.strip(), 16))

    for angle in range(0xFFFF + 1):
        print(f"Caching camera movements ({hexhw(angle)})...", end="\r")
        CAMERA_SNAPS.append(ess_up_adjust_noncached(angle))
    print("\nDone.")

    with gzip.open("camera_snaps.txt.gz", "wt") as cam:
        for angle in CAMERA_SNAPS:
            print(angle, file=cam)

def ess_up_adjust(angle):
    return CAMERA_SNAPS[angle]


# basic movement options

def ess(angle, left, amt):
    return (((angle + 0x0708*amt) if left else (angle - 0x0708*amt)) & 0xffff)

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

def hammer_shield_cancel(angle):
    return (angle - 0x0f90) & 0xffff

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
