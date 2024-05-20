import time

import pygame
import os

class Animation:
    animations = {}
    
    def __init__(self, x, y, animation_name, fps=24, ):
        """
        :param animation_name: имя папки с анимацией в /sprites/
        """
        if len(self.animations) == 0:
            self.load_animations()

        self.x = x
        self.y = y
        self.fps = fps
        if animation_name == 'BULK': self.fps = 10
        self.animation_name = animation_name

        # self.t0 = None  # время начала анимации
        self.t0 = time.time()  # время начала анимации

    def start(self):
        self.t0 = time.time()

    def get_current_frame(self):
        """
        :return: если анимация кончилась, вернет None
        """
        if self.t0 is None: raise Exception('попытка получить кадр из незапущеной анимации')
        dt = time.time() - self.t0
        frame_index = int(dt * self.fps)
        if frame_index >= len(self.animations[self.animation_name]):
            return None
        return self.animations[self.animation_name][frame_index]

    def is_over(self):
        return self.get_current_frame() is None

    @classmethod
    def load_animations(cls):
        anim_folders = next(os.walk('sprites'))[1]
        for name in anim_folders:
            frame_names = cls.get_frames_names(os.path.join('sprites', name, 'frames'))
            cls.animations[name] = [pygame.image.load(filename) for filename in frame_names]

    @classmethod
    def get_frames_names(cls, folder):
        def get_frame_number(filename: str) -> int:
            filename = filename[:filename.rfind('.')]  # обрезаем расширение
            for i in range(len(filename) - 1, -1, -1):
                if not filename[i].isdigit():
                    return int(filename[i + 1:])
            raise Exception(f'не удалось считать номер с конца имени файла кадра: {filename}')

        def main_():
            filenames = next(os.walk(folder))[2]
            filenames.sort(key=lambda name: get_frame_number(name))
            return [os.path.join(folder, filename) for filename in filenames]

        return main_()
    
    # @classmethod
    # def update_anims(cls, animations:set):
    #     for anim in animations:
    #         

def main():
    Animation.load_animations()


if __name__ == '__main__':
    main()
