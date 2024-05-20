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


class OpponentCells(Enum):
    unknown = 0
    empty = 1
    ship = 2
    marked_empty = auto()


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

    # @classmethod
    # def get_ship_by_crd(cls, x, y, ships) -> 'Ship':
    #     for ship in ships:
    #         x0, y0, x1, y1 = ship.get_rect()
    #         if x0 <= x <= x1 and y0 <= y <= y1:
    #             return ship
    #
    # def is_death(self, my_field):
    #     x0, y0, x1, y1 = self.get_rect()
    #     for x in range(x0, x1):
    #         for y in range(y0, y1):
    #             if my_field[x, y] == MyFildCells.intact_ship:
    #                 return False

    def __str__(self):
        return f'({self.x}, {self.y}) x{self.size}: {self.dir.name}'

    def __repr__(self):
        return str(self)


class RandomShipsSetter:
    def __init__(self, ships_count, w, h):
        self.ships_count = ships_count
        self.possible_crds_for_ships = self.get_possible_crds_for_ships(self.ships_count, w, h)

    @classmethod
    def set_random_ships(cls, field, ships_count):
        n_tries = 20
        for i in range(n_tries):
            try:
                ships = cls.get_ships(*field.shape, ships_count)
                break
            except:
                pass
        else:
            raise Exception('кажется, заполнить такое маленькое поле этим набором кораблей - невозможно')

        for ship in ships:
            cls.set_ship(field, ship)

        return ships

    @classmethod
    def get_ships(cls, field_w, field_h, ships_count):
        ships = []
        ships_setter = RandomShipsSetter(ships_count, field_w, field_h)
        for ship_size, count in ships_setter.ships_count.items():
            for _ in range(count):
                ship = ships_setter.get_random_possible_ship(ship_size)
                ships_setter.update_possible_crds_for_ships(ship)
                # ships_setter.set_ship(field, ship)
                ships.append(ship)
        return ships

    def get_random_possible_ship(self, ship_size) -> Ship:
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

    @classmethod
    def set_ship(cls, my_field, ship):
        x0, y0, x1, y1 = ship.get_rect()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                my_field[x, y] = MyFildCells.intact_ship

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
    def __init__(self, w, h, ships_count):
        self.my_field = np.full((w, h), MyFildCells.empty)
        self.ships_count = ships_count
        self.ships = RandomShipsSetter.set_random_ships(self.my_field, ships_count)
        self.intact_counter = IntactShipsCounter(self.ships)  # счетчик живых клеток у каждого корабля
        self.intact_ships_count = len(self.ships)  # количество живых кораблей всего

        self.opponent = None
        self.other_field = None
        self.user_marks = None  # отметки игрока на поле противника

    def set_opponent(self, other_player: 'Player'):
        self.opponent = other_player
        self.other_field = np.full(self.opponent.my_field.shape, OpponentCells.unknown)
        self.user_marks = np.full(self.opponent.my_field.shape, False, dtype=bool)

    def get_shoot(self, x, y) -> ShootStatus:
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
        self.other_field[x, y] = OpponentCells.ship if is_there_a_ship else OpponentCells.empty


class ConsoleInteface:
    str_by_cells = {
        MyFildCells.empty: '. ',
        MyFildCells.intact_ship: '▄▀',
        MyFildCells.missed_shot: 'x ',
        MyFildCells.destroyed_ship: '# ',

        OpponentCells.unknown: '. ',
        OpponentCells.empty: 'X ',
        OpponentCells.ship: '# ',
    }

    @classmethod
    def print_fields(cls, main_player_field, other_player_field, main_player_on_left):
        # формируем построчно сначала поле текущего игрока, потом поле противника
        w_main, h_main = main_player_field.shape
        w_other, h_other = other_player_field.shape
        number_margin = len(str(max(h_main, h_other)))
        main_player_lines = ['my:', ' ' * (number_margin + 1) + ' '.join(ABC[:w_main])]
        other_player_lines = ['opponent:', ' ' * (number_margin + 1) + ' '.join(ABC[:w_other])]
        for y in range(h_main):
            main_player_lines.append(f'{y + 1}'.rjust(number_margin, ' ') + ' ')
            for x in range(w_main):
                main_player_lines[-1] += cls.str_by_cells[main_player_field[x, y]]
        for y in range(h_other):
            other_player_lines.append(f'{y + 1}'.rjust(number_margin, ' ') + ' ')
            for x in range(w_other):
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


