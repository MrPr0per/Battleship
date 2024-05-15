from settings import *
import pygame
from main import Game


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

class Gui:
    def __init__(self, game: Game):
        pygame.init()
        self.sc = pygame.display.set_mode((SC_W, SC_H))
        pygame.display.set_caption('v0.3')
        self.clock = pygame.time.Clock()

        # self.margin_border_left = 0.1
        # self.margin_border_right = 0.1
        # self.margin_middle = 0.1
        self.cell_size = 40  # [px]

        self.game = game

    def quit(self):
        pygame.quit()
        quit()

    def process_events(self, events):
        for event in events:
            if event.type == pygame.QUIT: self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.quit()

    def mainloop(self):
        while True:
            events = pygame.event.get()
            self.process_events(events)

            self.draw_ui()

            pygame.display.update()
            self.clock.tick(FPS)

    def draw_ui(self):
        p1, p2 = self.get_top_left_corners()
        self.draw_grid(*p1, *self.game.players[0].my_field.shape)
        self.draw_grid(*p2, *self.game.players[1].my_field.shape)

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