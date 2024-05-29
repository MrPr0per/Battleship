import datetime
import random

import numpy as np

from settings import *
import pygame
from main import Player, MyFildCells, OpponentCells
from enum import Enum, auto


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


class Button:
    def __init__(self, x, y, w, h, text_surface, color, is_sticky=False, other_buttons=None):
        """
        :param is_sticky: будет ли кнопка отсаваться нажатой после клика
        :param other_buttons: другие кнопки, которые отожмутся при нажатии на эту 
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.text_surface = text_surface
        self.color = color

        self.is_hower = False
        self.is_pressed = False

        self.is_sticky = is_sticky
        self.other_buttons = other_buttons

    def process_events(self, events, mouce_pressed, keys_pressed):
        x, y = pygame.mouse.get_pos()
        is_pressed = any(mouce_pressed)

        self.is_hower = self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

        if not self.is_sticky:
            if not is_pressed: self.is_pressed = False

        for e in events:
            e: pygame.event.Event
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.is_hower:
                    self.is_pressed = True

                    if self.other_buttons is not None:
                        for b in self.other_buttons:
                            b: 'Button'
                            b.is_pressed = False

    def draw(self, sc: pygame.Surface):
        color = self.color
        if self.is_pressed:
            color = [i * 0.45 for i in color]
        elif self.is_hower:
            color = [i * 0.7 for i in color]

        pygame.draw.rect(sc, color, (self.x, self.y, self.w, self.h), border_radius=3)

        sc.blit(self.text_surface, (
            self.x + self.w / 2 - self.text_surface.get_width() / 2,
            self.y + self.h / 2 - self.text_surface.get_height() / 2
        ))


class SettingsScreen:
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

    def update_settings(self):
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


class SetShipsScreen(SettingsScreen):
    pass


class ClockSettings:
    def __init__(self, player_settings:'PlayerSettings', center_x, center_y):
        self.player_settings = player_settings

        render_holder_for_buttons = RenderedTextHolder()
        lael_font = pygame.font.SysFont(DEFAULT_FONT_NAME, 48)

        

        self.button_m_plus = Button()

    def get_clock_string(self):
        total_seconds = self.player_settings.time_to_game.seconds
        return f'{total_seconds // 60}:{total_seconds % 60}'
        
class ChooseTimeScreen(SettingsScreen):
    def __init__(self, sc, settings: 'Settings'):
        super().__init__(sc, settings)

        self.

    def draw(self):
        super().draw()

        player1_surf = self.font_renders_holder[f'1: {self.settings.left_settings.player_identity.name}']
        player2_surf = self.font_renders_holder[f'2: {self.settings.right_settings.player_identity.name}']
        self.sc.blit(player1_surf,
                     (self.sc.get_width() / 4 - player1_surf.get_width() / 2, self.sc.get_height() / 4))
        self.sc.blit(player2_surf,
                     (self.sc.get_width() * 3 / 4 - player2_surf.get_width() / 2, self.sc.get_height() / 4))

    def process_events(self, events, mouce_pressed, keys_pressed):
        super().process_events(events, mouce_pressed, keys_pressed)

        for b in self.left_buttons:
            b.process_events(events, mouce_pressed, keys_pressed)
        for b in self.right_buttons:
            b.process_events(events, mouce_pressed, keys_pressed)

    def update_settings(self, settings: 'Settings'):
        for i, b in enumerate(self.left_buttons):
            if b.is_pressed:
                if i == 0: settings.left_settings.player_identity = PlayerIdentity.human
                if i == 1: settings.left_settings.player_identity = PlayerIdentity.randomAI
                if i == 2: settings.left_settings.player_identity = PlayerIdentity.smartAI
                break

        for i, b in enumerate(self.right_buttons):
            if b.is_pressed:
                if i == 0: settings.right_settings.player_identity = PlayerIdentity.human
                if i == 1: settings.right_settings.player_identity = PlayerIdentity.randomAI
                if i == 2: settings.right_settings.player_identity = PlayerIdentity.smartAI
                break


class PlayerIdentity(Enum):
    human = auto()
    randomAI = auto()
    smartAI = auto()


class PlayerSettings:
    def __init__(self):
        self.player_identity = PlayerIdentity.human

        self.field_size = (10, 10)

        self.ships = []

        self.time_to_game = datetime.timedelta(minutes=10)


class Settings:
    def __init__(self):
        self.left_settings = PlayerSettings()
        self.right_settings = PlayerSettings()


class ScreensController:
    def __init__(self, sc, clock):
        self.settings = Settings()

        self.screens = [
            ChoosePlayersScreen(sc),
            ChooseTimeScreen(sc, self.settings),
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

            current_screen.update_settings(self.settings)

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
