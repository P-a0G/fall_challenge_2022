import sys
import math
import numpy as np
import random

directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}
BUILD_SCORE_THRESHOLD = 25


def debug_print(*args):
    print(*args, file=sys.stderr, flush=True)


def print_field(field):
    for line in field:
        strg = ''
        for e in line:
            strg += str(e).ljust(3)
        debug_print(strg)
    debug_print("\n")


width, height = [int(i) for i in input().split()]

scrap_amount_map = np.zeros((height, width), dtype=int)
owner_map = np.zeros((height, width), dtype=int)
recycler_map = np.zeros((height, width), dtype=int)

my_bots = np.zeros((height, width), dtype=int)
opp_bots = np.zeros((height, width), dtype=int)


class Cell:
    def __init__(self, args):
        self.scrap_amount, self.owner, self.units, self.recycler, self.can_build, self.can_spawn, self.in_range_of_recycler = args

    def __str__(self):
        return f'Element:   scrap amount:   {self.scrap_amount}\n' \
               f'           owner:          {self.owner}\n' \
               f'           units:          {self.units}\n' \
               f'           recycler:       {self.recycler}\n' \
               f'           can_build:      {self.can_build}\n' \
               f'           can_spawn:      {self.can_spawn}\n' \
               f'           in range of rec:{self.in_range_of_recycler}'


class Robot:
    def __init__(self, x, y, n=1):
        self.x = x
        self.y = y
        self.n = n

    def get_next_move(self, scrap_amount_map, owner_map):
        possibilities = []
        better_possibilites = []

        for d in directions.values():
            dx, dy = d
            new_x, new_y = self.x + dx, self.y + dy
            if 0 < new_x < height and 0 < new_y < width:
                if scrap_amount_map[new_x, new_y] > 0:
                    possibilities.append((new_x, new_y))
                    if owner_map[new_x, new_y] < 1:
                        better_possibilites.append((new_x, new_y))

        if len(possibilities) == 0:
            return None

        if len(better_possibilites) > 0:
            moves = random.sample(better_possibilites, min(self.n, len(better_possibilites)))  # todo move robots separately
        else:
            moves = [(width // 2, height // 2)]

        output = []
        for x, y in moves:
            output.append(f'MOVE {1} {self.y} {self.x} {y} {x}')
        return output

    def give_target(self, x, y):
        return f'MOVE {self.n} {self.y} {self.x} {y} {x}'


# game loop
while True:
    my_matter, opp_matter = [int(i) for i in input().split()]
    debug_print("my matter:", my_matter, "opp matter:", opp_matter)

    cells = []
    my_bots_objects = []
    possible_spaw_positions = []
    possible_build_positions = []

    for i in range(height):
        for j in range(width):
            cell = Cell([int(k) for k in input().split()])
            cells.append(cell)

            # owner: 1 = me, 0 = foe, -1 = neutral
            scrap_amount_map[i, j] = cell.scrap_amount
            owner_map[i, j] = cell.owner
            recycler_map[i, j] = cell.recycler

            if cell.units:
                if cell.owner == 1:
                    my_bots[i, j] = cell.units
                    my_bots_objects.append(Robot(i, j, cell.units))
                else:
                    opp_bots[i, j] = cell.units

            if cell.can_build:
                possible_build_positions.append([i, j, 0])

            if cell.can_spawn and not cell.units:
                possible_spaw_positions.append((i, j))

    # compute build scores
    for i in range(len(possible_build_positions)):
        x, y, _ = possible_build_positions[i]
        possible_build_positions[i][-1] += scrap_amount_map[x, y]

        for d in directions.values():
            dx, dy = d
            new_x, new_y = x + dx, y + dy
            if 0 < new_x < height and 0 < new_y < width:
                possible_build_positions[i][-1] += scrap_amount_map[new_x, new_y]
                if recycler_map[new_x, new_y]:
                    possible_build_positions[i][-1] -= 20

    possible_build_positions.sort(key=lambda x: x[-1])

    actions = []

    for robot in my_bots_objects:
        moves = robot.get_next_move(scrap_amount_map, owner_map)
        if moves is not None:
            actions += moves

    # farm
    if len(my_bots_objects) >= 4 and len(possible_build_positions) > 0:
        x, y, score = possible_build_positions.pop(-1)
        while my_matter >= 10 and score >= BUILD_SCORE_THRESHOLD:
            actions.append(f'BUILD {y} {x}')
            my_matter -= 10
            if len(possible_build_positions) == 0:
                break
            x, y, score = possible_build_positions.pop(-1)

    # spawn
    if my_matter >= 10 and len(possible_spaw_positions) > 0:
        random_spawns = random.sample(possible_spaw_positions, min(my_matter // 10, len(possible_spaw_positions)))
        for x, y in random_spawns:
            actions.append(f"SPAWN {1} {y} {x}")

    print_field(scrap_amount_map)

    print(';'.join(actions) if len(actions) > 0 else 'WAIT')


# To debug: print("Debug messages...", file=sys.stderr, flush=True)

