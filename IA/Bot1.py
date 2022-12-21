import sys
import math
import numpy as np
import random

directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}
BUILD_SCORE_THRESHOLD = 1


class Bot1:
    def __init__(self, h, w):
        self.height = h
        self.width = w

        self.scrap_amount_map = np.zeros((self.height, self.width), dtype=int)
        self.owner_map = np.zeros((self.height, self.width), dtype=int)
        self.units_map = np.zeros((self.height, self.width), dtype=int)
        self.recycler_map = np.zeros((self.height, self.width), dtype=int)

        self.my_bots = np.zeros((self.height, self.width), dtype=int)
        self.opp_bots = np.zeros((self.height, self.width), dtype=int)
        self.turn = 0

    def get_spawn_score(self, x, y, opp_bots_objects, my_bots_objects, owner_map):
        score = 0

        for robot in opp_bots_objects:
            if distance(x, y, robot.x, robot.y) <= 2:
                score += 1

        for d in directions.values():
            dx, dy = d
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < self.height and 0 <= new_y < self.width:
                if self.owner_map[new_x, new_y] == 0:
                    score += 10
                elif self.owner_map[new_x, new_y] == -1 and self.scrap_amount_map[new_x, new_y] > 0:
                    score += 10

        return score

    def get_move(self, my_matter, opp_matter, cells_param):
        self.turn += 1

        cells = []
        my_bots_objects = []
        opp_bots_objects = []
        possible_spawn_positions = []
        possible_build_positions = []
        n_recyclers = 0
        n_opp_recyclers = 0

        for i in range(self.height):
            for j in range(self.width):
                cell = Cell(cells_param[i][j])
                cells.append(cell)

                # owner: 1 = me, 0 = foe, -1 = neutral
                self.scrap_amount_map[i, j] = cell.scrap_amount
                self.owner_map[i, j] = cell.owner
                self.recycler_map[i, j] = cell.recycler
                self.units_map[i, j] = cell.units

                if cell.recycler:
                    if cell.owner == 1:
                        n_recyclers += 1
                    else:
                        n_opp_recyclers += 1

                if cell.units:
                    if cell.owner == 1:
                        self.my_bots[i, j] = cell.units
                        my_bots_objects.append(Robot(i, j, cell.units))
                    else:
                        self.opp_bots[i, j] = cell.units
                        opp_bots_objects.append(Robot(i, j, cell.units))

                if cell.can_build:
                    possible_build_positions.append([i, j, 0])

                if cell.can_spawn and not cell.units:
                    possible_spawn_positions.append([i, j, 0])

        # compute build scores
        for i in range(len(possible_build_positions)):
            x, y, _ = possible_build_positions[i]

            for d in directions.values():
                dx, dy = d
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < self.height and 0 <= new_y < self.width:
                    owner = self.owner_map[new_x, new_y]
                    if owner == 1:
                        possible_build_positions[i][-1] -= self.units_map[new_x, new_y]
                    elif owner == 0:
                        possible_build_positions[i][-1] += self.units_map[new_x, new_y]

        # compute spawn score
        for i in range(len(possible_spawn_positions)):
            x, y, _ = possible_spawn_positions[i]
            score = self.get_spawn_score(x, y, opp_bots_objects, my_bots_objects, self.owner_map)
            possible_spawn_positions[i][-1] = score

        possible_build_positions.sort(key=lambda x: x[-1])
        possible_spawn_positions.sort(key=lambda x: x[-1])

        actions = []

        for robot in my_bots_objects:
            moves = robot.get_next_move(self.scrap_amount_map, self.owner_map, self.height, self.width)
            if moves is not None:
                actions += moves

        # farm
        if self.turn <= 15 and len(my_bots_objects) >= 4 and len(possible_build_positions) > 0:
            x, y, score = possible_build_positions.pop(-1)
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
            strategic_spawn_pos = [e for e in possible_spawn_positions if e[-1] > 10]

            if len(strategic_spawn_pos) > 0:
                random_spawns = random.sample(strategic_spawn_pos, min(my_matter // 10, len(strategic_spawn_pos)))
            else:
                random_spawns = [possible_spawn_positions[0]]

            for x, y, score in random_spawns:
                actions.append(f"SPAWN {my_matter // 10 // len(random_spawns)} {y} {x}")

        return ';'.join(actions) if len(actions) > 0 else 'WAIT'


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

    def get_next_move(self, scrap_amount_map, owner_map, height, width):
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


def distance(x, y, a, b):
    return abs(x - a) + abs(y - b)




