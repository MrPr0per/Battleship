import datetime
import random
import time

import numpy as np
from numpy import array as arr
from enum import Enum, auto
from settings import *


class Dir(Enum):
    v = auto()
    h = auto()


class MyFildCells(Enum):
    empty = 0
    intact_ship = 1
    missed_shot = 2
    destroyed_ship = 3


class OppenentCells(Enum):
    unknown = 0
    empty = 1
    ship = 2


class ShootStatus(Enum):
    miss = auto()
    hit = auto()
    kill = auto()
    i_lose = auto()

    def is_success(self):
        if self == self.miss: return False
        if self in (ShootStatus.hit, ShootStatus.kill, ShootStatus.i_lose): return True
        raise NotImplemented()


class Ship:
    def __init__(self, dir_, size, x, y):
        self.dir = dir_
        self.size = size
        self.x = x
        self.y = y

    def get_rect(self):
        """возвращает (x0, y0, x1, y1) - верхнюю левую и нижнюю правую точки корабля"""
        if self.dir == Dir.h:
            return self.x, self.y, self.x + self.size - 1, self.y
        if self.dir == Dir.v:
            return self.x, self.y, self.x, self.y + self.size - 1
        raise ValueError('у корабля задано неизвестное напрвление (?)')

    def __str__(self):
        return f'({self.x}, {self.y}) x{self.size}: {self.dir.name}'

    def __repr__(self):
        return str(self)


class RandomShipsSetter:
    def __init__(self):
        self.possible_crds_for_ships = self.get_possible_crds_for_ships()

    @classmethod
    def set_random_ships(cls, field):
        ships = []
        ships_setter = RandomShipsSetter()
        for ship_size, count in SHIPS_COUNT.items():
            for _ in range(count):
                ship = ships_setter.get_random_possible_ship(ship_size)
                ships_setter.update_possible_crds_for_ships(ship)
                ships_setter.set_ship(field, ship)
                ships.append(ship)
        return ships

    def get_random_possible_ship(self, ship_size):
        # если корабль одно направления установить будет невозмножно - попробуем установить корабль другого направления
        dirs = [Dir.v, Dir.h]
        random.shuffle(dirs)
        for dir_ in dirs:
            try:
                x0, y0 = random.choice(tuple(self.possible_crds_for_ships[dir_][ship_size]))
                ship = Ship(dir_, ship_size, x0, y0)
                return ship
            except IndexError:
                continue
        raise Exception(f'для корабля такого размера нет места:'
                        f'{Debug.show_possible_crds_for_ships(self.possible_crds_for_ships, ship_sizes=(ship_size,))}')

    def set_ship(self, my_field, ship):
        x0, y0, x1, y1 = ship.get_rect()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                my_field[x, y] = MyFildCells.intact_ship

    @staticmethod
    def get_possible_crds_for_ships():
        # possible_crds_for_ships[direction][size] = {(0,0), (0,1) ... (7,9)}
        # - все возмножные точки, в которых будет верхний левый угол соотвествующего корабля
        ships_sises = SHIPS_COUNT.keys()
        possible_crds_for_ships = {Dir.v: {}, Dir.h: {}}
        for s in ships_sises:
            possible_crds_for_ships[Dir.v][s] = set()
            possible_crds_for_ships[Dir.h][s] = set()

        for x in range(FIELD_WIDTH):
            for y in range(FIELD_HEIGHT):
                for s in ships_sises:
                    if x + s <= FIELD_WIDTH:
                        possible_crds_for_ships[Dir.h][s].add((x, y))
                    if y + s <= FIELD_HEIGHT:
                        possible_crds_for_ships[Dir.v][s].add((x, y))
        return possible_crds_for_ships

    def update_possible_crds_for_ships(self, ship):
        """
        принимает координаты, направление и размер поставленного на поле корабля
        и чистит из possible_crds_for_ships лишние координаты
        """

        # нужно удилить все координаты из области [x0-s, x1+1] x [y0-1, y1+1] для горизонтальных кораблей размера s
        #                                    и из [x0-1, x1+1] x [y0-s, y1+1] для веритикльных размера s
        # x0y0 - верхняя левая точка нового корабля
        # x1y1 - нижняя правая точка нового корабля

        x0, y0, x1, y1 = ship.get_rect()

        for s in SHIPS_COUNT.keys():
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

    # def get_count(self, x, y):
    #     return self.intact_count_by_ship_id[self.ship_id_by_crd[(x,y)]]

    def __getitem__(self, crd):
        if crd in self.ship_id_by_crd:
            return self.intact_count_by_ship_id[self.ship_id_by_crd[crd]]
        return None

    def __setitem__(self, key, value):
        self.intact_count_by_ship_id[self.ship_id_by_crd[key]] = value


