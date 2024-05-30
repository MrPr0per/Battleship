import datetime
import random
import time

import numpy as np

from settings import *
import pygame
from main import Player, MyFildCells, OpponentCells, Ship
from enum import Enum, auto

from abc import ABC, abstractmethod


# нужно сделать окна:
# 1.
#   - выбор левого, правого игрока из (чел, тупой аи, умный аи)
# 2.
#   - Параметризация поля (размеры, типы и количество кораблей)
#   - расстановка кораблей
#   - Угловые корабли
# 3.
#   - выбор времени для каждого игрока (в т.ч. бесконечное)
#   Игра на время (в режиме hot seat)
#
#
# + предустановленные параметры, чтобы прокликать "далее"

class IDrawedOnScreen(ABC):
    @abstractmethod
    def draw(self, sc: pygame.Surface):
        pass


class IEventProcessed(ABC):
    @abstractmethod
    def process_events(self, events, mouce_pressed, keys_pressed):
        pass


class RenderedTextHolder:
    def __init__(self, font=DEFAULT_FONT_NAME, color=(255, 255, 255), font_size=DEFAULT_FONT_SIZE):
        self.renders = {}
        if isinstance(font, str):
            self.font = pygame.font.SysFont(font, font_size)
        elif isinstance(font, pygame.font.Font):
            self.font = font
        else:
            raise TypeError()
        self.color = color

    def __getitem__(self, string) -> pygame.Surface:
        if string not in self.renders:
            self.renders[string] = self.font.render(string, True, self.color)
        return self.renders[string]


