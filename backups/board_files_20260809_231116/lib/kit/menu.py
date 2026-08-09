"""可复用的五向键 LCD 菜单。"""

from .buttons import SHORT, LONG


class Menu:
    def __init__(self, display, items):
        self.display = display
        self.items = list(items)
        self.index = 0

    def render(self):
        self.display.clear()
        self.display.text(0, "Select", self.display.lcd.CYAN)
        if not self.items:
            self.display.text(1, "No items", self.display.lcd.YELLOW)
            return
        start = max(0, min(self.index - 1, len(self.items) - 3))
        for row, item_index in enumerate(range(start, min(start + 3, len(self.items))), 1):
            prefix = ">" if item_index == self.index else " "
            self.display.text(row, prefix + self.items[item_index][0])

    def move(self, delta):
        if not self.items:
            return
        self.index = (self.index + delta) % len(self.items)
        self.render()

    def select(self):
        if not self.items:
            return None
        label, callback = self.items[self.index]
        result = callback()
        self.render()
        return label, result

    def bind(self, buttons):
        buttons.on("up", SHORT, lambda _n, _e: self.move(-1))
        buttons.on("down", SHORT, lambda _n, _e: self.move(1))
        buttons.on("center", SHORT, lambda _n, _e: self.select())
        buttons.on("center", LONG, lambda _n, _e: self.select())
        self.render()