class Player:
    def __init__(self):
        self.my_field = np.full((FIELD_WIDTH, FIELD_HEIGHT), MyFildCells.empty)
        self.other_field = np.full((FIELD_WIDTH, FIELD_HEIGHT), OppenentCells.unknown)
        ships = RandomShipsSetter.set_random_ships(self.my_field)
        self.intact_counter = IntactShipsCounter(ships)  # счетчик живых клеток у каждого корабля
        self.intact_ships_count = len(ships)  # количество живых кораблей всего

    def get_shoot(self, x, y):
        if self.my_field[x, y] in (MyFildCells.empty, MyFildCells.destroyed_ship):
            self.my_field[x, y] = MyFildCells.missed_shot
            return ShootStatus.miss
        elif self.my_field[x, y] == MyFildCells.intact_ship:
            self.my_field[x, y] = MyFildCells.destroyed_ship
            self.intact_counter[x, y] -= 1
            if self.intact_counter[x, y] < 0: raise Exception('Невозможная ситуация')
            if self.intact_counter[x, y] > 0: return ShootStatus.hit
            if self.intact_counter[x, y] == 0:
                self.intact_ships_count -= 1
                if self.intact_ships_count < 0: raise Exception('Невозможная ситуация')
                if self.intact_ships_count > 0: return ShootStatus.kill
                if self.intact_ships_count == 0: return ShootStatus.i_lose
        else:
            raise NotImplemented(f'попадание в {self.intact_counter[x, y].name} еще не обрабатывается')

    def mark_shoot(self, x, y, is_there_a_ship):
        # if self.other_field[x, y] != OppenentCells.unknown: raise Exception('эта клетка уже отмечена')
        self.other_field[x, y] = OppenentCells.ship if is_there_a_ship else OppenentCells.empty


class UserInteface:
    str_by_cells = {
        MyFildCells.empty: '. ',
        MyFildCells.intact_ship: '▄▀',
        MyFildCells.missed_shot: 'x ',
        MyFildCells.destroyed_ship: '# ',

        OppenentCells.unknown: '. ',
        OppenentCells.empty: 'X ',
        OppenentCells.ship: '# ',
    }

    @classmethod
    def print_fields(cls, main_player_field, other_player_field, main_player_on_left):
        # формируем построчно сначала поле текущего игрока, потом поле противника
        number_margin = len(str(FIELD_HEIGHT))
        main_player_lines = ['my:', ' ' * (number_margin + 1) + ' '.join(ABC[:FIELD_WIDTH])]
        other_player_lines = ['opponent:', ' ' * (number_margin + 1) + ' '.join(ABC[:FIELD_WIDTH])]
        for y in range(FIELD_HEIGHT):
            main_player_lines.append(f'{y + 1}'.rjust(number_margin, ' ') + ' ')
            other_player_lines.append(f'{y + 1}'.rjust(number_margin, ' ') + ' ')
            for x in range(FIELD_WIDTH):
                main_player_lines[-1] += cls.str_by_cells[main_player_field[x, y]]
                other_player_lines[-1] += cls.str_by_cells[other_player_field[x, y]]

        out = ''
        if main_player_on_left:
            max_width = max(map(len, main_player_lines))
        else:
            max_width = max(map(len, other_player_lines))

        margin = 4
        # выводим
        for i in range(max(len(main_player_lines), len(other_player_lines))):
            main_line = main_player_lines[i] if i < len(main_player_lines) else ''
            other_line = other_player_lines[i] if i < len(other_player_lines) else ''
            if main_player_on_left:
                out += main_line.ljust(max_width + margin) + other_line + '\n'
            else:
                out += other_line.ljust(max_width + margin) + main_line + '\n'

        print(out)
        return out


