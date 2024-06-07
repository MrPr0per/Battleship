import datetime
import random
import time
import typing

import numpy as np

from base_elements import ShipRect, Dir, MyCell, ShootStatus, OpponentCell, MyField, OpponentField
from settings import *


class RandomShipsSetter:
    def __init__(self, ships_count, w, h):
        self.ships_count = ships_count
        self.possible_crds_for_ships = self.get_possible_crds_for_ships(self.ships_count, w, h)

    @classmethod
    def get_random_ships(cls, w, h, ships_count, n_tries=20):
        for i in range(n_tries):
            try:
                ships = cls.try_get_ships(w, h, ships_count)
                break
            except:
                pass
        else:
            raise Exception(f'за {n_tries} попыток случайной расстановки '
                            f'заполнить поле не удалось (кораблей слишком много)')

        return ships

    @classmethod
    def set_ships(cls, field, ships: list[ShipRect]):
        for ship in ships:
            cls.set_ship(field, ship)

    @classmethod
    def set_random_ships(cls, field, ships_count, n_tries=20):
        ships = cls.get_random_ships(*field.shape, ships_count, n_tries)

        cls.set_ships(field, ships)

        return ships

    @classmethod
    def try_get_ships(cls, field_w, field_h, ships_count):
        ships = []
        ships_setter = RandomShipsSetter(ships_count, field_w, field_h)
        for ship_size, count in ships_setter.ships_count.items():
            for _ in range(count):
                ship = ships_setter.get_random_possible_ship(ship_size)
                ships_setter.update_possible_crds_for_ships(ship)
                # ships_setter.set_ship(field, ship)
                ships.append(ship)
        return ships

    def get_random_possible_ship(self, ship_size) -> ShipRect:
        # если корабль одного направления установить будет невозмножно - попробуем установить другого
        dirs = [Dir.v, Dir.h]
        random.shuffle(dirs)
        for dir_ in dirs:
            try:
                x0, y0 = random.choice(tuple(self.possible_crds_for_ships[dir_][ship_size]))
                ship = ShipRect(dir_, ship_size, x0, y0)
                return ship
            except IndexError:
                continue
        raise Exception(f'для корабля размера {ship_size} нет места')
        # raise Exception(f'для корабля такого размера нет места:'
        # f'{Debug.show_possible_crds_for_ships(self.possible_crds_for_ships, ship_sizes=(ship_size,))}')

    @classmethod
    def set_ship(cls, my_field, ship):
        x0, y0, x1, y1 = ship.get_rect()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                my_field[x, y] = MyCell.intact_ship

    @staticmethod
    def get_possible_crds_for_ships(ships_count, field_width, field_height):
        # possible_crds_for_ships[direction][size] = {(0,0), (0,1) ... (7,9)}
        # - все возмножные точки, в которых будет верхний левый угол соотвествующего корабля
        ships_sises = ships_count.keys()
        possible_crds_for_ships = {Dir.v: {}, Dir.h: {}}
        for s in ships_sises:
            possible_crds_for_ships[Dir.v][s] = set()
            possible_crds_for_ships[Dir.h][s] = set()

        for x in range(field_width):
            for y in range(field_height):
                for s in ships_sises:
                    if x + s <= field_width:
                        possible_crds_for_ships[Dir.h][s].add((x, y))
                    if y + s <= field_height:
                        possible_crds_for_ships[Dir.v][s].add((x, y))
        return possible_crds_for_ships

    def update_possible_crds_for_ships(self, ship):
        """
        принимает координаты, направление и размер поставленного на поле корабля
        и чистит из possible_crds_for_ships лишние координаты
        """

        # нужно удалить все координаты из области [x0-s, x1+1] x [y0-1, y1+1] для горизонтальных кораблей размера s
        #                                    и из [x0-1, x1+1] x [y0-s, y1+1] для веритикльных размера s
        # x0y0 - верхняя левая точка нового корабля
        # x1y1 - нижняя правая точка нового корабля

        x0, y0, x1, y1 = ship.get_rect()

        for s in self.ships_count.keys():
            for x in range(x0 - s, x1 + 1 + 1):
                for y in range(y0 - 1, y1 + 1 + 1):
                    # if x0 <= x <= x1 and y0 <= y <= y1: continue
                    try:
                        self.possible_crds_for_ships[Dir.h][s].remove((x, y))
                    except KeyError:
                        pass
            for x in range(x0 - 1, x1 + 1 + 1):
                for y in range(y0 - s, y1 + 1 + 1):
                    # if x0 <= x <= x1 and y0 <= y <= y1: continue
                    try:
                        self.possible_crds_for_ships[Dir.v][s].remove((x, y))
                    except KeyError:
                        pass


