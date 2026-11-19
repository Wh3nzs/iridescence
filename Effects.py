class Shake:
    offsets = ((2, -1), (-2, 1), (1, 1), (-1, 0))
    frameTime = 0.03

    def __init__(self):
        self.elapsed = len(self.offsets) * self.frameTime
        self.strength = 1.0

    def trigger(self, strength=1.0):
        self.strength = strength
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def offset(self):
        frame = int(self.elapsed / self.frameTime)
        if frame < len(self.offsets):
            x, y = self.offsets[frame]
            return round(x * self.strength), round(y * self.strength)
        return (0, 0)


class Lunge:
    forwardTime = 0.12
    returnTime = 0.20

    def __init__(self):
        self.elapsed = self.forwardTime + self.returnTime
        self.reach = (0, 0)

    def trigger(self, reach):
        self.reach = reach
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def offset(self):
        if self.elapsed < self.forwardTime:
            t = self.elapsed / self.forwardTime
            amount = 1 - (1 - t) ** 2
        else:
            t = min((self.elapsed - self.forwardTime) / self.returnTime, 1.0)
            amount = 1 - t * t * (3 - 2 * t)
        dx, dy = self.reach
        return round(dx * amount), round(dy * amount)