class Game:
    def __init__(self):
        self.players = [Player(), Player()]
        self.current_player_index = 0

    def game_cycle(self):
        while True:
            current_player = self.players[self.current_player_index]
            other_player = self.players[(self.current_player_index + 1) % 2]
            UserInteface.print_fields(current_player.my_field, current_player.other_field,
                                      self.current_player_index == 0)

            shoot_crd = None
            while shoot_crd is None:
                shoot_crd = self.try_parse_input_crd(input())
            x, y = shoot_crd
            
            shoot_status = other_player.get_shoot(x, y)
            current_player.mark_shoot(x, y, shoot_status.is_success())
            print(shoot_status)
            if shoot_status == ShootStatus.i_lose:
                print(f'победил игрок {self.current_player_index + 1}!!!')
                break
            
            if not shoot_status.is_success():
                self.current_player_index = (self.current_player_index + 1) % 2



    @staticmethod
    def try_parse_input_crd(inp):
        if len(inp) < 2: return None
        letter = inp[0].upper()
        if letter not in ABC: return None
        x = ABC.index(letter)

        number = inp[1:]
        if not number.isdigit(): return None
        y = int(number) - 1

        if not (0 <= x < FIELD_WIDTH): return None
        if not (0 <= y < FIELD_HEIGHT): return None

        return x, y


class Debug:
    @staticmethod
    def show_possible_crds_for_ships(possible_crds_for_ships, ship_sizes=None, directions=None):
        if ship_sizes is None: ship_sizes = SHIPS_COUNT.keys()
        if directions is None: directions = Dir.v, Dir.h

        output = ''
        for s in ship_sizes:
            for d in directions:
                # print(f'{d.name}:')
                output += f'{d.name}:\n'
                for y in range(FIELD_HEIGHT):
                    for x in range(FIELD_WIDTH):
                        if (x, y) in possible_crds_for_ships[d][s]:
                            # print(f'{s} ', end='')
                            output += f'{s} '
                        else:
                            # print('. ', end='')
                            output += '. '
                    # print()
                    output += '\n'
                # print()
                output += '\n'

        return output

    @staticmethod
    def show_field(field):
        out = ''

        for y in range(FIELD_HEIGHT):
            for x in range(FIELD_WIDTH):
                if field[x, y]:
                    out += '▄▀'
                else:
                    out += '. '
            out += '\n'
        out += '\n'

        return out


class Tests:
    @staticmethod
    def test_set_ship():
        global FIELD_WIDTH, FIELD_HEIGHT
        old_w, old_h = FIELD_WIDTH, FIELD_HEIGHT
        FIELD_WIDTH, FIELD_HEIGHT = 4, 4

        pl = Player()
        pl.set_ship(Ship(Dir.v, 4, 0, 0))

        print(Debug.show_field(pl.my_ships))

        FIELD_WIDTH, FIELD_HEIGHT = old_w, old_h


# class Game:
#     @staticmethod
#     def run(cls):

def main():
    # r = Player.get_possible_crds_for_ships()
    # Player.update_possible_crds_for_ships(r, Ship(Dir.h, 2, 5, 5))
    # Debug.show_possible_crds_for_ships(r)

    # Tests.test_set_ship()

    # for i in range(100):
    #     pl1 = Player()
    #     pl1.set_random_ships()
    #     print(Debug.show_field(pl1.my_ships))

    game = Game()
    game.game_cycle()


if __name__ == '__main__':
    main()
