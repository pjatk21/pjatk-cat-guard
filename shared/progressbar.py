import math


class ProgressBar:
    def __init__(self, target_size: int):
        self.progress = 0.0
        self.target_size = target_size

    def update(self, new_p: float):
        self.progress = new_p

    def __draw(self):
        done = '\N{full block}' * math.floor(self.progress * self.target_size)
        left = '\N{light shade}' * math.ceil((1 - self.progress) * self.target_size)
        return f'`[{done}{left}]` {self.progress * 100:.2f}%'

    def __str__(self):
        return self.__draw()

if __name__ == '__main__':
    from time import sleep
    pb = ProgressBar(7)

    for i in range(11):
        pb.update(i/10)
        print(pb)
        sleep(0.1)
