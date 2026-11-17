class Shake:
    offsets = ((2, -1), (-2, 1), (1, 1), (-1, 0))
    frame_time = 0.03

    def __init__(self):
        self.elapsed = len(self.offsets) * self.frame_time

    def trigger(self):
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def offset(self):
        frame = int(self.elapsed / self.frame_time)
        if frame < len(self.offsets):
            return self.offsets[frame]
        return (0, 0)


class Lunge:
    forward_time = 0.12
    return_time = 0.20

    def __init__(self):
        self.elapsed = self.forward_time + self.return_time
        self.reach = (0, 0)

    def trigger(self, reach):
        self.reach = reach
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def offset(self):
        if self.elapsed < self.forward_time:
            t = self.elapsed / self.forward_time
            amount = 1 - (1 - t) ** 2
        else:
            t = min((self.elapsed - self.forward_time) / self.return_time, 1.0)
            amount = 1 - t * t * (3 - 2 * t)
        dx, dy = self.reach
        return round(dx * amount), round(dy * amount)
