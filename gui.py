import pickle
import random
import time

import numpy as np

from interface.interface_main import ScreensController, Settings, PlayerIdentity, RenderedTextHolder
from settings import *
import pygame
from base_elements import MyCell, OpponentCell, ShootStatus
from gameplay import Player, Timer
from ai import AI, RandomAI, SmartAI
from animation import Animation
from enum import Enum, auto

from settings import ABC


# перед началом игры другой маинлуп с менюшками:
# - выбор левого, правого игрока из (чел, тупой аи, умный аи)
# - расстановка кораблей

# пофиксить паузы между ходами ии

# TODO: реализовать
# промах
# забираем возможность отрывать клетки
# по нажатию любой клавиши показываем черный экран и передаем управление (но забираем возможнось что либо делать)
# по нажатию любой клавиши убираем черный экран и даем управление
# если нужно передать управление к ии все эти танцы с черным экраном не нужны:

# ии ходит только когда нет кулдауна
# если ходит ии, то не нужно показывать его поле (если сейчас не дебаг мод)

class GameState(Enum):
    player_is_move = auto()
    end_of_move = auto()
    splash = auto()
    gameover = auto()
    cooldown_before_change_player = auto()

    # def next(self):
    #     if self == self.player_is_move: return self.end_of_move
    #     if self == self.end_of_move: return self.splash
    #     if self == self.splash: return self.player_is_move


class Game:
    def __init__(self, settings: Settings):
        pl1_class = self.get_class_by_identity(settings.left_settings.player_identity)
        pl2_class = self.get_class_by_identity(settings.right_settings.player_identity)

        self.players = [
            # Player(10, 10, DEFAULT_SHIPS_COUNT),
            # # Player(10, 10, DEFAULT_SHIPS_COUNT),
            # RandomAI(10, 10, DEFAULT_SHIPS_COUNT),
            # # RandomAI(6, 10, DEFAULT_SHIPS_COUNT),

            pl1_class(*settings.left_settings.field_size, settings.left_settings.ships,
                      settings.left_settings.time_to_game),
            pl2_class(*settings.right_settings.field_size, settings.right_settings.ships,
                      settings.right_settings.time_to_game),
        ]
        self.players[0].set_opponent(self.players[1])
        self.players[1].set_opponent(self.players[0])
        self.current_player_index = 0
        self.current_player().timer.start()

        self.last_shoot_result: ShootStatus | None = None
        self.is_need_to_change_player = False

        self.winner_index = None

        self.game_state = GameState.player_is_move

        self.last_save_time = None

    @staticmethod
    def get_class_by_identity(identity: PlayerIdentity):
        if identity == PlayerIdentity.human:
            return Player
        elif identity == PlayerIdentity.randomAI:
            return RandomAI
        elif identity == PlayerIdentity.smartAI:
            return SmartAI
        else:
            raise NotImplemented()

    def current_player(self):
        return self.players[self.current_player_index]

    def current_opponent(self):
        return self.players[self.current_opponent_index()]

    def current_opponent_index(self):
        return (self.current_player_index + 1) % 2

    def shoot(self, x, y):
        self.last_shoot_result = self.current_opponent().get_shoot(x, y)
        self.current_player().mark_shoot(x, y, self.last_shoot_result.is_success())

        if not self.last_shoot_result.is_success():
            self.is_need_to_change_player = True

        if self.last_shoot_result == ShootStatus.total_annihilation:
            self.gameover(self.current_player_index)
        #     self.current_player_index += 1
        #     self.current_player_index %= 2

        # return result

    def change_player(self):
        # self.current_player().timer.stop()
        self.is_need_to_change_player = False
        self.current_player_index += 1
        self.current_player_index %= 2
        # self.current_player().timer.start()

    def check_loose_by_time(self):
        if self.current_player().timer.remained() <= 0:
            self.gameover(self.current_opponent_index())

    def gameover(self, winner_index):
        self.winner_index = winner_index
        self.current_player().timer.stop()
        self.current_opponent().timer.stop()

    def save(self):
        self.last_save_time = time.time()
        with open(QUICKSAVE_PATH, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls):
        with open(QUICKSAVE_PATH, 'rb') as f:
            game:'Game' = pickle.load(f)
            time_since_last_save = time.time() - game.last_save_time
            if game.players[0].timer.start_time is not None: game.players[0].timer.start_time += time_since_last_save
            if game.players[1].timer.start_time is not None: game.players[1].timer.start_time += time_since_last_save
            return game

