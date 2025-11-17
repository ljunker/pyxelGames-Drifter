import pyxel


class App:
    def __init__(self):
        pyxel.init(160, 120, fps=60, title="Drifter")
        pyxel.run(self.update, self.draw)

    def update(self):
        pass

    def draw(self):
        pyxel.cls(0)


App()
