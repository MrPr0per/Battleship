import random
import time

import numpy as np

from base_elements import OpponentCell, ShootStatus
from gameplay import Player
from settings import *

# Это нужно, чтобы не возникало цикцических импортов, но среда подсказывала методы Game
if False: from gui import Game


class AI:
    pass


class RandomAI(AI, Player):
    def __init__(self, w, h, ships_count, time_for_game):
        super().__init__(w, h, ships_count, time_for_game)
        self.not_cllicked_crds = None
        self.cooldown = AI_HIT_COOLDOWN  # [s]
        # self.cooldown = 0.1 # [s]
        self.end_step_time = None

    def set_opponent(self, other_player: 'Player'):
        self.opponent = other_player
        self.other_field = np.full(self.opponent.my_field.shape, OpponentCell.unknown)
        self.user_marks = np.full(self.opponent.my_field.shape, False, dtype=bool)
        w, h = self.opponent.my_field.shape
        self.not_cllicked_crds = [(x, y) for x in range(w) for y in range(h)]

    def make_step(self, game: 'Game'):
        # if self.end_step_time is not None and time.time() - self.end_step_time < self.cooldown: return 
        cell_crd = random.choice(self.not_cllicked_crds)
        self.not_cllicked_crds.remove(cell_crd)

        game.shoot(*cell_crd)

        self.end_step_time = time.time()

        return cell_crd

    def is_ready(self):
        if self.end_step_time is None: self.end_step_time = time.time()
        return time.time() - self.end_step_time > self.cooldown


