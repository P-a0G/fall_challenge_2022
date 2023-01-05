import sys
import math
import numpy as np
import random

directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}
BUILD_SCORE_THRESHOLD = 20
BUILD_MODE = True
STABLE_FIELD = False


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
range_of_my_recycle_map = np.zeros((height, width), dtype=int)
range_of_recycle_map = np.zeros((height, width), dtype=int)
dist_to_opp_map = np.ones((height, width), dtype=int) * 100

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


def get_invade_score(x, y):
    score = 0
    for d in directions.values():
        dx, dy = d
        new_x, new_y = x + dx, y + dy
        if 0 <= new_x < height and 0 <= new_y < width:
            # opp cell
            if owner_map[new_x, new_y] == 0:
                score += 1
            # neutral cell
            elif owner_map[new_x, new_y] == -1:
                score += 0.5
    return score


class Robot:
    def __init__(self, x, y, n=1):
        self.x = x
        self.y = y
        self.n = n

    def get_next_move(self, scrap_amount_map, owner_map):
        possibilities = []
        neutral_possibilities = []
        invade_possibilities = []

        for d in directions.values():
            dx, dy = d
            new_x, new_y = self.x + dx, self.y + dy
            if 0 <= new_x < height and 0 <= new_y < width:
                if scrap_amount_map[new_x, new_y] > 0 and recycler_map[new_x, new_y] == 0 and not(range_of_recycle_map[new_x, new_y] == 1 and scrap_amount_map[new_x, new_y] == 1):
                    possibilities.append((new_x, new_y))
                    if owner_map[new_x, new_y] == 0:
                        invade_possibilities.append((new_x, new_y))
                    elif owner_map[new_x, new_y] == -1:
                        neutral_possibilities.append((new_x, new_y))

        if len(possibilities) == 0:
            return None

        if len(invade_possibilities) > 0:
            invade_possibilities.sort(key=lambda e: get_invade_score(e[0], e[1]), reverse=True)

            output = []
            if self.n > len(invade_possibilities):
                x, y = invade_possibilities[0]
                output.append(f'MOVE {self.n - len(invade_possibilities) + 1} {self.y} {self.x} {y} {x}')

                for x, y in invade_possibilities[1:]:
                    output.append(f'MOVE 1 {self.y} {self.x} {y} {x}')

                return output

            for k in range(self.n):
                x, y = invade_possibilities[k]
                output.append(f'MOVE 1 {self.y} {self.x} {y} {x}')

            return output

        elif len(neutral_possibilities) > 0:
            # prioritize moves toward opponent
            if self.n == 1:
                neutral_possibilities.sort(key=lambda e: dist_to_opp_map[e[0], e[1]])
                moves = [neutral_possibilities[0]]

            else:
                moves = random.sample(neutral_possibilities,
                                      min(self.n, len(neutral_possibilities)))
        else:
            moves = self.get_target()

            if len(moves) == 0:
                moves = [(height // 2, width // 2)]


        output = []
        # going to a neutral map, go toward opp
        if len(neutral_possibilities) == 1 and len(possibilities) > 1 and owner_map[moves[0][0], moves[0][1]] == -1:
            x, y = moves[0]

            possibilities.sort(key=lambda e: dist_to_opp_map[e[0], e[1]])
            x2, y2 = possibilities[0]

            if x == x2 and y2 == y:
                output.append(f'MOVE {self.n} {self.y} {self.x} {y} {x}')
            else:
                output.append(f'MOVE {1} {self.y} {self.x} {y} {x}')
                output.append(f'MOVE {self.n - 1} {self.y} {self.x} {y2} {x2}')
        elif len(neutral_possibilities) == 2 \
                and self.x != neutral_possibilities[0][0] + neutral_possibilities[1][0] \
                and self.y != neutral_possibilities[0][1] + neutral_possibilities[1][1]:  # not opposite directions
            x, y = neutral_possibilities[0]
            x2, y2 = neutral_possibilities[1]
            if x == self.x:
                output.append(f'MOVE {1} {self.y} {self.x} {y} {x2}')
            else:
                output.append(f'MOVE {1} {self.y} {self.x} {y2} {x}')
        else:
            # convert moves to outputs
            if len(moves) > 1:
                # prioritize moves toward opponent
                if len(opp_bots_objects) > 0:
                    debug_print('DEBUG', moves)
                    moves.sort(key=lambda e: dist_to_opp_map[e[0], e[1]])

                moves = moves[:self.n]

                x, y = moves[0]
                x, y = self.target_further(x, y)
                output.append(f'MOVE {self.n - len(moves) + 1} {self.y} {self.x} {y} {x}')

                if len(moves) > 1:
                    for x, y in moves[1:]:
                        x, y = self.target_further(x, y)
                        output.append(f'MOVE {1} {self.y} {self.x} {y} {x}')
                        if owner_map[x, y] == -1:
                            owner_map[x, y] = 1
            else:
                x, y = moves[0]
                x, y = self.target_further(x, y)
                output.append(f'MOVE {self.n} {self.y} {self.x} {y} {x}')
        return output

    def target_further(self, x, y):
        if owner_map[x, y] != -1:
            return x, y

        n_x, n_y = 2 * x - self.x, 2 * y - self.y
        if 0 <= n_x < height and 0 <= n_y < width and scrap_amount_map[n_x, n_y] != 0 and not(recycler_map[n_x, n_y]):
            return n_x, n_y
        return x, y

    def get_target(self):
        seen_positions = []
        nodes_to_check = [(self.x, self.y, 0)]

        max_depth = 100
        output = []

        while len(nodes_to_check) > 0:
            # debug_print(">>> nodes to check:", len(nodes_to_check), ":", nodes_to_check, "seen_pos:", len(seen_positions), ":", seen_positions)
            x, y, depth = nodes_to_check.pop(0)
            seen_positions.append((x, y))

            if len(output) > 0 and depth > max_depth:
                continue

            for d in directions.values():
                dx, dy = d
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < height and 0 <= new_y < width:
                    if scrap_amount_map[new_x, new_y] > 0:
                        if (new_x, new_y) not in [(e1, e2) for e1, e2, _ in nodes_to_check] and (new_x, new_y) not in seen_positions:
                            if owner_map[new_x, new_y] != 1 and recycler_map[new_x, new_y] == 0 \
                                    and not(range_of_recycle_map[new_x, new_y] and scrap_amount_map[new_x, new_y] == 1):
                                output.append((new_x, new_y))
                                max_depth = depth

                            nodes_to_check.append((new_x, new_y, depth + 1))

        return output

    def give_target(self, x, y):
        return [f'MOVE {self.n} {self.y} {self.x} {y} {x}']


def get_spawn_score(i, j, opp_bots_objects, my_bots_objects, owner_map):  # todo faire spawn proche des adversaires
    score = 0

    if scrap_amount_map[i, j] == 1 and range_of_recycle_map[i, j] == 1:
        return -1

    for robot in opp_bots_objects:
        if distance(i, j, robot.x, robot.y) == 2:
            score += 1

    my_units = units_map[i, j]

    for d in directions.values():
        dx, dy = d
        new_x, new_y = i + dx, j + dy
        if 0 <= new_x < height and 0 <= new_y < width:
            if owner_map[new_x, new_y] == 0 and recycler_map[new_x, new_y] == 0:
                if units_map[new_x, new_y] >= 0:
                    my_units -= units_map[new_x, new_y]
                    if my_units <= 0:
                        score += 10
                    else:
                        score += 3
                else:
                    score += 3
            elif owner_map[new_x, new_y] == -1 and scrap_amount_map[new_x, new_y] > 1:
                score += 1

    return score


def is_sensitive(x, y):
    if recycler_map[x, y] == 1:
        return False
    if owner_map[x, y] != 1:
        return False
    for d in directions.values():
        dx, dy = d
        new_x, new_y = x + dx, y + dy
        if 0 <= new_x < height and 0 <= new_y < width:
            if scrap_amount_map[new_x, new_y] > 0 and owner_map[new_x, new_y] < 1 and recycler_map[new_x, new_y] == 0:
                if dist_to_opp_map[x, y] < dist_to_opp_map[new_x, new_y]:
                    return True
    return False


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
    sensitive_cells = []

    for i in range(height):
        for j in range(width):
            cell = Cell([int(k) for k in input().split()])
            cells.append(cell)

            # owner: 1 = me, 0 = foe, -1 = neutral
            scrap_amount_map[i, j] = cell.scrap_amount
            owner_map[i, j] = cell.owner
            recycler_map[i, j] = cell.recycler
            range_of_recycle_map[i, j] = cell.in_range_of_recycler
            if cell.in_range_of_recycler and cell.scrap_amount == 2:
                sensitive_cells.append((i, j))

            if cell.owner == 1 and cell.recycler == 1:
                range_of_my_recycle_map[i, j] = 1
                for d in directions.values():
                    dx, dy = d
                    new_x, new_y = i + dx, j + dy
                    if 0 <= new_x < height and 0 <= new_y < width:
                        range_of_my_recycle_map[new_x, new_y] = 1

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
    # update distance_map
    dist_to_opp_map = np.ones((height, width), dtype=int) * 100

    for bot in opp_bots_objects:
        seen_positions = []
        nodes_to_check = [(bot.x, bot.y, 0)]

        while len(nodes_to_check) > 0:
            x, y, depth = nodes_to_check.pop(0)
            dist_to_opp_map[x, y] = min(dist_to_opp_map[x, y], depth)
            seen_positions.append((x, y))

            for d in directions.values():
                dx, dy = d
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < height and 0 <= new_y < width:
                    if scrap_amount_map[new_x, new_y] > 0 and recycler_map[new_x, new_y] == 0:
                        if (new_x, new_y) not in [(e1, e2) for e1, e2, _ in nodes_to_check] and (new_x, new_y) not in seen_positions:
                            nodes_to_check.append((new_x, new_y, depth + 1))

    # Update Stable field
    if not STABLE_FIELD:
        STABLE_FIELD = True
        for i in range(height):
            if not STABLE_FIELD:
                break
            for j in range(width):
                if owner_map[i, j] == 1 and dist_to_opp_map[i, j] < 100:
                    STABLE_FIELD = False
                    break
    if STABLE_FIELD:
        debug_print("Stable field detected")

    for bot in my_bots_objects:
        if dist_to_opp_map[bot.x, bot.y] < 3:
            BUILD_MODE = False

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

        # ignore maps with too low scrap amount
        if scrap_amount_map[x, y] < 3:
            continue

        if not range_of_my_recycle_map[x, y]:
            possible_build_positions[i][-1] = scrap_amount_map[x, y]
        else:
            possible_build_positions[i][-1] = 0

        for d in directions.values():
            dx, dy = d
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < height and 0 <= new_y < width:
                if not range_of_my_recycle_map[new_x, new_y]:
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
    debug_print("possible build pos:", possible_build_positions)
    if (BUILD_MODE or n_recyclers < n_opp_recyclers) and not STABLE_FIELD and len(my_bots_objects) >= 4 and len(possible_build_positions) > 0:
        x, y, score = possible_build_positions.pop(-1)
        added_this_turn = [(x, y)]

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

            # remove possible positions near the last build
            new_possible_build_pos = []
            my_matter -= 10
            for i, j, score in possible_build_positions:
                if distance(x, y, i, j) > 2:
                    new_possible_build_pos.append((i, j, score))

            possible_build_positions = new_possible_build_pos

            if len(possible_build_positions) == 0:
                break
            x, y, score = possible_build_positions.pop(-1)

    # spawn
    # spawn on sensitive cells
    if len(sensitive_cells) > 0 and my_matter >= 10:
        for x, y in sensitive_cells:
            if is_sensitive(x, y):
                debug_print("spawn sensitive", y, x)
                actions.append(f"SPAWN 1 {y} {x}")
                my_matter -= 10

    if my_matter >= 10 and len(possible_spawn_positions) > 0:
        debug_print("possible spawn pos:", len(possible_spawn_positions), possible_spawn_positions)
        strategic_spawn_pos = [e for e in possible_spawn_positions if e[-1] > 10]

        if len(strategic_spawn_pos) > 0:
            debug_print("strategic spawn", len(strategic_spawn_pos))
            random_spawns = strategic_spawn_pos[- (my_matter // 10):]
        else:
            debug_print("random spawn")
            random_spawns = []
            my_matter_cpy = my_matter

            # spawn near opponent if I can
            if len(opp_bots_objects) > 0:
                possible_spawn_positions.sort(key=lambda x: dist_to_opp_map[x[0], x[1]], reverse=True)

            # random_spawns.append(possible_spawn_positions[-1])
            while my_matter_cpy >= 10 and len(possible_spawn_positions) > 0:
                random_spawns.append(possible_spawn_positions.pop(-1))
                my_matter_cpy -= 10

        for x, y, score in random_spawns:
            actions.append(f"SPAWN {my_matter // 10 // len(random_spawns)} {y} {x}")

    # print_field(scrap_amount_map)

    debug_print("actions:", actions)
    print(';'.join(actions) if len(actions) > 0 else 'WAIT')

# To debug: print("Debug messages...", file=sys.stderr, flush=True)

