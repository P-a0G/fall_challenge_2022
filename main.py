import sys
import math
import numpy as np
import random

directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}
turn = 0


def distance(x, y, a, b):
    return abs(x - a) + abs(y - b)


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
    def __init__(self, args, i, j):
        self.scrap_amount, self.owner, self.units, self.recycler, self.can_build, self.can_spawn, self.in_range_of_recycler = args
        self.i = i
        self.j = j

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

    def __str__(self):
        return f'Robot: x={self.x} y={self.y} n={self.n}'

    def get_next_move(self, opp_robot_pos):
        dist_min = 50
        i_min, j_min = -1, -1
        for i, j in opp_robot_pos:
            dist0 = distance(self.x, self.y, i, j)
            if dist0 == 1:
                continue
            if dist0 == 2:
                return f'MOVE {self.n} {self.y} {self.x} {j} {i}'
            if dist0 < dist_min:
                dist_min = dist0
                i_min, j_min = i, j

        if dist_min == 50:
            return None

        return f'MOVE {self.n} {self.y} {self.x} {j_min} {i_min}'

    def get_next_move2(self, scrap_amount_map, owner_map):
        possibilities = []
        better_possibilites = []

        for d in directions.values():
            dx, dy = d
            new_x, new_y = self.x + dx, self.y + dy
            if 0 <= new_x < height and 0 <= new_y < width:
                if scrap_amount_map[new_x, new_y] > 0:
                    possibilities.append((new_x, new_y))
                    if owner_map[new_x, new_y] < 1:
                        better_possibilites.append((new_x, new_y))

        if len(possibilities) == 0:
            return None

        if len(better_possibilites) > 0:
            moves = random.sample(better_possibilites, min(self.n, len(better_possibilites)))  # todo move robots separately
        else:
            moves = [(height // 2, width // 2)]

        output = []
        for x, y in moves:
            output.append(f'MOVE {1} {self.y} {self.x} {y} {x}')
            if owner_map[x, y] == -1:
                owner_map[x, y] = 1
        return output

    def give_target(self, x, y):
        return f'MOVE {self.n} {self.y} {self.x} {y} {x}'


class AggressivBot:
    def __init__(self, h, w):
        self.height = h
        self.width = w

        self.scrap_amount_map = np.zeros((h, w), dtype=int)
        self.recycler_map = np.zeros((h, w), dtype=int)
        self.owner_map = np.zeros((h, w), dtype=int)
        self.units_map = np.zeros((h, w), dtype=int)
        self.range_of_recycler = np.zeros((h, w), dtype=int)

        self.turn_strat1 = 6

    def get_spawn_score(self, i, j, opp_bots_objects, my_bots_objects, owner_map):
        score = 0

        for robot in opp_bots_objects:
            if distance(i, j, robot.x, robot.y) <= 2:
                score += 1

        for d in directions.values():
            dx, dy = d
            new_x, new_y = i + dx, j + dy
            if 0 <= new_x < self.height and 0 <= new_y < self.width:
                if owner_map[new_x, new_y] == 0:
                    score += 10
                elif owner_map[new_x, new_y] == -1 and self.scrap_amount_map[new_x, new_y] > 0:
                    score += 10

        return score

    def get_next_actions(self, cells, my_matter, opp_matter, turn):
        my_robots = []
        opp_robots = []
        opp_robots_pos = []
        nb_my_bots = 0
        nb_opp_bots = 0

        possible_build_pos = []
        possible_spawn_pos = []

        for cell in cells:
            if cell.units > 0:
                if cell.owner == 1:
                    my_robots.append(Robot(cell.i, cell.j, cell.units))
                    nb_my_bots += cell.units
                else:
                    opp_robots.append(Robot(cell.i, cell.j, cell.units))
                    nb_opp_bots += cell.units
                    opp_robots_pos.append((cell.i, cell.j))

            self.scrap_amount_map[cell.i, cell.j] = cell.scrap_amount
            self.recycler_map[cell.i, cell.j] = cell.recycler
            self.owner_map[cell.i, cell.j] = cell.owner
            self.units_map[cell.i, cell.j] = cell.units

            if cell.owner == 1 and cell.recycler > 0:
                self.range_of_recycler[cell.i, cell.j] = 1
                for d in directions.values():
                    dx, dy = d
                    new_x, new_y = cell.i + dx, cell.j + dy
                    if 0 <= new_x < self.height and 0 <= new_y < self.width:
                        self.range_of_recycler[new_x, new_y] = 1

            if cell.can_build:
                possible_build_pos.append([cell.i, cell.j, 0])
            if cell.can_spawn:
                possible_spawn_pos.append([cell.i, cell.j, 0])

        # print_field(self.scrap_amount_map)
        for robot in my_robots:
            debug_print(robot)

        # get actions

        # build recyclers
        for i in range(len(possible_build_pos)):
            x, y, _ = possible_build_pos[i]
            if self.scrap_amount_map[x, y] < 3:
                continue

            for d in directions.values():
                dx, dy = d
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < self.height and 0 <= new_y < self.width:
                    if not self.range_of_recycler[new_x, new_y]\
                            and self.scrap_amount_map[x, y] < self.scrap_amount_map[new_x, new_y]:
                        possible_build_pos[i][-1] += 1

        possible_build_pos.sort(key=lambda v: v[-1])

        actions = []

        # build
        if len(possible_build_pos) > 0:
            x, y, score = possible_build_pos.pop(-1)
            if turn <= self.turn_strat1:
                min_score = 3
            else:
                min_score = 5
            while my_matter >= 10 and score >= min_score:
                actions.append(f'BUILD {y} {x}')

                # remove recycler from possible position
                new_spawn_pos = []
                for i in range(len(possible_spawn_pos)):
                    e1, e2, e3 = possible_spawn_pos[i]
                    if e1 == x and e2 == y:
                        continue
                    else:
                        new_spawn_pos.append((e1, e2, e3))
                possible_spawn_pos = new_spawn_pos

                my_matter -= 10
                if len(possible_build_pos) == 0:
                    break
                x, y, score = possible_build_pos.pop(-1)

        # spawn
        if turn <= self.turn_strat1:
            best_spawn_pos = None
            best_score = 1000
            for x, y, _ in possible_spawn_pos:
                score = 0
                for i, j in opp_robots_pos:
                    score += distance(i, j, x, y)

                if score < best_score:
                    best_spawn_pos = (x, y)
                    best_score = score

            if best_spawn_pos is not None:
                x, y = best_spawn_pos
                actions.append(f"SPAWN {my_matter // 10} {y} {x}")
        else:
            # compute spawn score
            for i in range(len(possible_spawn_pos)):
                x, y, _ = possible_spawn_pos[i]
                score = self.get_spawn_score(x, y, opp_robots, my_robots, self.owner_map)
                possible_spawn_pos[i][-1] = score

            if my_matter >= 10 and len(possible_spawn_pos) > 0:
                strategic_spawn_pos = [e for e in possible_spawn_pos if e[-1] > 10]

                if len(strategic_spawn_pos) > 0:
                    debug_print("strategic spawn", len(strategic_spawn_pos))
                    random_spawns = random.sample(strategic_spawn_pos, min(my_matter // 10, len(strategic_spawn_pos)))
                else:
                    debug_print("random spawn")
                    random_spawns = [possible_spawn_pos[0]]

                for x, y, score in random_spawns:
                    actions.append(f"SPAWN {my_matter // 10 // len(random_spawns)} {y} {x}")

        # move robots
        for robot in my_robots:
            if turn <= self.turn_strat1:
                robot_action = robot.get_next_move(opp_robots_pos)
                if robot_action is not None:
                    actions.append(robot_action)
            else:
                nxt_move = robot.get_next_move2(self.scrap_amount_map, self.owner_map)
                if nxt_move is not None:
                    actions += nxt_move

        return actions


my_bot = AggressivBot(height, width)

# game loop
while True:
    my_matter, opp_matter = [int(i) for i in input().split()]
    debug_print("my matter:", my_matter, "opp matter:", opp_matter)
    turn += 1

    cells = []
    for i in range(height):
        for j in range(width):
            cell = Cell([int(k) for k in input().split()], i=i, j=j)
            cells.append(cell)

    actions = my_bot.get_next_actions(cells, my_matter, opp_matter, turn)

    print(';'.join(actions) if len(actions) > 0 else 'WAIT')

# To debug: print("Debug messages...", file=sys.stderr, flush=True)

