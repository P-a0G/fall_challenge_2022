import random
import numpy as np


directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}


def distance(x, y, a, b):
    return abs(x - a) + abs(y - b)


class Robot:
    def __init__(self, x, y, n=1):
        self.x = x
        self.y = y
        self.n = n

    def get_next_move(self, scrap_amount_map, owner_map, opp_robot_pos):
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

    def get_next_actions(self, cells, my_matter, opp_matter):
        my_robots = []
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
                    nb_opp_bots += cell.units
                    opp_robots_pos.append((i, j))

            self.scrap_amount_map[cell.i, cell.j] = cell.scrap
            self.recycler_map[cell.i, cell.j] = cell.recycler
            self.owner_map[cell.i, cell.j] = cell.owner
            self.units_map[cell.i, cell.j] = cell.units

            if cell.can_build:
                possible_build_pos.append([cell.i, cell.j, 0])
            if cell.can_spawn:
                possible_spawn_pos.append((cell.i, cell.j))

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
                    if not (self.recycler_map[new_x, new_y] and self.owner_map[new_x, new_y] == 1) \
                            and self.scrap_amount_map[x, y] < self.scrap_amount_map[new_x, new_y]:
                        possible_build_pos[i][-1] += 1

        possible_build_pos.sort(key=lambda v: v[-1])

        actions = []

        # build
        x, y, score = possible_build_pos.pop(-1)
        while my_matter >= 10 and score >= 5:
            actions.append(f'BUILD {y} {x}')

            # remove recycler from possible position
            new_spawn_pos = []
            for i in range(len(possible_spawn_pos)):
                e1, e2 = possible_spawn_pos[i]
                if e1 == x and e2 == y:
                    continue
                else:
                    new_spawn_pos.append((e1, e2))
            possible_spawn_pos = new_spawn_pos

            my_matter -= 10
            if len(possible_build_pos) == 0:
                break
            x, y, score = possible_build_pos.pop(-1)

        # spawn
        for robot in my_robots:
            robot_action = robot.get_next_move(self.scrap_amount_map, self.owner_map, opp_robots_pos)
            if robot_action is not None:
                actions.append(robot_action)

        return actions

