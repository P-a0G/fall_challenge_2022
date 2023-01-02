import sys
import math
import numpy as np
import random

directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}
BUILD_SCORE_THRESHOLD = 20


def debug_print(*args):
    print(*args, file=sys.stderr, flush=True)


def print_field(field):
    for line in field:
        strg = ''
        for e in line:
            strg += str(e).ljust(3)
        debug_print(strg)
    debug_print("\n")


def distance(x, y, a, b):
    return abs(x - a) + abs(y - b)


width, height = [int(i) for i in input().split()]

scrap_amount_map = np.zeros((height, width), dtype=int)
owner_map = np.zeros((height, width), dtype=int)
units_map = np.zeros((height, width), dtype=int)
recycler_map = np.zeros((height, width), dtype=int)

my_bots = np.zeros((height, width), dtype=int)
opp_bots = np.zeros((height, width), dtype=int)
turn = 0


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
            if 0 <= new_x < height and 0 <= new_y < width:
                if scrap_amount_map[new_x, new_y] > 0 and recycler_map[new_x, new_y] == 0:
                    possibilities.append((new_x, new_y))
                    if owner_map[new_x, new_y] < 1:
                        better_possibilites.append((new_x, new_y))

        if len(possibilities) == 0:
            return None

        if len(better_possibilites) > 0:
            moves = random.sample(better_possibilites,
                                  min(self.n, len(better_possibilites)))
        else:
            target = self.get_target()

            if len(target) == 0:
                target = (height // 2, width // 2)
            moves = [target]

        output = []
        if len(moves) > 1:
            for x, y in moves:
                output.append(f'MOVE {1} {self.y} {self.x} {y} {x}')
                if owner_map[x, y] == -1:
                    owner_map[x, y] = 1
        else:
            x, y = moves[0]
            output.append(f'MOVE {self.n} {self.y} {self.x} {y} {x}')
        return output

    def get_target(self):
        seen_positions = []
        nodes_to_check = [(self.x, self.y)]

        while len(nodes_to_check) > 0:
            # debug_print(">>> nodes to check:", len(nodes_to_check), ":", nodes_to_check, "seen_pos:", len(seen_positions), ":", seen_positions)
            x, y = nodes_to_check.pop(0)
            seen_positions.append((x, y))

            for d in directions.values():
                dx, dy = d
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < height and 0 <= new_y < width:
                    if scrap_amount_map[new_x, new_y] > 0:
                        if (new_x, new_y) not in nodes_to_check and (new_x, new_y) not in seen_positions:
                            if owner_map[new_x, new_y] != 1 and recycler_map[new_x, new_y] == 0:
                                # debug_print("found closest: target positions de", self.x, self.y, "=", new_x, new_y, "scrap amount:",  scrap_amount_map[new_x, new_y])
                                return new_x, new_y

                            nodes_to_check.append((new_x, new_y))
        # debug_print("target positions de", self.x, self.y, "= []")
        return []

    def give_target(self, x, y):
        return [f'MOVE {self.n} {self.y} {self.x} {y} {x}']


def get_spawn_score(i, j, opp_bots_objects, my_bots_objects, owner_map):  # todo faire spawn proche des adversaires
    score = 0

    for robot in opp_bots_objects:
        if distance(i, j, robot.x, robot.y) <= 2:
            score += 1

    for d in directions.values():
        dx, dy = d
        new_x, new_y = i + dx, j + dy
        if 0 <= new_x < height and 0 <= new_y < width:
            if owner_map[new_x, new_y] == 0 and recycler_map[new_x, new_y] == 0:
                score += 10
            elif owner_map[new_x, new_y] == -1 and scrap_amount_map[new_x, new_y] > 0:
                score += 1

    return score


# game loop
while True:
    my_matter, opp_matter = [int(i) for i in input().split()]
    debug_print("my matter:", my_matter, "opp matter:", opp_matter)
    turn += 1

    cells = []
    my_bots_objects = []
    opp_bots_objects = []
    possible_spawn_positions = []
    possible_build_positions = []
    n_recyclers = 0
    n_opp_recyclers = 0

    for i in range(height):
        for j in range(width):
            cell = Cell([int(k) for k in input().split()])
            cells.append(cell)

            # owner: 1 = me, 0 = foe, -1 = neutral
            scrap_amount_map[i, j] = cell.scrap_amount
            owner_map[i, j] = cell.owner
            recycler_map[i, j] = cell.recycler
            units_map[i, j] = cell.units

            if cell.recycler:
                if cell.owner == 1:
                    n_recyclers += 1
                else:
                    n_opp_recyclers += 1

            if cell.units:
                if cell.owner == 1:
                    my_bots[i, j] = cell.units
                    my_bots_objects.append(Robot(i, j, cell.units))
                else:
                    opp_bots[i, j] = cell.units
                    opp_bots_objects.append(Robot(i, j, cell.units))

            if cell.can_build:
                possible_build_positions.append([i, j, 0])

            if cell.can_spawn:
                possible_spawn_positions.append([i, j, 0])

    # compute build scores
    print("possible build pos:", len(possible_build_positions), file=sys.stderr, flush=True)
    for i in range(len(possible_build_positions)):
        x, y, _ = possible_build_positions[i]

        # build to block opp
        """
        for d in directions.values():
            dx, dy = d
            new_x, new_y = x + dx, y + dy

            if 0 <= new_x < height and 0 <= new_y < width:
                owner = owner_map[new_x, new_y]
                if owner == 1:
                    possible_build_positions[i][-1] -= units_map[new_x, new_y]
                elif owner == 0:
                    possible_build_positions[i][-1] += units_map[new_x, new_y]
        """
        # build recycler to product resources
        if scrap_amount_map[x, y] < 3:
            continue

        possible_build_positions[i][-1] = scrap_amount_map[x, y]

        for d in directions.values():
            dx, dy = d
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < height and 0 <= new_y < width:
                if not (recycler_map[new_x, new_y] and owner_map[new_x, new_y] == 1) and scrap_amount_map[x, y] < \
                        scrap_amount_map[new_x, new_y]:
                    possible_build_positions[i][-1] += min(scrap_amount_map[new_x, new_y], scrap_amount_map[x, y])

    # compute spawn score
    for i in range(len(possible_spawn_positions)):
        x, y, _ = possible_spawn_positions[i]
        score = get_spawn_score(x, y, opp_bots_objects, my_bots_objects, owner_map)
        possible_spawn_positions[i][-1] = score

    possible_build_positions.sort(key=lambda x: x[-1])
    print("build score:", possible_build_positions[-1], file=sys.stderr, flush=True)
    possible_spawn_positions.sort(key=lambda x: x[-1])

    actions = []

    # send a robot into enemy camp
    min_dist = 50
    scout_robot_and_target = None
    for robot in my_bots_objects:
        for opp_robot in opp_bots_objects:
            dist0 = distance(robot.x, robot.y, opp_robot.x, opp_robot.y)
            if dist0 < min_dist:
                min_dist = dist0
                scout_robot_and_target = (robot.x, robot.y, opp_robot.x, opp_robot.y)

    if min_dist > 0 and scout_robot_and_target is not None:
        for robot in my_bots_objects:
            if robot.x == scout_robot_and_target[0] and robot.y == scout_robot_and_target[1]:
                actions += robot.give_target(scout_robot_and_target[2], scout_robot_and_target[3])
            else:
                moves = robot.get_next_move(scrap_amount_map, owner_map)
                if moves is not None:
                    actions += moves

    else:
        for robot in my_bots_objects:
            moves = robot.get_next_move(scrap_amount_map, owner_map)
            if moves is not None:
                actions += moves

    # farm
    if (turn <= 15 or n_recyclers < n_opp_recyclers) and len(my_bots_objects) >= 4 and len(possible_build_positions) > 0:
        x, y, score = possible_build_positions.pop(-1)
        actions.append(f'MESSAGE {"building"}')
        while my_matter >= 10 and score >= BUILD_SCORE_THRESHOLD:
            actions.append(f'BUILD {y} {x}')

            # remove recycler from possible position
            new_spawn_pos = []
            for i in range(len(possible_spawn_positions)):
                e1, e2, e3 = possible_spawn_positions[i]
                if e1 == x and e2 == y:
                    continue
                else:
                    new_spawn_pos.append((e1, e2, e3))
            possible_spawn_positions = new_spawn_pos

            my_matter -= 10
            if len(possible_build_positions) == 0:
                break
            x, y, score = possible_build_positions.pop(-1)

    # spawn
    if my_matter >= 10 and len(possible_spawn_positions) > 0:
        debug_print("possible spawn pos:", len(possible_spawn_positions), possible_spawn_positions)
        strategic_spawn_pos = [e for e in possible_spawn_positions if e[-1] > 10]

        if len(strategic_spawn_pos) > 0:
            debug_print("strategic spawn", len(strategic_spawn_pos))
            random_spawns = random.sample(strategic_spawn_pos, min(my_matter // 10, len(strategic_spawn_pos)))
        else:
            debug_print("random spawn")
            random_spawns = []
            my_matter_cpy = my_matter
            while my_matter_cpy >= 10 and len(possible_spawn_positions) > 0:
                random_spawns.append(possible_spawn_positions.pop(-1))
                my_matter_cpy -= 10

        for x, y, score in random_spawns:
            actions.append(f"SPAWN {my_matter // 10 // len(random_spawns)} {y} {x}")

    # print_field(scrap_amount_map)

    debug_print("actions:", actions)
    print(';'.join(actions) if len(actions) > 0 else 'WAIT')

# To debug: print("Debug messages...", file=sys.stderr, flush=True)

