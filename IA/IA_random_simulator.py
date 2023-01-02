import sys
import math
import time
import numpy as np
import random

directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}


DEPTH = 10


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


class Bot1:
    def __init__(self, h, w):
        self.BUILD_SCORE_THRESHOLD = 1

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
            while my_matter >= 10 and score >= self.BUILD_SCORE_THRESHOLD:
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
        self.save_scrap = None
        self.save_owner = None
        self.save_units = None
        self.save_recycler = None
        self.save_can_build = None
        self.save_can_spawn = None
        self.save_in_range_of_recycler = None

    def __str__(self):
        return f'Element:   scrap amount:   {self.scrap_amount}\n' \
               f'           owner:          {self.owner}\n' \
               f'           units:          {self.units}\n' \
               f'           recycler:       {self.recycler}\n' \
               f'           can_build:      {self.can_build}\n' \
               f'           can_spawn:      {self.can_spawn}\n' \
               f'           in range of rec:{self.in_range_of_recycler}'

    def recycle(self):
        if self.in_range_of_recycler:
            self.scrap_amount -= 1
            if self.scrap_amount == 0:
                self.owner = 0
                self.in_range_of_recycler = 0
                self.units = 0
                self.recycler = 0

    def save(self):
        self.save_scrap = self.scrap_amount
        self.save_owner = self.owner
        self.save_units = self.units
        self.save_recycler = self.recycler
        self.save_can_build = self.can_build
        self.save_can_spawn = self.can_spawn
        self.save_in_range_of_recycler = self.in_range_of_recycler

    def load(self):
        self.scrap_amount = self.save_scrap
        self.owner = self.save_owner
        self.units = self.save_units
        self.recycler = self.save_recycler
        self.can_build = self.save_can_build
        self.can_spawn = self.save_can_spawn
        self.in_range_of_recycler = self.save_in_range_of_recycler


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


class Player:
    def __init__(self, id):
        self.matter = 10
        self.id = id


