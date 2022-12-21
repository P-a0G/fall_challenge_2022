import random
import numpy as np
from utils import debug_map

directions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}


class Cell:
    def __init__(self, scrap):
        self.scrap = scrap
        self.owner = 0
        self.units = 0
        self.recycler = 0
        self.in_range_of_recycler = 0

    def __str__(self):
        return f"Core cell [{self.scrap}, {self.owner}, {self.units}, {self.recycler}, {self.in_range_of_recycler}]"

    def recycle(self):
        if self.in_range_of_recycler:
            self.scrap -= 1
            if self.scrap == 0:
                self.owner = 0
                self.in_range_of_recycler = 0
                self.units = 0
                self.recycler = 0


def can_build():
    pass  # todo


def can_spawn():
    pass  # todo


class Player:
    def __init__(self, id):
        self.matter = 10
        self.id = id


class Core:
    def __init__(self):
        self.h = random.randint(6, 12)
        self.w = random.randint(12, 24)

        self.stable_field = 0
        self.scrap_map = np.zeros((self.h, self.w), dtype=int)
        self.last_scrap_map = self.scrap_map.copy()

        self.cells = self.init_cells()

        self.players = {1: Player(1), 2: Player(2)}

        self.recyclers_gain = {1: np.zeros(10, dtype=int), 2: np.zeros(10, dtype=int)}

        self.turn = 1

    def init_cells(self):
        cells = {}

        symmetric = random.randint(0, 1)

        if symmetric:
            # create cells
            for i in range(self.h):
                for j in range(self.w // 2 + 1):
                    scrap = random.randint(0, 10)
                    self.scrap_map[i, j] = scrap

                    cells[(i, j)] = Cell(scrap)
                    cells[(i, self.w - j - 1)] = Cell(scrap)
                    self.scrap_map[i, self.w - j - 1] = scrap
        else:
            # create cells
            for i in range(self.h // 2 + 1):
                for j in range(self.w):
                    scrap = random.randint(0, 10)
                    self.scrap_map[i, j] = scrap

                    cells[(i, j)] = Cell(scrap)

                    cells[(self.h - i - 1, self.w - j - 1)] = Cell(scrap)
                    self.scrap_map[self.h - i - 1, self.w - j - 1] = scrap

        # init robots
        init_breaker = 0
        while init_breaker < 10:
            init_breaker += 1
            i = random.randint(1, self.h // 3)
            j = random.randint(1, self.w // 3)

            if symmetric:
                if j + 1 >= self.w - j - 2:
                    continue
            else:
                if i + 1 >= self.h - i - 2 and j + 1 >= self.w - j - 2:
                    continue

            if cells[(i, j)].scrap > 0 and \
                    cells[(i + 1, j)].scrap > 0 and \
                    cells[(i - 1, j)].scrap > 0 and\
                    cells[(i, j + 1)].scrap > 0 and \
                    cells[(i, j - 1)].scrap > 0:

                for x, y in [(i+1, j), (i-1, j), (i, j+1), (i, j-1)]:
                    cells[(x, y)].owner = 1
                    cells[(x, y)].units = 1

                    if symmetric:
                        cells[(x, self.w - y - 1)].owner = 2
                        cells[(x, self.w - y - 1)].units = 1
                    else:
                        cells[(self.h - x - 1, self.w - y - 1)].owner = 2
                        cells[(self.h - x - 1, self.w - y - 1)].units = 1

                cells[(i, j)].owner = 1
                if symmetric:
                    cells[(i, self.w - j - 1)].owner = 2
                else:
                    cells[(self.h - i - 1, self.w - j - 1)].owner = 2

                break

        if init_breaker == 10:
            raise ValueError("failed to init robots")  # failed to init robots

        return cells

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

        for k in range(self.cells[(x, y)].scrap):
            self.recyclers_gain[player_id][k] += 1

        for d in directions.values():
            dx, dy = d
            new_x, new_y = x + dx, y + dy
            if 0 < new_x < self.h and 0 < new_y < self.w:
                if self.cells[(new_x, new_y)].scrap > 0:
                    self.cells[(new_x, new_y)].in_range_of_recycler = 1

                    for k in range(max(self.cells[(new_x, new_y)].scrap, self.cells[(x, y)].scrap)):
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

    def update_stable_field(self):
        if (self.scrap_map == self.last_scrap_map).all():
            self.stable_field += 1
        else:
            self.last_scrap_map = self.scrap_map.copy()
            self.stable_field = 0

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
        self.update_stable_field()
        done = self.stable_field >= 20 or self.turn >= 200

        # debug_map(self.cells, self.h, self.w)
        # assert False

        return self.cells, self.get_reward(), done, info