class SmartAI(AI, Player):
    def __init__(self, w, h, ships_count, time_for_game):
        super().__init__(w, h, ships_count, time_for_game)
        self.not_cllicked_crds = None
        # self.cooldown = 0.7  # [s]
        # self.cooldown = 0.1 # [s]
        self.end_step_time = None

        self.first_hit_crd = None
        self.second_hit_crd = None
        self.ship_crds = []
        self.next_cells_to_shoot = []

        # self.in_process_of_killing = False
        # self.hit_crd = None
        # self.current_ship_dir = None
        # self.cells_to_determine_dir = []

    def set_opponent(self, other_player: 'Player'):
        self.opponent = other_player
        self.other_field = np.full(self.opponent.my_field.shape, OpponentCell.unknown)
        self.user_marks = np.full(self.opponent.my_field.shape, False, dtype=bool)
        w, h = self.opponent.my_field.shape
        self.not_cllicked_crds = [(x, y) for x in range(w) for y in range(h)]

    def make_step(self, game: 'Game') -> tuple[int, int]:
        # if self.end_step_time is not None and time.time() - self.end_step_time < self.cooldown: return

        # стратегия при попадании:
        # - находим соседнюю с попаданием клетку корабля
        # - продолжаем стрелять в том же направлении, пока не промажем или не убьем корабль
        #   - если промазали - стреляем так же по прямой в противоположном направлении до убийства
        # - теперь, когда имеем 2 крайние точки корабля - убираем соседние с ним клетки из очереди на обстрел

        self.end_step_time = time.time()

        if self.first_hit_crd is None:
            shoot_crd = random.choice(self.not_cllicked_crds)
            result = self.shoot(shoot_crd, game)

            if result.is_success():
                self.ship_crds.append(shoot_crd)

            if result == ShootStatus.miss:
                pass
            elif result == ShootStatus.hit:
                self.after_first_hit(shoot_crd)
            elif result in (ShootStatus.kill, ShootStatus.total_annihilation):
                self.after_kill()
            else:
                raise NotImplemented()

        elif self.first_hit_crd is not None and self.second_hit_crd is None:
            shoot_crd = random.choice(self.next_cells_to_shoot)
            result = self.shoot(shoot_crd, game)

            if result.is_success():
                self.ship_crds.append(shoot_crd)

            if result == ShootStatus.miss:
                pass
            elif result == ShootStatus.hit:
                self.after_second_hit(shoot_crd)
            elif result in (ShootStatus.kill, ShootStatus.total_annihilation):
                self.after_kill()
            else:
                raise NotImplemented()

        elif self.first_hit_crd is not None and self.second_hit_crd is not None:
            shoot_crd = random.choice(self.next_cells_to_shoot)
            result = self.shoot(shoot_crd, game)

            if result.is_success():
                self.ship_crds.append(shoot_crd)

            if result == ShootStatus.miss:
                self.after_miss_after_2_hit(shoot_crd)
            elif result == ShootStatus.hit:
                self.after_n_plus_3th_hit(shoot_crd)
            elif result in (ShootStatus.kill, ShootStatus.total_annihilation):
                self.after_kill()
            else:
                raise NotImplemented()

        else:
            raise Exception('невозможная ситуация')

        return shoot_crd

    def after_first_hit(self, shoot_crd):
        self.first_hit_crd = shoot_crd
        # проверяем соседние по кругу клетки
        for dx, dy in (-1, 0), (0, 1), (1, 0), (0, -1):
            cell_to_check = (shoot_crd[0] + dx, shoot_crd[1] + dy)
            if cell_to_check in self.not_cllicked_crds:
                self.next_cells_to_shoot.append(cell_to_check)

    def after_second_hit(self, shoot_crd):
        self.second_hit_crd = shoot_crd
        self.next_cells_to_shoot.clear()
        dx = self.second_hit_crd[0] - self.first_hit_crd[0]
        dy = self.second_hit_crd[1] - self.first_hit_crd[1]
        next_cell_to_shoot1 = (self.first_hit_crd[0] - dx, self.first_hit_crd[1] - dy)
        if next_cell_to_shoot1 in self.not_cllicked_crds:
            self.next_cells_to_shoot.append(next_cell_to_shoot1)
        next_cell_to_shoot2 = (self.second_hit_crd[0] + dx, self.second_hit_crd[1] + dy)
        if next_cell_to_shoot2 in self.not_cllicked_crds:
            self.next_cells_to_shoot.append(next_cell_to_shoot2)

    def after_n_plus_3th_hit(self, shoot_crd):
        dx = sign(shoot_crd[0] - self.first_hit_crd[0])
        dy = sign(shoot_crd[1] - self.first_hit_crd[1])
        # нормированный вектор от последнего попадания к первому

        next_cell_to_shoot = (shoot_crd[0] + dx, shoot_crd[1] + dy)
        if next_cell_to_shoot in self.not_cllicked_crds:
            self.next_cells_to_shoot.append(next_cell_to_shoot)

    def after_miss_after_2_hit(self, shoot_crd):
        dx = sign(shoot_crd[0] - self.first_hit_crd[0])
        dy = sign(shoot_crd[1] - self.first_hit_crd[1])
        # нормированный вектор от последнего попадания к первому
        self.edge_point = (shoot_crd[0] - dx, shoot_crd[1] - dy)

    def after_kill(self):
        x1 = min((x for x, y in self.ship_crds))
        y1 = min((y for x, y in self.ship_crds))
        x2 = max((x for x, y in self.ship_crds))
        y2 = max((y for x, y in self.ship_crds))
        w, h = self.other_field.shape

        for x in range(x1 - 1, x2 + 2):
            for y in range(y1 - 1, y2 + 2):
                if not (x1 <= x <= x2 and y1 <= y <= y2) and 0 <= x < w and 0 <= y < h:
                    self.mark_shoot(x, y, False)
                if (x, y) in self.not_cllicked_crds:
                    self.not_cllicked_crds.remove((x, y))

        self.first_hit_crd = None
        self.second_hit_crd = None
        self.ship_crds = []
        self.next_cells_to_shoot = []

    def shoot(self, crd, game) -> ShootStatus:
        self.not_cllicked_crds.remove(crd)
        if crd in self.next_cells_to_shoot:
            self.next_cells_to_shoot.remove(crd)
        game.shoot(*crd)
        return game.last_shoot_result

    def is_ready(self):
        if self.end_step_time is None: self.end_step_time = time.time()
        return time.time() - self.end_step_time > AI_HIT_COOLDOWN


def sign(x):
    if x < 0: return -1
    if x == 0: return 0
    if x > 0: return 1
    raise AssertionError('невозможная ситуация')