class IntactShipsCounter:
    """
    Хранит количество живых частей корабля, связанных с данной клеткой
    Например если IntactShipsCounter[(2,3)] == 3, то у корабля, содержащего клетку (2,3) есть еще 3 живые клетки
    Это нужно, чтобы определять, ранен или убил корабль
    """

    def __init__(self, ships):
        self.ship_id_by_crd = {}
        self.intact_count_by_ship_id = {}
        for ship_id, ship in enumerate(ships):
            x0, y0, x1, y1 = ship.get_rect()
            self.intact_count_by_ship_id[ship_id] = ship.size
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    self.ship_id_by_crd[(x, y)] = ship_id

    def __getitem__(self, crd):
        if crd in self.ship_id_by_crd:
            return self.intact_count_by_ship_id[self.ship_id_by_crd[crd]]
        return None

    def __setitem__(self, key, value):
        self.intact_count_by_ship_id[self.ship_id_by_crd[key]] = value


class Player:
    def __init__(self, w, h, ships: list[ShipRect], time_for_game: datetime.timedelta):
        # self.my_field = my_field

        self.my_field = np.full((w, h), MyCell.empty)
        self.ships_count = ShipRect.get_ships_count(ships)
        # self.ships = RandomShipsSetter.set_random_ships(self.my_field, ships_count)
        self.ships = ships
        RandomShipsSetter.set_ships(self.my_field, self.ships)

        self.intact_counter = IntactShipsCounter(self.ships)  # счетчик живых клеток у каждого корабля
        self.intact_ships_count = len(self.ships)  # количество живых кораблей всего

        self.opponent: typing.Union['Player', None] = None
        self.other_field = None
        self.user_marks = None  # отметки игрока на поле противника

        self.timer = Timer(time_for_game.seconds)

        # self.end_of_move_time = None

    def set_opponent(self, other_player: 'Player'):
        self.opponent = other_player
        self.other_field = np.full(self.opponent.my_field.shape, OpponentCell.unknown)
        self.user_marks = np.full(self.opponent.my_field.shape, False, dtype=bool)

    def get_shoot(self, x, y) -> ShootStatus:
        if self.my_field[x, y] in (MyCell.empty, MyCell.destroyed_ship):
            self.my_field[x, y] = MyCell.missed_shot
            return ShootStatus.miss
        elif self.my_field[x, y] == MyCell.intact_ship:
            self.my_field[x, y] = MyCell.destroyed_ship

            self.intact_counter[x, y] -= 1
            if self.intact_counter[x, y] < 0: raise Exception('Невозможная ситуация')
            if self.intact_counter[x, y] > 0: return ShootStatus.hit
            if self.intact_counter[x, y] == 0:
                self.intact_ships_count -= 1
                if self.intact_ships_count < 0: raise Exception('Невозможная ситуация')
                if self.intact_ships_count > 0: return ShootStatus.kill
                if self.intact_ships_count == 0: return ShootStatus.total_annihilation
        else:
            raise NotImplemented(f'попадание в {self.intact_counter[x, y].name} еще не обрабатывается')

    def mark_shoot(self, x, y, is_there_a_ship):
        # if self.other_field[x, y] != OppenentCells.unknown: raise Exception('эта клетка уже отмечена')
        self.other_field[x, y] = OpponentCell.ship if is_there_a_ship else OpponentCell.empty
        # self.opponent.my_field[x, y] = MyCell.missed_shot

    # def is_ready_to_change_player(self):
    #     return time.time() - self.end_of_move_time >= MOVE_COOLDOWN


class Timer:
    def __init__(self, seconds=None):
        self.seconds = seconds
        self.start_time = None

    def set_time(self, new_seconds):
        self.seconds = new_seconds

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time is None: return
        time_delta = time.time() - self.start_time
        self.seconds -= time_delta
        self.start_time = None

    def remained(self):
        if self.start_time is None: return max(0, self.seconds )
        time_delta = time.time() - self.start_time
        return max(0, self.seconds - time_delta)

    def is_time_up(self):
        return self.remained() <= 0

    def __str__(self):
        # s = int(self.remained())
        # return f'{s // 60}:{s % 60:0>2}:{self.remained() % 1:.2f}'
        s = self.remained()
        return f'{int(s // 60)}:{s % 60:0>5.2f}'
