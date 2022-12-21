from Game_core import Core
from IA.Bot1 import Bot1
import time
import numpy as np
from tqdm import tqdm
from utils import debug_map
# test


class Simulator:
    def __init__(self):
        self.game = Core()

        self.player_1 = Bot1(self.game.h, self.game.w)
        self.player_2 = Bot1(self.game.h, self.game.w)

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

    def play_a_game(self):
        cells = self.game.cells
        init_score = self.game.get_reward()

        if init_score != 0:
            for k in cells:
                cell = cells[k]
                if cell.owner != 0:
                    print(k, cell.owner)
            print("init score was:", init_score)
            assert False  # wrong init

        turn = 0

        # game_start = time.time()
        while True:
            turn += 1
            time_start = time.time()
            cells_param = []

            for i in range(self.game.h):
                line = []
                for j in range(self.game.w):
                    cell = self.game.cells[(i, j)]
                    line.append((
                        cell.scrap,
                        self.convert_owner(1, cell.owner),
                        cell.units,
                        cell.recycler,
                        cell.owner == 1 and not cell.recycler,  # can build
                        cell.owner == 1 and not cell.recycler,  # can spawn
                        cell.in_range_of_recycler))
                cells_param.append(line)

            player_1_moves = self.player_1.get_move(
                self.game.players[1].matter,
                self.game.players[2].matter,
                cells_param
            )
            if time.time() - time_start > 0.006:
                print("Player 1 timeout")
                score = -100
                break

            cells_param_p2 = []

            for i in range(self.game.h):
                line = []
                for j in range(self.game.w):
                    cell = self.game.cells[(i, j)]
                    line.append((
                        cell.scrap,
                        self.convert_owner(2, cell.owner),
                        cell.units,
                        cell.recycler,
                        cell.owner == 2 and not cell.recycler,  # can build
                        cell.owner == 2 and not cell.recycler,  # can spawn
                        cell.in_range_of_recycler))
                cells_param_p2.append(line)

            time_start = time.time()
            player_2_moves = self.player_2.get_move(
                self.game.players[2].matter,
                self.game.players[1].matter,
                cells_param_p2
            )
            if time.time() - time_start > 0.006:
                print("Player 2 timeout")
                score = -100
                break

            cells, score, done, info = self.game.play(player_1_moves, player_2_moves)

            # print(f"Turn {turn}: Score = {score}")

            if done:
                # print("\tEnd of the Game, score=", score)
                break

            assert turn <= 200
            # print("turn:", turn)
            # debug_map(self.game.cells, self.game.h, self.game.w)

        # debug_map(self.game.cells, self.game.h, self.game.w)
        # print("score:", score)

        return score


if __name__ == '__main__':
    n_games = 1000

    start = time.time()
    played_games = 0

    avr_score = 0
    for k in tqdm(range(n_games)):
        score = 0
        duration = 0
        try:
            simulator = Simulator()
            score = simulator.play_a_game()
        except ValueError as e:
            # print(f"\t\t error game {k}:", e)
            continue

        avr_score += score
        played_games += 1

    print("End of simulation:", time.time() - start, "s")
    print("Played games =", played_games)
    print("Average score =", avr_score / n_games)