class Core:
    def __init__(self, h, w):
        self.h = h
        self.w = w

        # self.stable_field = 0
        self.scrap_map = np.zeros((self.h, self.w), dtype=int)
        self.last_scrap_map = self.scrap_map.copy()

        self.cells = {}

        self.players = {1: Player(1), 2: Player(2)}
        self.player2 = Bot1(h, w)

        self.recyclers_gain = {1: np.zeros(10, dtype=int), 2: np.zeros(10, dtype=int)}

        self.turn = 1

    # actions
    def move(self, player_id, amount, from_y, from_x, to_y, to_x):
        if player_id != self.cells[(from_x, from_y)].owner or self.cells[(from_x, from_y)].units < amount:
            return

        if abs(from_x - to_x) + abs(from_y - to_y) != 1:  # wrong move
            return

        self.cells[(from_x, from_y)].units -= amount

        if self.cells[(to_x, to_y)].owner == player_id:
            self.cells[(to_x, to_y)].units += amount
        elif self.cells[(to_x, to_y)].owner == 0:
            self.cells[(to_x, to_y)].units += amount
            self.cells[(to_x, to_y)].owner = player_id
        else:
            self.cells[(to_x, to_y)].units -= amount
            if self.cells[(to_x, to_y)].units < 0:
                self.cells[(to_x, to_y)].units = -self.cells[(to_x, to_y)].units
                self.cells[(to_x, to_y)].owner = player_id

    def build(self, player_id, y, x):
        if player_id != self.cells[(x, y)].owner or self.cells[(x, y)].recycler > 0:
            return

        if self.players[player_id].matter < 10:
            return

        self.players[player_id].matter -= 10
        self.cells[(x, y)].recycler = 1
        self.cells[(x, y)].in_range_of_recycler = 1

        for k in range(self.cells[(x, y)].scrap_amount):
            self.recyclers_gain[player_id][k] += 1

        for d in directions.values():
            dx, dy = d
            new_x, new_y = x + dx, y + dy
            if 0 < new_x < self.h and 0 < new_y < self.w:
                if self.cells[(new_x, new_y)].scrap_amount > 0:
                    self.cells[(new_x, new_y)].in_range_of_recycler = 1

                    for k in range(max(self.cells[(new_x, new_y)].scrap_amount, self.cells[(x, y)].scrap_amount)):
                        self.recyclers_gain[player_id][k] += 1

    def spawn(self, player_id, amount, y, x):
        if player_id != self.cells[(x, y)].owner:
            return

        if self.players[player_id].matter < 10 * amount:
            return

        self.cells[(x, y)].units += amount
        self.players[player_id].matter -= amount * 10

    def wait(self, player):
        return

    def recycle(self):
        for cell in self.cells.values():
            cell.recycle()

    @staticmethod
    def message(player, text):
        print("\t\tplayer", player, ":", text)

    def get_reward(self):
        reward = 0
        for cell in self.cells.values():
            if cell.owner == 1:
                reward += 1
            elif cell.owner == 2:
                reward -= 1
        return reward

    # def update_stable_field(self):
    #     if (self.scrap_map == self.last_scrap_map).all():
    #         self.stable_field += 1
    #     else:
    #         self.last_scrap_map = self.scrap_map.copy()
    #         self.stable_field = 0

    def get_recycle_gain(self):
        player_1_gain = self.recyclers_gain[1][0]
        player_2_gain = self.recyclers_gain[2][0]

        for k in range(9):
            self.recyclers_gain[1][k] = self.recyclers_gain[1][k + 1]
            self.recyclers_gain[2][k] = self.recyclers_gain[1][k + 1]

        self.recyclers_gain[1][2] = 0
        self.recyclers_gain[2][2] = 0

        return player_1_gain, player_2_gain

    def play(self, actions_player_1, actions_player_2):
        # debug_map(self.cells, self.h, self.w)
        info = "info"

        actions_player_1 = [action.split(" ") for action in actions_player_1.split(";")]
        actions_player_2 = [action.split(" ") for action in actions_player_2.split(";")]

        # Les actions BUILD sont complétées.
        for action in actions_player_1:
            if action[0] == "BUILD":
                self.build(1, int(action[1]), int(action[2]))

        for action in actions_player_2:
            if action[0] == "BUILD":
                self.build(2, int(action[1]), int(action[2]))

        # Les actions MOVE et SPAWN sont simultanément complétées. Un robot ne peut faire ces deux actions en un tour
        # Les unités des équipes opposées sur une case sont retirées un pour un.
        # Les robots restants marqueront les cases sur lesquelles elles se trouvent, changeant le owner de la case.
        for action in actions_player_1:
            if action[0] == "SPAWN":
                self.spawn(1, int(action[1]), int(action[2]), int(action[3]))

        for action in actions_player_2:
            if action[0] == "SPAWN":
                self.spawn(2, int(action[1]), int(action[2]), int(action[3]))

        for action in actions_player_1:
            if action[0] == "MOVE":
                self.move(1, int(action[1]), int(action[2]), int(action[3]), int(action[4]), int(action[5]))

        for action in actions_player_2:
            if action[0] == "MOVE":
                self.move(2, int(action[1]), int(action[2]), int(action[3]), int(action[4]), int(action[5]))

        # Les recycleurs recyclent la case sur lesquelles elles se trouvent et les 4 cases adjacentes tant qu'elles ne sont pas déjà de l'herbe
        # Les tuiles avec un scrapAmount à 0 sont maintenant de l'herbe. Les recycleurs ou les robots sur cette case sont retirés.
        self.recycle()

        # Les joueurs reçoivent de base 10 matériaux ainsi que ceux acquis lors du recyclage.
        player_1_gain, player_2_gain = self.get_recycle_gain()

        self.players[1].matter += 10 + player_1_gain
        self.players[2].matter += 10 + player_2_gain

        self.turn += 1
        # self.update_stable_field()
        # done = self.stable_field >= 20 or self.turn >= 200
        done = False

        # debug_map(self.cells, self.h, self.w)
        # assert False

        return self.cells, self.get_reward(), done, info

    def update(self, my_matter, opp_matter, cells, turn):
        self.players[1].matter = my_matter
        self.players[2].matter = opp_matter

        self.cells = cells

        self.turn = turn

        self.update_recyclers_gain()

    def update_recyclers_gain(self):
        pass  # todo

    @staticmethod
    def convert_owner(player_id, owner):
        if player_id == 1:
            if owner == 1:
                return 1
            elif owner == 0:
                return -1
            return 0

        if owner == 2:
            return 1
        elif owner == 0:
            return -1
        return 0

    def get_cells_params(self, player):
        cells_param = []

        for i in range(self.h):
            line = []
            for j in range(self.w):
                cell = self.cells[(i, j)]
                line.append((
                    cell.scrap_amount,
                    self.convert_owner(player, cell.owner),
                    cell.units,
                    cell.recycler,
                    cell.owner == player and not cell.recycler and cell.units == 0,  # can build
                    cell.owner == player and not cell.recycler,  # can spawn
                    cell.in_range_of_recycler))
            cells_param.append(line)
        return cells_param

    def get_build_pos(self, my_matter):
        actions = []
        load_possible_build = False
        possible_build_pos = []

        while my_matter >= 10:
            if random.random() < 0.9:
                return actions, my_matter

            if not load_possible_build:
                load_possible_build = True
                for k in self.cells:
                    cell = self.cells[k]
                    # can build
                    if cell.owner == 1 and cell.scrap_amount > 0 and cell.recycler == 0 and cell.units == 0:
                        possible_build_pos.append(f"BUILD {k[1]} {k[0]}")

            if len(possible_build_pos) == 0:
                return actions, my_matter  # no build possible

            # random selected action
            actions.append(random.choice(possible_build_pos))
            possible_build_pos.remove(actions[-1])
            my_matter -= 10

        return actions, my_matter

    def get_random_bot_spawn(self, my_matter):
        actions = []
        possible_spawn_pos = []
        for k in self.cells:
            cell = self.cells[k]
            if cell.owner == 1 and cell.recycler == 0:
                # spawn only near field I don't own
                for d in directions.values():
                    dx, dy = d
                    new_x, new_y = k[0] + dx, k[1] + dy
                    if 0 < new_x < self.h and 0 < new_y < self.w \
                            and self.cells[(new_x, new_y)].owner != 1 and self.cells[(new_x, new_y)].scrap_amount > 0:
                        possible_spawn_pos.append(k)
                        break

        while len(possible_spawn_pos) > 0 and my_matter >= 10:
            x, y = possible_spawn_pos.pop(random.randint(0, len(possible_spawn_pos) - 1))
            n = random.randint(1, my_matter//10)
            my_matter -= 10 * n
            actions.append(f"SPAWN {n} {y} {x}")

        return actions

    def get_random_bot_moves(self):
        actions = []
        for k in self.cells:
            cell = self.cells[k]

            n = cell.units
            if n > 0 and cell.owner == 1:
                possible_dir = []
                for d in directions.values():
                    dx, dy = d
                    new_x, new_y = k[0] + dx, k[1] + dy
                    if 0 < new_x < self.h and 0 < new_y < self.w:
                        possible_dir.append((new_x, new_y))

                # todo move des robots d'une même place à des endroits différents?
                if random.random() < 0.9:
                    x, y = random.choice(possible_dir)
                    actions.append(f"MOVE {n} {k[1]} {k[0]} {y} {x}")
                else:
                    x, y = random.choice(possible_dir)
                    actions.append(f"MOVE {random.randint(0, n)} {k[1]} {k[0]} {y} {x}")
        return actions

    def get_my_random_action(self, my_matter):
        outputs = []

        # get build pos
        build_pos, my_matter = self.get_build_pos(my_matter)
        outputs += build_pos

        # random spawn of robots (on maps near a map I don't own)
        outputs += self.get_random_bot_spawn(my_matter)

        # random move for each robot
        outputs += self.get_random_bot_moves()

        return ";".join(outputs) if len(outputs) > 0 else "WAIT"

    def generate_best_move(self):
        best_move = "WAIT"
        best_score = -1e9
        start = time.time()

        nb_simu = 0

        for k in self.cells:
            self.cells[k].save()
        matter_player_1_save = self.players[1].matter
        matter_player_2_save = self.players[2].matter

        recycler_gain_save = self.recyclers_gain.copy()

        while time.time() - start < 0.045:
            nb_simu += 1

            ''' reset game state '''
            # reset cells
            for k in self.cells:
                self.cells[k].load()
            # reset my matter
            self.players[1].matter = matter_player_1_save
            self.players[2].matter = matter_player_2_save
            # reset recycler gain
            self.recyclers_gain = recycler_gain_save

            my_action = self.get_my_random_action(
                self.players[1].matter
            )
            opp_action = self.player2.get_move(
                self.players[2].matter,
                self.players[1].matter,
                self.get_cells_params(player=2)
            )

            cells, score, done, info = self.play(my_action, opp_action)

            for i in range(DEPTH - 1):
                action1 = self.get_my_random_action(
                    self.players[1].matter
                )
                action2 = self.player2.get_move(
                    self.players[2].matter,
                    self.players[1].matter,
                    self.get_cells_params(player=2)
                )

                _, score, _, _ = self.play(action1, action2)

            if score > best_score:
                best_move = my_action
                best_score = score

        debug_print("nb simu =", nb_simu, "-> score:", best_score)
        debug_print("best move:", best_move)
        return best_move


width, height = [int(i) for i in input().split()]
turn = 0
core = Core(height, width)


# game loop
while True:
    my_matter, opp_matter = [int(i) for i in input().split()]
    debug_print("my matter:", my_matter, "opp matter:", opp_matter)
    turn += 1

    cells = {}

    for i in range(height):
        for j in range(width):
            cell = Cell([int(k) for k in input().split()])
            cells[i, j] = cell

    core.update(my_matter, opp_matter, cells, turn)

    actions = core.generate_best_move()

    print(actions)
    # print(';'.join(actions) if len(actions) > 0 else 'WAIT')


# To debug: print("Debug messages...", file=sys.stderr, flush=True)

