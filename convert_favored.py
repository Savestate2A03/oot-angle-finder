with open('camera_favored.txt', 'r') as f:
    with open('js/camera_favored.ts', 'w') as w:
        w.write("export const FAVORED_ANGLES = [\n\t")
        lines = f.readlines()
        camera_angles = []
        count = 0
        for line in lines:
            v = line.strip()
            w.write("0x" + v + ",")
            count += 1
            if count % 16 == 0:
                w.write("\n\t")
        w.write("\n];\n")