# class Game:
#     def __init__(self):
#         self.players = [Player(10, 11, DEFAULT_SHIPS_COUNT), Player(12, 13, DEFAULT_SHIPS_COUNT)]
#         self.players[0].set_opponent(self.players[1])
#         self.players[1].set_opponent(self.players[0])
#         self.current_player_index = 0
# 
#     def game_cycle(self):
#         while True:
#             current_player = self.players[self.current_player_index]
#             other_player = self.players[(self.current_player_index + 1) % 2]
#             ConsoleInteface.print_fields(current_player.my_field, current_player.other_field,
#                                          self.current_player_index == 0)
# 
#             shoot_crd = None
#             while shoot_crd is None:
#                 shoot_crd = self.try_parse_input_crd(input(), *current_player.my_field.shape)
#             x, y = shoot_crd
# 
#             shoot_status = other_player.get_shoot(x, y)
#             current_player.mark_shoot(x, y, shoot_status.is_success())
#             print(shoot_status)
#             if shoot_status == ShootStatus.i_lose:
#                 print(f'победил игрок {self.current_player_index + 1}!!!')
#                 break
# 
#             if not shoot_status.is_success():
#                 self.current_player_index = (self.current_player_index + 1) % 2
# 
#     @staticmethod
#     def try_parse_input_crd(inp, w, h):
#         if len(inp) < 2: return None
#         letter = inp[0].upper()
#         if letter not in ABC: return None
#         x = ABC.index(letter)
# 
#         number = inp[1:]
#         if not number.isdigit(): return None
#         y = int(number) - 1
# 
#         if not (0 <= x < w): return None
#         if not (0 <= y < h): return None
# 
#         return x, y


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

        w, h = field.shape
        for y in range(h):
            for x in range(w):
                if field[x, y]:
                    out += '▄▀'
                else:
                    out += '. '
            out += '\n'
        out += '\n'

        return out


# class Tests:
#     @staticmethod
#     def test_set_ship():
#         global FIELD_WIDTH, FIELD_HEIGHT
#         old_w, old_h = FIELD_WIDTH, FIELD_HEIGHT
#         FIELD_WIDTH, FIELD_HEIGHT = 4, 4
#
#         pl = Player()
#         pl.set_ship(Ship(Dir.v, 4, 0, 0))
#
#         print(Debug.show_field(pl.my_ships))
#
#         FIELD_WIDTH, FIELD_HEIGHT = old_w, old_h


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

# (1,7225)	SAS CITY
# (2,7223)	Молодость всё простит
# (3,6728)	Анар балана
# (4,6583)	Топающие котики🐈🐖🐈
# (5,6263)	Спать люблю пиздец
# (6,5886)	Матвей и ааа, женщины
# (7,5863)	Грешные блуждатели 96 регион
# (8,5563)	В поисках твоей мамки
# (9,5323)	МАКАРЕГОРОВ
# (10,5153)	Скуфи-ду
# (11,4883)	Пешеходно-безалкогольное хозяйство
# (12,4873)	Можелюк и Ко
# (13,4663)	Интегральные Извращенцы
# (14,4643)	лягушки-нелегалы
# (15,4623)	Распределение хаоса
# (16,4408)	Гураняяя
# (17,4303)	устрицам вход запрещен
# (18,4273)	Волчки
# (19,4163)	Friends
# (20,4023)	Тельца
# (21,3923)	Малышки молоденькие
# (22,3743)	Без названия
# (23,3613)	Настол(й)ки
# (24,3603)	Гусиные кексики
# (25,3563)	Теорема Фистинга
# (26,3243)	СГУФ
# (27,2993)	Токио-3
# (28,2683)	dxdy
# (29,2623)	Хуяримся по городу
# (30,2613)	Хлеб
# (31,2128)	Ляськи-масяськи
# (32,2113)	Длинный логарифм
# (33,2103)	Проебали Кирилла
# (34,1983)	Саппортеры
# (35,1963)	Микробы
# (36,1938)	4 мушкетёра Ахахах🌚
# (37,1843)	антиперсики
# (38,1673)	8 друзей Савелия
# (39,1656)	Я_КАКАЮ
# (40,1623)	abs(Власть)
# (41,1623)	6 подруг Оушена
# (42,1523)	Try hard
# (43,1443)	е-балл от рубля
# (44,1243)	Геометрическое место кочек
# (45,1173)	Grott Quest
# (46,741)	questrunner(s*?)
# (47,723)	Интеллектуалы
# (48,703)	Скибиди туалет или крипер
# (49,563)	Нас было двое
# (50,400)	Хайп
# (51,362)	Эвтектический чугун
# (52,0)	гопстоп!
# (53,0)	Спецотдел
# (54,0)	Разрабы пидорасы
# (55,0)	Персики
# (56,0)	Мороша TEAM
# (57,0)	Горквест
# (58,0)	F1
# (59,-1)	Оргииии
