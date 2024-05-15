from settings import *
import pygame
from main import Player, MyFildCells, OpponentCells


# todo:
# база:
#   - отображение полей в зависимости от игрока
#   - возможность кликать и взаимодействовать
#   - возможность отмечать клетки как пустые (как флажки в сапере)
#   - подсветка клетки при наведении
# фичи:
#   - взрыв/всплеск при попадании или промахе (со звуком)
#   - спрайты кораблей, фона
# 
# выстрел, видишь результат, скрываешь поле, передаешь управление
#


class Game:
    def __init__(self):
        self.players = [Player(4, 15, DEFAULT_SHIPS_COUNT), Player(6, 10, DEFAULT_SHIPS_COUNT)]
        self.players[0].set_opponent(self.players[1])
        self.players[1].set_opponent(self.players[0])
        self.current_player_index = 0

    def current_player(self):
        return self.players[self.current_player_index]

    def current_opponent(self):
        return self.players[(self.current_player_index + 1) % 2]

    def shoot(self, x, y):
        result = self.current_opponent().get_shoot(x, y)
        self.current_player().mark_shoot(x, y, result.is_success())

        if not result.is_success():
            self.current_player_index += 1
            self.current_player_index %= 2

        return result


class Gui:
    color_by_cell = {
        MyFildCells.empty: None,
        MyFildCells.intact_ship: (230, 230, 230),
        MyFildCells.missed_shot: (50, 50, 50),
        MyFildCells.destroyed_ship: (200, 100, 100),

        OpponentCells.unknown: None,
        OpponentCells.empty: (100, 100, 100),
        OpponentCells.ship: (200, 100, 100)
    }

    def __init__(self, game: Game):
        pygame.init()
        self.sc = pygame.display.set_mode((SC_W, SC_H))
        pygame.display.set_caption('v0.3')
        self.clock = pygame.time.Clock()

        self.game = game

        # self.margin_border_left = 0.1
        # self.margin_border_right = 0.1
        # self.margin_middle = 0.1
        self.cell_size = 40  # [px]

        # координаты верхеного левого угла у левого и правого полей на экране
        self.p_left, self.p_right = self.get_top_left_corners()

        self.mark_sprite = pygame.image.load('sprites/flag.png')
        # TODO: отмасштабировать спрайт, если cell_size != 40
        if self.cell_size != 40: raise Exception('отмасштабировать спрайт, если cell_size != 40')

    def get_field_crd(self, mouse_x, mouse_y):
        topleft_point = self.p_left if self.game.current_player_index == 1 else self.p_right
        x, y = mouse_x - topleft_point[0], mouse_y - topleft_point[1]
        x //= self.cell_size
        y //= self.cell_size
        return int(x), int(y)

    def process_events(self, events, mouce_pressed):

        def quit_game():
            pygame.quit()
            quit()

        for event in events:
            if event.type == pygame.QUIT: quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: quit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                x, y = self.get_field_crd(mouse_x, mouse_y)
                w, h = self.game.current_player().other_field.shape
                if not (0 <= x < w and 0 <= y < h): continue

                if event.button == 1:
                    if self.game.current_player().other_field[x, y] != OpponentCells.unknown: continue
                    self.game.shoot(x, y)
                if event.button == 3:
                    self.game.current_player().user_marks[x, y] = not self.game.current_player().user_marks[x, y]


    def mainloop(self):
        while True:
            events = pygame.event.get()
            mouce_pressed = pygame.mouse.get_pressed()
            self.process_events(events, mouce_pressed)

            self.sc.fill((0, 0, 0))
            self.draw_ui()

            pygame.display.update()
            self.clock.tick(FPS)

    def draw_ui(self):

        if self.game.current_player_index == 0:
            self.draw_field(*self.p_left, self.game.current_player().my_field)
            self.draw_field(*self.p_right, self.game.current_player().other_field,
                            self.game.current_player().user_marks)
        else:
            self.draw_field(*self.p_right, self.game.current_player().my_field)
            self.draw_field(*self.p_left, self.game.current_player().other_field, self.game.current_player().user_marks)

    def draw_field(self, x0, y0, field, marks=None):
        w, h = field.shape
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

    def get_top_left_corners(self):
        w1, h1 = map(lambda x: x * self.cell_size, self.game.players[0].my_field.shape)
        w2, h2 = map(lambda x: x * self.cell_size, self.game.players[1].my_field.shape)

        margin_horisontal = (SC_W - w1 - w2) / 3
        margin_vertical1 = (SC_H - h1) / 2
        margin_vertical2 = (SC_H - h2) / 2

        p1 = (margin_horisontal, margin_vertical1)
        p2 = (margin_horisontal * 2 + w1, margin_vertical2)

        return p1, p2


def main():
    game = Game()
    gui = Gui(game)
    gui.mainloop()


if __name__ == '__main__':
    main()