class Button(IDrawedOnScreen, IEventProcessed):
    def __init__(self, x, y, w, h, text, bg_color, is_sticky=False, other_buttons=None):
        """
        :param text - отрендеренный текст или строка
        :param is_sticky: будет ли кнопка отсаваться нажатой после клика
        :param other_buttons: другие кнопки, которые отожмутся при нажатии на эту 
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        if isinstance(text, str):
            text = DEFAULT_FONT.render(text, True, WHITE)
        if not isinstance(text, pygame.Surface): raise TypeError()

        self.text_surface = text
        self.bg_color = bg_color

        self.is_hower = False
        self.is_pressed = False
        self.is_click_processed = True
        self.time_of_click = None
        self.time_of_last_pressed_update = None

        self.is_sticky = is_sticky
        self.other_buttons = other_buttons

    # @classmethod
    # def simple_init(cls, x, y, w, h, text, font=None, bg_color=RED, text_color=WHITE,
    #                 is_sticky=False, other_buttons=None):
    #     if font is None:
    #         font = DEFAULT_FONT
    #     return Button(x, y, w, h, font.render(text, True, text_color), bg_color, is_sticky, other_buttons)

    def is_clicked(self):
        if self.is_click_processed: return False
        self.is_click_processed = True
        return True

    def is_long_pressed(self):
        t = time.time()
        if not self.is_pressed: return False
        if t - self.time_of_click < 0.2: return False
        if self.time_of_last_pressed_update is not None and t - self.time_of_last_pressed_update < 1 / 12: return False
        self.time_of_last_pressed_update = t
        return True

    def process_events(self, events, mouce_pressed, keys_pressed):
        x, y = pygame.mouse.get_pos()
        is_mouce_pressed = any(mouce_pressed)

        self.is_hower = self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

        if not self.is_sticky:
            if not is_mouce_pressed: self.is_pressed = False

        if not self.is_hower: return

        for e in events:
            e: pygame.event.Event
            if e.type == pygame.MOUSEBUTTONDOWN:
                self.is_pressed = True
                self.is_click_processed = False
                self.time_of_click = time.time()

                if self.other_buttons is not None:
                    for b in self.other_buttons:
                        b: 'Button'
                        b.is_pressed = False

    def draw(self, sc: pygame.Surface):
        color = self.bg_color
        if self.is_pressed:
            color = [i * 0.5 for i in color]
        elif self.is_hower:
            color = [i * 0.7 for i in color]

        pygame.draw.rect(sc, color, (self.x, self.y, self.w, self.h), border_radius=3)

        sc.blit(self.text_surface, (
            self.x + self.w / 2 - self.text_surface.get_width() / 2,
            self.y + self.h / 2 - self.text_surface.get_height() / 2
        ))

    def set_pos(self, new_x, new_y):
        self.x = new_x
        self.y = new_y


class Label(IDrawedOnScreen):
    def __init__(self, center_x, center_y, text, font: pygame.font.Font, color=WHITE):
        self.center_x = center_x
        self.center_y = center_y
        self.font = font
        self.color = color

        self.render = font.render(text, True, color)

    def w(self):
        return self.render.get_width()

    def h(self):
        return self.render.get_height()

    def draw(self, sc: pygame.Surface):
        sc.blit(self.render, (self.center_x - self.render.get_width() / 2,
                              self.center_y - self.render.get_height() / 2))

    def change_text(self, new_text):
        self.render = self.font.render(new_text, True, self.color)


class SettingsScreen(IEventProcessed):
    def __init__(self, sc, settings):
        self.settings = settings

        self.font_size = 24
        self.button_h = 32
        self.font_renders_holder = RenderedTextHolder(pygame.font.SysFont('Lucida Console', self.font_size))
        self.sc = sc

        next_button_w = self.sc.get_width() / 10
        # next_button_h = 32
        self.next_button = Button(self.sc.get_width() * 19 / 20 - next_button_w, self.sc.get_height() * 9 / 10,
                                  next_button_w, self.button_h, self.font_renders_holder['next'], (100, 200, 100))

    def draw(self):
        self.next_button.draw(self.sc)

    def process_events(self, events, mouce_pressed, keys_pressed):
        self.next_button.process_events(events, mouce_pressed, keys_pressed)


class ChoosePlayersScreen(SettingsScreen):
    def __init__(self, sc: pygame.Surface, settings: 'Settings'):
        super().__init__(sc, settings)

        w, h = sc.get_size()
        column_width = w / 3

        button_width = column_width
        button_height = 32

        self.left_buttons = [
            Button(w / 4 - column_width / 2, h / 2 + 0 * button_height * 1.25, button_width, button_height,
                   self.font_renders_holder['human'], (200, 100, 100), True),
            Button(w / 4 - column_width / 2, h / 2 + 1 * button_height * 1.25, button_width, button_height,
                   self.font_renders_holder['random AI'], (200, 100, 100), True),
            Button(w / 4 - column_width / 2, h / 2 + 2 * button_height * 1.25, button_width, button_height,
                   self.font_renders_holder['smart AI'], (200, 100, 100), True),
        ]
        self.right_buttons = [
            Button(w * 3 / 4 - column_width / 2, h / 2 + 0 * button_height * 1.25, button_width, button_height,
                   self.font_renders_holder['human'], (200, 100, 100), True),
            Button(w * 3 / 4 - column_width / 2, h / 2 + 1 * button_height * 1.25, button_width, button_height,
                   self.font_renders_holder['random AI'], (200, 100, 100), True),
            Button(w * 3 / 4 - column_width / 2, h / 2 + 2 * button_height * 1.25, button_width, button_height,
                   self.font_renders_holder['smart AI'], (200, 100, 100), True),
        ]

        self.left_buttons[0].is_pressed = True
        self.right_buttons[0].is_pressed = True

        for i in range(3):
            self.left_buttons[i].other_buttons = [self.left_buttons[j] for j in range(3) if j != i]
            self.right_buttons[i].other_buttons = [self.right_buttons[j] for j in range(3) if j != i]

        # 
        # self.column_width = w / 3

        # self.p1 = (w / 4 - self.column_width / 2, h / 8)
        # self.p2 = (w * 3 / 4 - self.column_width / 2, h / 8)

    def draw(self):
        super().draw()

        player1_surf = self.font_renders_holder['player 1:']
        self.sc.blit(player1_surf, (self.sc.get_width() / 4 - player1_surf.get_width() / 2, self.sc.get_height() / 4))

        player2_surf = self.font_renders_holder['player 2:']
        self.sc.blit(player2_surf,
                     (self.sc.get_width() * 3 / 4 - player2_surf.get_width() / 2, self.sc.get_height() / 4))

        for b in self.left_buttons:
            b.draw(self.sc)
        for b in self.right_buttons:
            b.draw(self.sc)

    def process_events(self, events, mouce_pressed, keys_pressed):
        super().process_events(events, mouce_pressed, keys_pressed)

        for b in self.left_buttons:
            b.process_events(events, mouce_pressed, keys_pressed)
        for b in self.right_buttons:
            b.process_events(events, mouce_pressed, keys_pressed)

        for i, b in enumerate(self.left_buttons):
            if b.is_pressed:
                if i == 0: self.settings.left_settings.player_identity = PlayerIdentity.human
                if i == 1: self.settings.left_settings.player_identity = PlayerIdentity.randomAI
                if i == 2: self.settings.left_settings.player_identity = PlayerIdentity.smartAI
                break

        for i, b in enumerate(self.right_buttons):
            if b.is_pressed:
                if i == 0: self.settings.right_settings.player_identity = PlayerIdentity.human
                if i == 1: self.settings.right_settings.player_identity = PlayerIdentity.randomAI
                if i == 2: self.settings.right_settings.player_identity = PlayerIdentity.smartAI
                break

    # def update_settings(self):


# region ChooseTimeScreen
class ClockSettingsPanel(IEventProcessed):

    def __init__(self, player_settings: 'PlayerSettings', center_x, center_y):
        self.player_settings = player_settings

        # buttons_font = pygame.font.SysFont(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)
        # self.label_font_holder = RenderedTextHolder(font_size=DEFAULT_FONT_SIZE * 2)
        label_font = pygame.font.SysFont(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE * 2)
        self.time_label = Label(center_x, center_y, self.get_clock_string(), label_font)

        # time_surface = label_font.render(self.get_clock_string(), True, WHITE)
        # time_surface = self.label_font_holder[self.get_clock_string()]
        plus_surface = DEFAULT_FONT.render('▲', True, WHITE)
        minus_surface = DEFAULT_FONT.render('▼', True, WHITE)

        # label_w, label_h = time_surface.get_size()
        # self.label_x, self.label_y = center_x - label_w / 2, center_y - label_h / 2

        buttons_size = 32
        buttons_margin = 32

        self.button_m_plus = Button(
            center_x - self.time_label.w() / 4 - buttons_size / 2,
            center_y - self.time_label.h() / 2 - buttons_margin - buttons_size,
            buttons_size, buttons_size, plus_surface, GREEN)
        self.button_m_minus = Button(
            center_x - self.time_label.w() / 4 - buttons_size / 2,
            center_y + self.time_label.h() / 2 + buttons_margin,
            buttons_size, buttons_size, minus_surface, RED)
        self.button_s_plus = Button(
            center_x + self.time_label.w() / 4 - buttons_size / 2,
            center_y - self.time_label.h() / 2 - buttons_margin - buttons_size,
            buttons_size, buttons_size, plus_surface, GREEN)
        self.button_s_minus = Button(
            center_x + self.time_label.w() / 4 - buttons_size / 2,
            center_y + self.time_label.h() / 2 + buttons_margin,
            buttons_size, buttons_size, minus_surface, RED)

    def get_clock_string(self):
        total_seconds = self.player_settings.time_to_game.seconds
        return f'{total_seconds // 60}:{total_seconds % 60:0>2}'

    def draw(self, sc):
        self.time_label.draw(sc)
        self.button_m_plus.draw(sc)
        self.button_m_minus.draw(sc)
        self.button_s_plus.draw(sc)
        self.button_s_minus.draw(sc)

    def process_events(self, events, mouce_pressed, keys_pressed):
        self.button_m_plus.process_events(events, mouce_pressed, keys_pressed)
        self.button_m_minus.process_events(events, mouce_pressed, keys_pressed)
        self.button_s_plus.process_events(events, mouce_pressed, keys_pressed)
        self.button_s_minus.process_events(events, mouce_pressed, keys_pressed)

        is_clock_changed = False
        if self.button_m_plus.is_clicked() or self.button_m_plus.is_long_pressed():
            self.player_settings.time_to_game += datetime.timedelta(minutes=1)
            is_clock_changed = True
        if self.button_m_minus.is_clicked() or self.button_m_minus.is_long_pressed():
            if self.player_settings.time_to_game >= datetime.timedelta(minutes=1):
                self.player_settings.time_to_game -= datetime.timedelta(minutes=1)
                is_clock_changed = True
        if self.button_s_plus.is_clicked() or self.button_s_plus.is_long_pressed():
            self.player_settings.time_to_game += datetime.timedelta(seconds=1)
            is_clock_changed = True
        if self.button_s_minus.is_clicked() or self.button_s_minus.is_long_pressed():
            if self.player_settings.time_to_game >= datetime.timedelta(seconds=1):
                self.player_settings.time_to_game -= datetime.timedelta(seconds=1)
                is_clock_changed = True

        if is_clock_changed:
            # self.player_settings.time_to_game = max(self.player_settings.time_to_game, datetime.timedelta(0))
            self.time_label.change_text(self.get_clock_string())


class ChooseTimeScreen(SettingsScreen):
    def __init__(self, sc, settings: 'Settings'):
        super().__init__(sc, settings)

        w, h = sc.get_size()
        self.left_time_panel = ClockSettingsPanel(settings.left_settings, w / 2 - w / 4, h / 2)
        self.right_time_panel = ClockSettingsPanel(settings.right_settings, w / 2 + w / 4, h / 2)

    def draw(self):
        super().draw()

        player1_surf = self.font_renders_holder[f'1: {self.settings.left_settings.player_identity.name}']
        player2_surf = self.font_renders_holder[f'2: {self.settings.right_settings.player_identity.name}']
        self.sc.blit(player1_surf,
                     (self.sc.get_width() / 4 - player1_surf.get_width() / 2, self.sc.get_height() / 4))
        self.sc.blit(player2_surf,
                     (self.sc.get_width() * 3 / 4 - player2_surf.get_width() / 2, self.sc.get_height() / 4))

        self.left_time_panel.draw(self.sc)
        self.right_time_panel.draw(self.sc)

    def process_events(self, events, mouce_pressed, keys_pressed):
        super().process_events(events, mouce_pressed, keys_pressed)
        self.left_time_panel.process_events(events, mouce_pressed, keys_pressed)
        self.right_time_panel.process_events(events, mouce_pressed, keys_pressed)

        # for b in self.left_buttons:
        #     b.process_events(events, mouce_pressed, keys_pressed)
        # for b in self.right_buttons:
        #     b.process_events(events, mouce_pressed, keys_pressed)

    # def update_settings(self):
    #     pass
    # for i, b in enumerate(self.left_buttons):
    #     if b.is_pressed:
    #         if i == 0: settings.left_settings.player_identity = PlayerIdentity.human
    #         if i == 1: settings.left_settings.player_identity = PlayerIdentity.randomAI
    #         if i == 2: settings.left_settings.player_identity = PlayerIdentity.smartAI
    #         break
    #
    # for i, b in enumerate(self.right_buttons):
    #     if b.is_pressed:
    #         if i == 0: settings.right_settings.player_identity = PlayerIdentity.human
    #         if i == 1: settings.right_settings.player_identity = PlayerIdentity.randomAI
    #         if i == 2: settings.right_settings.player_identity = PlayerIdentity.smartAI
    #         break


# endregion

# region SetShipsScreen

class Grid(IDrawedOnScreen):
    def __init__(self, center_x, center_y, n_cells_horisontal, n_cells_vertical, cell_size, bg_color=None,
                 grid_color=WHITE):
        self.center_x = center_x
        self.center_y = center_y
        self.n_cells_horisontal = n_cells_horisontal
        self.n_cells_vertical = n_cells_vertical
        self.cell_size = cell_size
        self.bg_color = bg_color
        self.grid_color = grid_color

    def set_size(self, new_size):
        self.n_cells_horisontal, self.n_cells_vertical = new_size

    def w(self):
        return self.n_cells_horisontal * self.cell_size

    def h(self):
        return self.n_cells_vertical * self.cell_size

    def top_left_corner(self):
        return self.center_x - self.w() / 2, self.center_y - self.h() / 2

    def draw(self, sc: pygame.Surface):
        x0 = self.center_x - self.w() / 2
        y0 = self.center_y - self.h() / 2
        x1 = x0 + self.n_cells_horisontal * self.cell_size
        y1 = y0 + self.n_cells_vertical * self.cell_size

        if self.bg_color is not None:
            pygame.draw.rect(sc, self.bg_color, (x0, y0, self.w(), self.h()))

        for i_vert in range(self.n_cells_vertical + 1):
            for i_hor in range(self.n_cells_horisontal + 1):
                x = x0 + i_hor * self.cell_size
                y = y0 + i_vert * self.cell_size

                pygame.draw.line(sc, self.grid_color, (x0, y), (x1, y))
                pygame.draw.line(sc, self.grid_color, (x, y0), (x, y1))

    def get_field_crd(self, mouse_x, mouse_y):
        """
        :return: координаты на поле противника
        """
        topleft_x, topleft_y = self.top_left_corner()
        x, y = mouse_x - topleft_x, mouse_y - topleft_y
        x //= self.cell_size
        y //= self.cell_size
        return int(x), int(y)

class FieldSettingsPanel(IDrawedOnScreen, IEventProcessed):
    def __init__(self, player_settings: 'PlayerSettings', center_x, center_y, cell_size, is_left=True):
        self.player_settings = player_settings
        self.cell_size = cell_size
        self.is_left = is_left
        self.center_x = center_x
        self.center_y = center_y

        self.grid = Grid(center_x, center_y, *self.player_settings.field_size, self.cell_size)

        if is_left:
            side_button_x = center_x - self.grid.w() / 2 - DEFAULT_BUTTON_MARGIN - DEFAULT_BUTTON_SIZE
        else:
            side_button_x = center_x + self.grid.w() / 2 + DEFAULT_BUTTON_MARGIN

        arrow_up = DEFAULT_FONT.render('▲', True, WHITE)
        arrow_down = pygame.transform.rotate(arrow_up, 180)
        arrow_left = pygame.transform.rotate(arrow_up, 90)
        arrow_right = pygame.transform.rotate(arrow_up, 270)

        self.button_h_inc = Button(side_button_x, center_y - DEFAULT_BUTTON_MARGIN / 2 - DEFAULT_BUTTON_SIZE,
                                   DEFAULT_BUTTON_SIZE, DEFAULT_BUTTON_SIZE, arrow_up, GREY)
        self.button_h_dec = Button(side_button_x, center_y + DEFAULT_BUTTON_MARGIN / 2,
                                   DEFAULT_BUTTON_SIZE, DEFAULT_BUTTON_SIZE, arrow_down, GREY)
        self.button_w_dec = Button(center_x - DEFAULT_BUTTON_MARGIN / 2 - DEFAULT_BUTTON_SIZE,
                                   center_y + self.grid.h() / 2 + DEFAULT_BUTTON_MARGIN,
                                   DEFAULT_BUTTON_SIZE, DEFAULT_BUTTON_SIZE, arrow_left, GREY)
        self.button_w_inc = Button(center_x + DEFAULT_BUTTON_MARGIN / 2,
                                   center_y + self.grid.h() / 2 + DEFAULT_BUTTON_MARGIN,
                                   DEFAULT_BUTTON_SIZE, DEFAULT_BUTTON_SIZE, arrow_right, GREY)
        self.buttons = [self.button_h_inc,
                        self.button_h_dec,
                        self.button_w_dec,
                        self.button_w_inc]

    def update_buttons_crds(self):
        if self.is_left:
            side_button_x = self.center_x - self.grid.w() / 2 - DEFAULT_BUTTON_MARGIN - DEFAULT_BUTTON_SIZE
        else:
            side_button_x = self.center_x + self.grid.w() / 2 + DEFAULT_BUTTON_MARGIN

        self.button_h_inc.set_pos(side_button_x,
                                  self.center_y - DEFAULT_BUTTON_MARGIN / 2 - DEFAULT_BUTTON_SIZE)

        self.button_h_dec.set_pos(side_button_x,
                                  self.center_y + DEFAULT_BUTTON_MARGIN / 2)

        self.button_w_dec.set_pos(self.center_x - DEFAULT_BUTTON_MARGIN / 2 - DEFAULT_BUTTON_SIZE,
                                  self.center_y + self.grid.h() / 2 + DEFAULT_BUTTON_MARGIN)

        self.button_w_inc.set_pos(self.center_x + DEFAULT_BUTTON_MARGIN / 2,
                                  self.center_y + self.grid.h() / 2 + DEFAULT_BUTTON_MARGIN)

    def process_events(self, events, mouce_pressed, keys_pressed):
        for b in self.buttons:
            b.process_events(events, mouce_pressed, keys_pressed)

        if self.button_w_inc.is_clicked():
            self.player_settings.field_size[0] += 1
        if self.button_w_dec.is_clicked():
            self.player_settings.field_size[0] -= 1
        if self.button_h_inc.is_clicked():
            self.player_settings.field_size[1] += 1
        if self.button_h_dec.is_clicked():
            self.player_settings.field_size[1] -= 1

        self.player_settings.field_size[0] = max(self.player_settings.field_size[0], 1)
        self.player_settings.field_size[1] = max(self.player_settings.field_size[1], 1)

        self.grid.set_size(self.player_settings.field_size)
        self.update_buttons_crds()

    def draw(self, sc: pygame.Surface):
        self.grid.draw(sc)
        for b in self.buttons:
            b.draw(sc)


class ShipCountPanel(IDrawedOnScreen, IEventProcessed):
    def __init__(self, ship_size, player_settings: 'PlayerSettings', top_side_point, cell_size, ):
        self.player_settings = player_settings
        self.ship_size = ship_size
        self.unset_count = self.player_settings.ships_count[self.ship_size]

        x0, y0 = top_side_point
        self.button_dec = Button(x0, y0, cell_size, cell_size, '-', GREY)
        self.button_inc = Button(x0 + cell_size * 1.2, y0, cell_size, cell_size, '+', GREY)
        self.label = Label(x0 + cell_size * (2.2 + 1.5), y0 + cell_size / 2, self.get_str(),
                           pygame.font.SysFont(DEFAULT_FONT_NAME, int(cell_size * 0.6)))
        self.ship_grid = Grid(x0 + cell_size * (2.2 + 3) + cell_size * self.ship_size / 2,
                              y0 + cell_size / 2, self.ship_size, 1, cell_size, RED)

        self.picking_up_crd = None
        self.put_down_crd = None

        self.picked_ship = Grid(0, 0, ship_size, 1, cell_size + 1, BRIGHT_RED)
    def get_str(self):
        return f'{self.unset_count}/{self.player_settings.ships_count[self.ship_size]}'

    def process_events(self, events, mouce_pressed, keys_pressed):
        self.button_dec.process_events(events, mouce_pressed, keys_pressed)
        self.button_inc.process_events(events, mouce_pressed, keys_pressed)

        if self.button_dec.is_clicked():
            self.player_settings.ships_count[self.ship_size] -= 1
            if self.player_settings.ships_count[self.ship_size] < 0:
                self.player_settings.ships_count[self.ship_size] = 0
            self.label.change_text(self.get_str())
        if self.button_inc.is_clicked():
            self.player_settings.ships_count[self.ship_size] += 1
            self.label.change_text(self.get_str())

        mx, my = pygame.mouse.get_pos()
        # self.current_mouce_crd = (mx, my)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.ship_grid.center_x - self.ship_grid.w() / 2 <= mx <= self.ship_grid.center_x + self.ship_grid.w() / 2:
                    if self.ship_grid.center_y - self.ship_grid.h() / 2 <= my <= self.ship_grid.center_y + self.ship_grid.h() / 2:
                        self.picking_up_crd = (mx, my)
        if self.picking_up_crd is not None and not any(mouce_pressed):
            self.picking_up_crd = None
            self.put_down_crd = (mx, my)

    def draw(self, sc: pygame.Surface):
        self.button_dec.draw(sc)
        self.button_inc.draw(sc)
        self.label.draw(sc)
        self.ship_grid.draw(sc)


class ShipsPanel(IDrawedOnScreen, IEventProcessed):
    def __init__(self, player_settings: 'PlayerSettings', top_side_point, cell_size, is_left, ):
        # for k in player_settings.ships_count.keys():

        x0, y0 = top_side_point
        interligne = 1.2
        self.ship_panels = {}
        for i in range(4):
            self.ship_panels[4 - i] = ShipCountPanel(4 - i, player_settings,
                                                     (x0, y0 + i * cell_size * interligne), cell_size)
        # self.x4_ship_count = ShipCountPanel(4, player_settings, (x0, y0 + 0 * cell_size * interligne), cell_size)
        # self.x3_ship_count = ShipCountPanel(3, player_settings, (x0, y0 + 1 * cell_size * interligne), cell_size)
        # self.x2_ship_count = ShipCountPanel(2, player_settings, (x0, y0 + 2 * cell_size * interligne), cell_size)
        # self.x1_ship_count = ShipCountPanel(1, player_settings, (x0, y0 + 3 * cell_size * interligne), cell_size)

    def process_events(self, events, mouce_pressed, keys_pressed):
        for p in self.ship_panels.values():
            p.process_events(events, mouce_pressed, keys_pressed)
        # self.x4_ship_count.process_events(events, mouce_pressed, keys_pressed)
        # self.x3_ship_count.process_events(events, mouce_pressed, keys_pressed)
        # self.x2_ship_count.process_events(events, mouce_pressed, keys_pressed)
        # self.x1_ship_count.process_events(events, mouce_pressed, keys_pressed)

    def draw(self, sc: pygame.Surface):
        for p in self.ship_panels.values():
            p.draw(sc)


class ShipPickingController(IEventProcessed, IDrawedOnScreen):
    """осуществляет перетаскивание кораблей из нижней панели на сетку"""

    def __init__(self, field_panel: FieldSettingsPanel, ships_panel: ShipsPanel):
        self.field_panel = field_panel
        self.ships_panel = ships_panel

    def draw(self, sc: pygame.Surface):
        mx, my = pygame.mouse.get_pos()
        for p in self.ships_panel.ship_panels.values():
            if p.picking_up_crd is not None:
                delta_x = mx - p.picking_up_crd[0]
                delta_y = my - p.picking_up_crd[1]
                p.picked_ship.center_x = p.ship_grid.center_x + delta_x
                p.picked_ship.center_y = p.ship_grid.center_y + delta_y
                p.picked_ship.draw(sc)

            if p.put_down_crd is not None:

                p.put_down_crd = None


    def process_events(self, events, mouce_pressed, keys_pressed):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    ...


class SetShipsScreen(SettingsScreen):
    def __init__(self, sc, settings):
        super().__init__(sc, settings)

        w, h = sc.get_size()
        cell_size = 30

        self.left_field_panel = FieldSettingsPanel(settings.left_settings, w / 2 - w * 0.18, h * 0.3, cell_size,
                                                   is_left=True)
        self.right_field_panel = FieldSettingsPanel(settings.right_settings, w / 2 + w * 0.18, h * 0.3, cell_size,
                                                    is_left=False)

        self.left_ships_panel = ShipsPanel(settings.left_settings, (
            self.left_field_panel.center_x - self.left_field_panel.grid.w() / 2, h * 0.7), cell_size, True)
        self.right_ships_panel = ShipsPanel(settings.left_settings, (
            self.right_field_panel.center_x - self.right_field_panel.grid.w() / 2, h * 0.7), cell_size, False)

        self.left_ship_picking_conroller = ShipPickingController(self.left_field_panel, self.left_ships_panel)
        self.right_ship_picking_conroller = ShipPickingController(self.right_field_panel, self.right_ships_panel)

    def process_events(self, events, mouce_pressed, keys_pressed):
        super().process_events(events, mouce_pressed, keys_pressed)
        self.left_field_panel.process_events(events, mouce_pressed, keys_pressed)
        self.right_field_panel.process_events(events, mouce_pressed, keys_pressed)
        self.left_ships_panel.process_events(events, mouce_pressed, keys_pressed)
        self.right_ships_panel.process_events(events, mouce_pressed, keys_pressed)

    def draw(self):
        super().draw()
        self.left_field_panel.draw(self.sc)
        self.right_field_panel.draw(self.sc)
        self.left_ships_panel.draw(self.sc)
        self.right_ships_panel.draw(self.sc)
        self.left_ship_picking_conroller.draw(self.sc)
        self.right_ship_picking_conroller.draw(self.sc)


# endregion

class PlayerIdentity(Enum):
    human = auto()
    randomAI = auto()
    smartAI = auto()


class PlayerSettings:
    def __init__(self):
        self.player_identity = PlayerIdentity.human

        self.time_to_game = datetime.timedelta(minutes=10)

        # self.field_size = (10, 10)
        # self.ships = []

        self.field_size = [10, 10]
        self.ships_count = DEFAULT_SHIPS_COUNT.copy()
        self.ships: list[Ship] = []


class Settings:
    def __init__(self):
        self.left_settings = PlayerSettings()
        self.right_settings = PlayerSettings()


class ScreensController:
    def __init__(self, sc, clock):
        self.settings = Settings()

        self.screens = [
            ChoosePlayersScreen(sc, self.settings),
            ChooseTimeScreen(sc, self.settings),
            SetShipsScreen(sc, self.settings)
        ]
        self.current_screen_index = 0

        self.sc = sc
        self.clock = clock

        self.all_fields_is_filled = False

    def get_current_screen(self):
        return self.screens[self.current_screen_index]

    def process_events(self, events, mouce_pressed, keys_pressed):
        def quit_game():
            pygame.quit()
            quit()

        for event in events:
            if event.type == pygame.QUIT: quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: quit_game()

    def mainloop(self):
        # отрисовывает и считывает данные с экранов
        # по завершении возвращает объект со всеми собранными данными

        while True:
            events = pygame.event.get()
            mouce_pressed = pygame.mouse.get_pressed()
            keys_pressed = pygame.key.get_pressed()

            current_screen = self.get_current_screen()

            self.process_events(events, mouce_pressed, keys_pressed)
            current_screen.process_events(events, mouce_pressed, keys_pressed)

            # current_screen.update_settings()

            self.update()

            if self.all_fields_is_filled: return self.settings

            self.sc.fill((0, 0, 0))
            current_screen.draw()

            pygame.display.update()
            self.clock.tick(FPS)

    def update(self):
        if self.get_current_screen().next_button.is_pressed:
            self.current_screen_index += 1

        if self.current_screen_index >= len(self.screens):
            self.all_fields_is_filled = True


def main():
    pygame.init()
    sc = pygame.display.set_mode((SC_W, SC_H))
    pygame.display.set_caption('v0.3')
    clock = pygame.time.Clock()

    sc_controller = ScreensController(sc, clock)
    settings = sc_controller.mainloop()

    print(settings)


if __name__ == '__main__':
    main()
