import gzip

# generally just ess up, but also considered adjusting
# the camera when turning left / right / 180
def ess_up_adjust_noncached(angle):

    # camera bullshit as determined by manual testing

    # these snap to 0x4000
    if (0x385F <= angle < 0x4000):
        return 0x4000

    # these snap to 0x8000
    if (0x794F <= angle < 0x8000):
        return 0x8000

    # these snap to 0xc001
    if 0xBEBF <= angle < 0xC001:
        return False

    # these snap to 0x0000
    if 0xFF8F <= angle:
        return False

    # these gravitate towards 0xbe81
    if 0xBE4F <= angle < 0xBE7F:
        return 0xBE81

    # these gravitate towards 0xbec1
    if 0xBE7F <= angle < 0xBEBF:
        return 0xBEC1

    # these gravitate towards 0xff91
    if 0xFF5F <= angle < 0xFF8F:
        return 0xFF91

    global camera_angles
    for index in range(len(camera_angles)):
        camera_angle = camera_angles[index]
        if (camera_angle & 0xFFF0) >= (angle & 0xFFF0):
            # more camera bullshit go to hell
            if (0xF55F <= angle < 0xF8BF) and (angle & 0xF == 0xF):
                index += 1  # if we're in the above range and last char is f
            if 0xF8BF <= angle:
                index += 1  # however this happens automatically when above 0xf8bf
            if (0xB43F <= angle < 0xB85F) and (angle & 0xF == 0xF):
                index += 1  # samething but for another value range
            if 0xB85F <= angle < 0xC001:
                index += 1  # automatic again
            if angle & 0xF == 0xF:
                # snapping up happens on the f threshold apparently
                return camera_angles[index + 1] & 0xFFFF
            return camera_angles[index] & 0xFFFF
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
    with open("camera_favored.txt", "r") as f:
        for line in f:
            camera_angles.append(int(line.strip(), 16))

    for angle in range(0xFFFF + 1):
        if (angle % 0x1000) == 0:
            print(f"Caching camera movements ({hex(angle)})...", end="\r")
        CAMERA_SNAPS.append(ess_up_adjust_noncached(angle))
    print("\nDone.")

    with gzip.open("camera_snaps.txt.gz", "wt") as cam:
        for angle in CAMERA_SNAPS:
            print(angle, file=cam)


def ess_up_adjust(angle):
    return CAMERA_SNAPS[angle]


# basic movement options

def ess_left(angle):
    return angle + 0x0708


def ess_right(angle):
    return angle - 0x0708


def turn_left(angle):
    angle = ess_up_adjust(angle)  # camera auto adjusts similar to ess up
    if not angle:
        return None
    return angle + 0x4000


def turn_right(angle):
    angle = ess_up_adjust(angle)
    if not angle:
        return None
    return angle - 0x4000


def turn_180(angle):
    angle = ess_up_adjust(angle)
    if not angle:
        return None
    return angle + 0x8000


# no_carry movement options. these can be
# executed when Link isn't holding anything

def sidehop_sideroll_left(angle):
    return angle + 0x1CD8


def sidehop_sideroll_right(angle):
    return angle - 0x1CD8


def ess_down_sideroll(angle):
    left = True
    camera_angle = ess_up_adjust(angle)
    # link always rolls right when the camera is auto snapping
    if not camera_angle:
        left = False
    elif camera_angle >= angle:  # left / right depends on camera
        left = False
    return angle + 0x3A98 if left else angle - 0x3A98


def backflip_sideroll(angle):
    # forces a right roll even if ess down roll goes left
    return angle - 0x3A98


# sword-related movement

def sword_spin_shield_cancel(angle):
    return angle - 0x0CCD


def biggoron_slash_shield_cancel(angle):
    return angle + 0x1219


def biggoron_quickspin_shield_cancel(angle):
    return angle - 0x0D24


def hammer_shield_cancel(angle):
    return angle - 0x0F90


# perfect corner shield turns (n64 only)

def shield_topright(angle):
    angle = ess_up_adjust(angle)
    if not angle:
        return None
    return angle - 0x2000


def shield_topleft(angle):
    angle = ess_up_adjust(angle)
    if not angle:
        return None
    return angle + 0x2000


def shield_bottomleft(angle):
    angle = ess_up_adjust(angle)
    if not angle:
        return None
    return angle + 0x6000


def shield_bottomright(angle):
    angle = ess_up_adjust(angle)
    if not angle:
        return None
    return angle - 0x6000


table = {
    "ess up": ess_up_adjust,
    "ess right": ess_right,
    "ess left": ess_left,
    "turn right": turn_right,
    "turn left": turn_left,
    "turn 180": turn_180,
    "sidehop sideroll left": sidehop_sideroll_left,
    "sidehop sideroll right": sidehop_sideroll_right,
    "ess down sideroll": ess_down_sideroll,
    "backflip sideroll": backflip_sideroll,
    "sword spin shield cancel": sword_spin_shield_cancel,
    "biggoron slash shield cancel": biggoron_slash_shield_cancel,
    "biggoron quickspin shield cancel": biggoron_quickspin_shield_cancel,
    "hammer shield cancel": hammer_shield_cancel,
    "shield top-right": shield_topright,
    "shield top-left": shield_topleft,
    "shield bottom-left": shield_bottomleft,
    "shield bottom-right": shield_bottomright,
}
