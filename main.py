from base_elements import Dir, MyCell, OpponentCell
from settings import *


class ConsoleInteface:
    str_by_cells = {
        MyCell.empty: '. ',
        MyCell.intact_ship: '▄▀',
        MyCell.missed_shot: 'x ',
        MyCell.destroyed_ship: '# ',

        OpponentCell.unknown: '. ',
        OpponentCell.empty: 'X ',
        OpponentCell.ship: '# ',
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


# class Debug:
#     @staticmethod
#     def show_possible_crds_for_ships(possible_crds_for_ships, ship_sizes=None, directions=None):
#         if ship_sizes is None: ship_sizes = SHIPS_COUNT.keys()
#         if directions is None: directions = Dir.v, Dir.h
#
#         output = ''
#         for s in ship_sizes:
#             for d in directions:
#                 # print(f'{d.name}:')
#                 output += f'{d.name}:\n'
#                 for y in range(FIELD_HEIGHT):
#                     for x in range(FIELD_WIDTH):
#                         if (x, y) in possible_crds_for_ships[d][s]:
#                             # print(f'{s} ', end='')
#                             output += f'{s} '
#                         else:
#                             # print('. ', end='')
#                             output += '. '
#                     # print()
#                     output += '\n'
#                 # print()
#                 output += '\n'
#
#         return output
#
#     @staticmethod
#     def show_field(field):
#         out = ''
#
#         w, h = field.shape
#         for y in range(h):
#             for x in range(w):
#                 if field[x, y]:
#                     out += '▄▀'
#                 else:
#                     out += '. '
#             out += '\n'
#         out += '\n'
#
#         return out


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

    pass


if __name__ == '__main__':
    main()