# у игрока и ии должен быть общий метод, отвечающий за получение следующего хода


class Gui:
    color_by_cell = {
        MyCell.empty: None,
        MyCell.intact_ship: (230, 230, 230),
        MyCell.missed_shot: (50, 50, 50),
        MyCell.destroyed_ship: (200, 100, 100),

        OpponentCell.unknown: None,
        OpponentCell.empty: (100, 100, 100),
        OpponentCell.ship: (200, 100, 100)
    }

    def __init__(self, sc, clock, game: Game):
        pygame.init()
        self.sc: pygame.Surface = sc
        self.clock = clock

        self.game = game
        # self.game.game_state = GameState.player_is_move  # TODO: перенести это в game

        self.cell_size = 40  # [px]
        # координаты верхеного левого угла у левого и правого полей на экране
        self.p_left, self.p_right = self.get_top_left_corners()
        self.mark_sprite = pygame.image.load('sprites/flag.png')
        # if self.cell_size != 40: raise Exception('отмасштабировать спрайт, если cell_size != 40')

        self.animations = set()  # текущие анимации

        self.transfer_text1 = DEFAULT_FONT.render('Нажмите любую клавишу, чтобы передать управление', True, WHITE)
        self.transfer_text2 = DEFAULT_FONT.render('Нажмите любую клавишу', True, WHITE)
        self.game_over_text_render = None
        self.shoot_status_text_render_holder = RenderedTextHolder()
        self.save_hint_render = pygame.font.SysFont(DEFAULT_FONT_NAME, 18).render('[F5] - сохранение [F9] - загрузка (работают и после закрытия игры)', True, WHITE)

        self.cooldown_timer = Timer()

    def mainloop(self):
        while True:
            events = pygame.event.get()
            mouce_pressed = pygame.mouse.get_pressed()
            keys_pressed = pygame.key.get_pressed()
            self.process_events(events, mouce_pressed, keys_pressed)

            # if not isinstance(self.game.current_player(), AI) and self.game.is_need_to_change_player:
            #     self.game.change_player()

            self.game.check_loose_by_time()

            if self.game.winner_index is not None:
                self.game.game_state = GameState.gameover

            self.animations = {anim for anim in self.animations if not anim.is_over()}

            self.sc.fill((0, 0, 0))

            if self.game.game_state in (
                    GameState.player_is_move, GameState.end_of_move, GameState.cooldown_before_change_player):
                self.draw_ui()
                self.draw_animations()
                self.draw_timers()
            elif self.game.game_state == GameState.splash:
                self.draw_splash()
                self.draw_timers()
            elif self.game.game_state == GameState.gameover:
                self.draw_gameover_screen()
                self.draw_timers()
            else:
                raise NotImplemented()

            # if self.game.is_need_to_change_player and len(self.animations) == 0:
            #     self.game.change_player()

            pygame.display.update()
            self.clock.tick(FPS)

    def get_field_crd(self, mouse_x, mouse_y):
        """
        :return: координаты на поле противника
        """
        topleft_point = self.p_left if self.game.current_player_index == 1 else self.p_right
        x, y = mouse_x - topleft_point[0], mouse_y - topleft_point[1]
        x //= self.cell_size
        y //= self.cell_size
        return int(x), int(y)

    def get_sc_crd(self, field_x, field_y):
        """
        :return: координаты клетки на экране по координатам на поле противника
        """
        x0, y0 = self.p_left if self.game.current_player_index == 1 else self.p_right
        return (x0 + field_x * self.cell_size,
                y0 + field_y * self.cell_size,)

    def process_events(self, events, mouce_pressed, keys_pressed):
        def quit_game():
            pygame.quit()
            quit()

        def is_any_key_pressed(event_: pygame.event.Event):
            return event_.type == pygame.KEYDOWN and event_.key not in (pygame.K_F5, pygame.K_F9, pygame.K_ESCAPE)

        if not isinstance(self.game.current_player(), Player): return

        for event in events:
            if event.type == pygame.QUIT: quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: quit_game()
                if event.key == pygame.K_F5:
                    self.game.save()
                if event.key == pygame.K_F9:
                    self.game = Game.load()

        if self.game.game_state == GameState.player_is_move:
            # if self.game.is_need_to_change_player and self.game.current_player().is_ready_to_change_player():
            #     self.game.current_player().end_of_move_time = None
            #     self.game.current_player().timer.stop()
            #     self.game.change_player()
            #     self.game.current_player().timer.start()
            #     return

            if isinstance(self.game.current_player(), AI):
                if self.game.current_player().is_ready():
                    # if self.game.is_need_to_change_player:
                    #     self.game.current_player().end_step_time = None
                    #     self.game.current_player().timer.stop()
                    #     self.game.change_player()
                    #     self.game.current_player().timer.start()
                    # else:
                    x, y = self.game.current_player().make_step(self.game)
                    # self.game.current_player().make_step(self.game, *self.game.current_player().other_field.shape)

                    if self.game.last_shoot_result.is_success():
                        self.animations.add(Animation(*self.get_sc_crd(x, y), 'BOOM'))
                    else:
                        self.animations.add(Animation(*self.get_sc_crd(x, y), 'BULK'))
                        self.start_cooldown_before_change_player()
                        self.game.current_player().end_step_time = None

                        # self.gui_game_state = GuiGameState.cooldown_before_change_player

                        # self.game.current_player().timer.stop()
                        # # self.game.change_player()
                        # self.game.is_need_to_change_player = True
                        # self.game.current_player().end_of_move_time = time.time()
                        # self.game.current_player().timer.start()

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    x, y = self.get_field_crd(mouse_x, mouse_y)
                    w, h = self.game.current_player().other_field.shape
                    if not (0 <= x < w and 0 <= y < h): continue

                    if event.button == 1:
                        if self.game.current_player().other_field[x, y] != OpponentCell.unknown: continue
                        self.game.shoot(x, y)
                        if self.game.last_shoot_result.is_success():
                            self.animations.add(Animation(*self.get_sc_crd(x, y), 'BOOM'))
                        else:
                            self.animations.add(Animation(*self.get_sc_crd(x, y), 'BULK'))
                            # if not isinstance(self.game.current_opponent(), AI):
                            #     # если оппонент - не ии, то нужно передать управление через черный экран
                            #     self.gui_game_state = GuiGameState.end_of_move
                            # else:
                            #     self.game.current_player().timer.stop()
                            #     self.game.change_player()
                            #     self.game.current_player().timer.start()

                            # if not isinstance(self.game.current_player(), AI):
                            #     self.gui_game_state = GuiGameState.end_of_move
                            # else:
                            #     self.game.current_player().timer.stop()
                            #     self.game.change_player()
                            #     self.game.current_player().timer.start()

                            if not isinstance(self.game.current_opponent(), AI) and not isinstance(
                                    self.game.current_player(), AI):
                                self.game.game_state = GameState.end_of_move
                            else:
                                self.start_cooldown_before_change_player()
                                # self.gui_game_state = GuiGameState.cooldown_before_change_player
                                # self.game.current_player().timer.stop()
                                # # self.game.change_player()
                                # self.game.is_need_to_change_player = True
                                # self.game.current_player().end_of_move_time = time.time()
                                # self.game.current_player().timer.start()

                    if event.button == 3:
                        self.game.current_player().user_marks[x, y] = not self.game.current_player().user_marks[x, y]
        elif self.game.game_state == GameState.end_of_move:
            for event in events:
                if is_any_key_pressed(event):
                    if isinstance(self.game.current_player(), AI):
                        raise AssertionError('после ии ход должен сразу передваться игроку, минуя end_of_move и splash')
                    else:
                        if isinstance(self.game.current_opponent(), AI):
                            self.game.game_state = GameState.player_is_move
                            self.game.current_player().timer.stop()
                            self.game.change_player()
                            self.game.current_player().timer.start()
                        else:
                            # если оппонент - не ии (человек), то нужно передать управление через черный экран
                            self.game.game_state = GameState.splash
                            self.game.current_player().timer.stop()

                if event.type == pygame.MOUSEBUTTONDOWN:  # оставляем возможность ставить крестики даже после промаха
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    x, y = self.get_field_crd(mouse_x, mouse_y)
                    w, h = self.game.current_player().other_field.shape
                    if not (0 <= x < w and 0 <= y < h): continue

                    if event.button == 3:
                        self.game.current_player().user_marks[x, y] = not self.game.current_player().user_marks[x, y]
        elif self.game.game_state == GameState.splash:
            for event in events:
                if is_any_key_pressed(event):
                    # self.gui_game_state = self.gui_game_state.next()
                    self.game.game_state = GameState.player_is_move
                    self.game.change_player()
                    self.game.current_player().timer.start()
        elif self.game.game_state == GameState.cooldown_before_change_player:
            if self.cooldown_timer.is_time_up():
                self.game.change_player()
                self.game.current_player().timer.start()
                self.game.game_state = GameState.player_is_move

            # # self.game.change_player()
            # self.game.is_need_to_change_player = True
            # self.game.current_player().end_of_move_time = time.time()
            # self.game.current_player().timer.start()

        elif self.game.game_state == GameState.gameover:
            for event in events:
                if is_any_key_pressed(event):
                    quit_game()
        else:
            raise NotImplemented()

    def start_cooldown_before_change_player(self):
        self.game.game_state = GameState.cooldown_before_change_player
        self.game.current_player().timer.stop()
        self.game.current_opponent().timer.stop()
        self.cooldown_timer.set_time(MOVE_COOLDOWN)
        self.cooldown_timer.start()

    def draw_timers(self):
        r1 = DEFAULT_FONT.render(self.game.players[0].timer.__str__(), True, WHITE)
        r2 = DEFAULT_FONT.render(self.game.players[1].timer.__str__(), True, WHITE)
        w, h = self.sc.get_size()
        self.sc.blit(r1, (r1.get_width() * 0.5, r1.get_height() * 2))
        self.sc.blit(r2, (w - r2.get_width() * (1 + 0.5), r2.get_height() * 2))

    def draw_ui(self):

        if self.game.current_player_index == 0:
            self.draw_field(*self.p_left, self.game.current_player().my_field,
                            is_hide=isinstance(self.game.current_player(), AI) and HIDE_AI_FIELD)
            self.draw_field(*self.p_right, self.game.current_player().other_field,
                            self.game.current_player().user_marks)
        else:
            self.draw_field(*self.p_right, self.game.current_player().my_field,
                            is_hide=isinstance(self.game.current_player(), AI) and HIDE_AI_FIELD)
            self.draw_field(*self.p_left, self.game.current_player().other_field, self.game.current_player().user_marks)

        if self.game.game_state == GameState.end_of_move:
            self.sc.blit(self.transfer_text1, (TEXT_MATGIN_LEFT_RIGHT, TEXT_MATGIN_TOP_BOT))

        shoot_status_str = self.game.last_shoot_result.__str__()
        if shoot_status_str == 'None': shoot_status_str = ''
        shoot_status_render = self.shoot_status_text_render_holder[shoot_status_str]
        self.sc.blit(shoot_status_render, (
            TEXT_MATGIN_LEFT_RIGHT, self.sc.get_height() - shoot_status_render.get_height() - TEXT_MATGIN_TOP_BOT))

        self.sc.blit(self.save_hint_render, (self.sc.get_width() - self.save_hint_render.get_width() - TEXT_MATGIN_LEFT_RIGHT,
                                             self.sc.get_height() - self.save_hint_render.get_height() - TEXT_MATGIN_TOP_BOT))

    def draw_gameover_screen(self):
        self.draw_field(*self.p_left, self.game.players[0].my_field)
        self.draw_field(*self.p_right, self.game.players[1].my_field)

        if self.game_over_text_render is None:
            winner = 'Left player' if self.game.winner_index == 0 else 'Right player'
            self.game_over_text_render = DEFAULT_FONT.render(f'{winner} is win!', True, WHITE)
        self.sc.blit(self.game_over_text_render, (
            self.sc.get_width() / 2 - self.game_over_text_render.get_width() / 2,
            self.sc.get_height() - self.game_over_text_render.get_height() * 1.5
        ))

    def draw_field(self, x0, y0, field, marks=None, is_hide=False):
        w, h = field.shape

        if is_hide:
            pygame.draw.rect(self.sc, (25, 25, 25), (x0, y0, w * self.cell_size, h * self.cell_size,))
            self.draw_grid(x0, y0, w, h)
            return

        for y in range(h):
            for x in range(w):
                cell = field[x, y]
                if cell not in self.color_by_cell: raise Exception(f"для клетки {cell} не задан цвет")
                color = self.color_by_cell[cell]
                if color is None: continue

                pygame.draw.rect(self.sc, color, (x0 + x * self.cell_size,
                                                  y0 + y * self.cell_size,
                                                  self.cell_size,
                                                  self.cell_size,
                                                  ))
        if marks is not None:
            for y in range(h):
                for x in range(w):
                    if not marks[x, y]: continue
                    self.sc.blit(self.mark_sprite, (x0 + x * self.cell_size, y0 + y * self.cell_size))

        self.draw_grid(x0, y0, w, h)

    def draw_grid(self, x0, y0, n_cells_horisontal, n_cells_vertical):
        x1 = x0 + n_cells_horisontal * self.cell_size
        y1 = y0 + n_cells_vertical * self.cell_size
        for i_vert in range(n_cells_vertical + 1):
            for i_hor in range(n_cells_horisontal + 1):
                x = x0 + i_hor * self.cell_size
                y = y0 + i_vert * self.cell_size

                pygame.draw.line(self.sc, (255, 255, 255), (x0, y), (x1, y))
                pygame.draw.line(self.sc, (255, 255, 255), (x, y0), (x, y1))

    def draw_animations(self):
        for anim in self.animations:
            anim: Animation
            frame = anim.get_current_frame()
            if frame is None: continue
            self.sc.blit(frame, (anim.x, anim.y))

    def get_top_left_corners(self):
        w1, h1 = map(lambda x: x * self.cell_size, self.game.players[0].my_field.shape)
        w2, h2 = map(lambda x: x * self.cell_size, self.game.players[1].my_field.shape)

        margin_horisontal = (SC_W - w1 - w2) / 3
        margin_vertical1 = (SC_H - h1) / 2
        margin_vertical2 = (SC_H - h2) / 2

        p1 = (margin_horisontal, margin_vertical1)
        p2 = (margin_horisontal * 2 + w1, margin_vertical2)

        return p1, p2

    def draw_splash(self):
        self.sc.blit(self.transfer_text2, (0, 0))


def main():
    pygame.init()
    sc = pygame.display.set_mode((SC_W, SC_H))
    pygame.display.set_caption('v0.3')
    clock = pygame.time.Clock()

    sc_controller = ScreensController(sc, clock)
    settings = sc_controller.mainloop()

    game = Game(settings)
    gui = Gui(sc, clock, game)
    gui.mainloop()


if __name__ == '__main__':
    main()


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
