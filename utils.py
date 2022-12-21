import numpy as np


def debug_map(cells, h, w):
    robot_map = np.zeros((h, w), dtype=int)
    scrap_map = np.zeros((h, w), dtype=int)
    owner_map = np.zeros((h, w), dtype=int)
    recycler_map = np.zeros((h, w), dtype=int)
    for k in cells:
        i, j = k

        robot_map[i, j] = cells[k].units
        scrap_map[i, j] = cells[k].scrap
        owner_map[i, j] = cells[k].owner
        recycler_map[i, j] = cells[k].recycler

    # print("Scrap map:")
    # for line in scrap_map:
    #     strg = ''
    #     for e in line:
    #         strg += str(e).ljust(3) if e > 0 else ".".ljust(3)
    #     print(strg)
    # print("\n")

    # print_map("Robot", robot_map, scrap_map)
    print_map("Owner", owner_map, scrap_map)
    print_map("Recycler", recycler_map, scrap_map)


def print_map(strg, map0, scrap_map):
    print(f"{strg} map:")
    for i, line in enumerate(map0):
        strg = ''
        for j, e in enumerate(line):
            blank = " " if scrap_map[i, j] == 0 else "."
            strg += str(e).ljust(3) if e > 0 else blank.ljust(3)
        print(strg)
    print("\n")

