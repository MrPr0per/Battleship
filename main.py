from gui import Game, Gui
from interface.interface_main import ScreensController
from settings import *


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
