from pathlib import Path

import pygame


class PlayerAttack:
    full_health_pass_time = 0.9
    passes = 3
    shrink_time = 0.16
    result_time = 0.45
    expand_time = 0.24

    def __init__(self, arena, enemy_hp=30):
        self.arena = arena
        self.max_hp = self.hp = enemy_hp
        self.phase = "idle"
        self.elapsed = 0.0
        self.damage = 0
        self.critical = False
        path = Path(__file__).parent / "Assets" / "EnemyHealthBar.png"
        art = pygame.image.load(path).convert_alpha()
        self.meter = pygame.transform.scale(art.subsurface(art.get_bounding_rect()), (53, 18))
        self.meter_rect = self.meter.get_rect(center=arena.center)

    @property
    def active(self):
        return self.phase != "idle"

    def start(self):
        if not self.active and self.hp > 0:
            self.phase = "shrink"
            self.elapsed = 0.0

    @property
    def pass_time(self):
        missing_health = 1 - self.hp / self.max_hp
        return self.full_health_pass_time / (1 + missing_health)

    @property
    def marker(self):
        sweep = self.elapsed / self.pass_time
        fraction = 1 - abs(sweep % 2 - 1)
        return round(fraction * (self.meter_rect.width - 1))

    def finish_attempt(self, damage, critical=False):
        self.critical = critical
        self.damage = damage
        self.hp = max(0, self.hp - damage)
        self.phase = "result"
        self.elapsed = 0.0

    def strike(self):
        if self.phase == "aim":
            center = self.meter_rect.width // 2
            distance = abs(self.marker - center)
            crit_damage = max(1, (self.max_hp + 2) // 4)
            damage = 1 + (crit_damage - 1) * (center - distance) // center
            self.finish_attempt(damage, critical=distance == 0)
            return True
        return False

    def update(self, dt):
        if not self.active:
            return
        self.elapsed += dt
        if self.phase == "shrink" and self.elapsed >= self.shrink_time:
            self.elapsed -= self.shrink_time
            self.phase = "aim"
        if self.phase == "aim" and self.elapsed >= self.passes * self.pass_time:
            self.finish_attempt(0)
        elif self.phase == "result" and self.elapsed >= self.result_time:
            self.elapsed -= self.result_time
            self.phase = "expand"
        if self.phase == "expand" and self.elapsed >= self.expand_time:
            self.phase = "idle"

    def draw(self, surface, font):
        box = self.meter_rect.inflate(4, 6)
        if self.phase in ("shrink", "expand"):
            if self.phase == "shrink":
                t = min(self.elapsed / self.shrink_time, 1)
            else:
                progress = min(self.elapsed / self.expand_time, 1)
                t = 1 - progress * progress * (3 - 2 * progress)
            box.size = (round(self.arena.width + (box.width - self.arena.width) * t),
                        round(self.arena.height + (box.height - self.arena.height) * t))
            box.center = self.arena.center
        pygame.draw.rect(surface, "white", box, 1)
        if self.phase in ("shrink", "expand"):
            return
        surface.blit(self.meter, self.meter_rect)
        if self.phase == "aim":
            x = self.meter_rect.left + self.marker
            pygame.draw.line(surface, "yellow", (x, box.top + 1), (x, box.bottom - 2))
            message = "Space to strike"
        elif self.damage == 0:
            message = "Miss"
        elif self.critical:
            message = f"Crit! {self.damage} damage"
        else:
            message = f"{self.damage} damage"
        label = font.render(message, True, "white")
        surface.blit(label, label.get_rect(midtop=(box.centerx, box.bottom + 2)))
