import time
from abc import ABC, abstractmethod

import pygame

from settings import DEFAULT_FONT, WHITE


class IDrawedOnScreen(ABC):
    @abstractmethod
    def draw(self, sc: pygame.Surface):
        pass


class IEventProcessed(ABC):
    @abstractmethod
    def process_events(self, events, mouce_pressed, keys_pressed):
        pass


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

    def swap_axes(self):
        self.n_cells_horisontal, self.n_cells_vertical = self.n_cells_vertical, self.n_cells_horisontal

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

    def get_sc_crd(self, cell_x, cell_y):
        """
        :return: координаты клетки на экране по координатам на поле противника
        """
        x0, y0 = self.top_left_corner()
        return (x0 + cell_x * self.cell_size,
                y0 + cell_y * self.cell_size,)