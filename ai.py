import random
import time

import numpy as np

from base_elements import OpponentCell
from gameplay import Player


class AI:
    pass


class RandomAI(AI, Player):
    def __init__(self, w, h, ships_count):
        super().__init__(w, h, ships_count)
        self.not_cllicked_crds = None
        self.cooldown = 0.7 # [s]
        # self.cooldown = 0.1 # [s]
        self.end_step_time = None

    def set_opponent(self, other_player: 'Player'):
        self.opponent = other_player
        self.other_field = np.full(self.opponent.my_field.shape, OpponentCell.unknown)
        self.user_marks = np.full(self.opponent.my_field.shape, False, dtype=bool)
        w, h = self.opponent.my_field.shape
        self.not_cllicked_crds = [(x, y) for x in range(w) for y in range(h)]

    def make_step(self, game):
        # if self.end_step_time is not None and time.time() - self.end_step_time < self.cooldown: return 
        cell = random.choice(self.not_cllicked_crds)
        self.not_cllicked_crds.remove(cell)

        game.shoot(*cell)
        
        self.end_step_time = time.time()

        return cell
    
    def is_ready(self):
        if self.end_step_time is None: self.end_step_time = time.time()
        return self.end_step_time is None or time.time() - self.end_step_time > self.cooldown


class SmartAI(AI, Player):
    pass