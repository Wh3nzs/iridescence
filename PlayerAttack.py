from pathlib import Path
import random

import pygame


class PlayerAttack:
    fullHealthPassTime = 0.45
    passes = 3
    shrinkTime = 0.16
    resultTime = 0.45
    expandTime = 0.24
    sequenceLength = 4
    sequenceTime = 2.5  # Seconds to enter the entire sequence.

    def __init__(self, arena, enemyHp=30):
        self.arena = arena
        self.maxHp = self.hp = enemyHp
        self.phase = "idle"
        self.elapsed = 0.0
        self.damage = 0
        self.critical = False
        self.attackMode = "meter"
        self.nextMode = "meter"  # Normal attack first, then WASD, alternating.
        self.sequence = []
        self.sequenceIndex = 0
        self.heldKeys = set()
        self.keyIcons = {}
        for key, letter in ((pygame.K_w, "W"), (pygame.K_a, "A"),
                            (pygame.K_s, "S"), (pygame.K_d, "D")):
            icon = pygame.image.load(Path(__file__).parent / "Assets" / f"{letter}Icon.png").convert_alpha()
            bounds = icon.get_bounding_rect()
            if bounds:
                icon = icon.subsurface(bounds)
            self.keyIcons[key] = pygame.transform.scale(icon, (16, 16))
        path = Path(__file__).parent / "Assets" / "EnemyHealthBar.png"
        art = pygame.image.load(path).convert_alpha()
        self.meter = pygame.transform.scale(art.subsurface(art.get_bounding_rect()), (53, 18))
        self.meterRect = self.meter.get_rect(center=arena.center)

    @property
    def active(self):
        return self.phase != "idle"

    def start(self, mode=None):
        if mode not in (None, "meter", "sequence"):
            raise ValueError("Attack mode must be 'meter' or 'sequence'")
        if not self.active and self.hp > 0:
            self.attackMode = mode or self.nextMode
            self.nextMode = "meter" if self.attackMode == "sequence" else "sequence"
            self.sequence = random.choices(tuple(self.keyIcons), k=self.sequenceLength)
            self.sequenceIndex = 0
            self.phase = "shrink"
            self.elapsed = 0.0

    def handleEvent(self, event):
        if event.type == pygame.KEYUP:
            self.heldKeys.discard(event.key)
            return False
        if event.type != pygame.KEYDOWN:
            return False
        if event.key in self.heldKeys or getattr(event, "repeat", False):
            return False
        self.heldKeys.add(event.key)
        if self.phase != "aim":
            return False
        if self.attackMode == "meter":
            return self.strike() if event.key == pygame.K_SPACE else False
        if event.key not in self.keyIcons:
            return False
        if event.key != self.sequence[self.sequenceIndex]:
            self.finishSequence()
            return False
        self.sequenceIndex += 1
        if self.sequenceIndex == len(self.sequence):
            self.finishSequence()
        return True  # Every correct key gets feedback, not just the last one.

    def finishSequence(self):
        fullDamage = max(1, (self.maxHp + 2) // 4)
        damage = fullDamage * self.sequenceIndex // len(self.sequence)
        self.finishAttempt(damage, critical=self.sequenceIndex == len(self.sequence))

    @property
    def passTime(self):
        missingHealth = 1 - self.hp / self.maxHp
        return self.fullHealthPassTime / (1 + missingHealth)

    @property
    def marker(self):
        sweep = self.elapsed / self.passTime
        fraction = 1 - abs(sweep % 2 - 1)
        return round(fraction * (self.meterRect.width - 1))

    def finishAttempt(self, damage, critical=False):
        self.critical = critical
        self.damage = damage
        self.hp = max(0, self.hp - damage)
        self.phase = "result"
        self.elapsed = 0.0

    def strike(self):
        if self.phase == "aim" and self.attackMode == "meter":
            center = self.meterRect.width // 2
            distance = abs(self.marker - center)
            critDamage = max(1, (self.maxHp + 2) // 4)
            damage = 1 + (critDamage - 1) * (center - distance) // center
            self.finishAttempt(damage, critical=distance == 0)
            return True
        return False

    def update(self, dt):
        if not self.active:
            return
        self.elapsed += dt
        if self.phase == "shrink" and self.elapsed >= self.shrinkTime:
            self.elapsed -= self.shrinkTime
            self.phase = "aim"
        if self.phase == "aim":
            if self.attackMode == "sequence" and self.elapsed >= self.sequenceTime:
                self.finishSequence()
            elif self.attackMode == "meter" and self.elapsed >= self.passes * self.passTime:
                self.finishAttempt(0)
        elif self.phase == "result" and self.elapsed >= self.resultTime:
            self.elapsed -= self.resultTime
            self.phase = "expand"
        if self.phase == "expand" and self.elapsed >= self.expandTime:
            self.phase = "idle"

    def draw(self, surface, font):
        box = self.meterRect.inflate(4, 6)
        if self.attackMode == "sequence":
            box.size = (max(60, self.sequenceLength * 18 + 4), 32)
            box.center = self.arena.center
        if self.phase in ("shrink", "expand"):
            if self.phase == "shrink":
                t = min(self.elapsed / self.shrinkTime, 1)
            else:
                progress = min(self.elapsed / self.expandTime, 1)
                t = 1 - progress * progress * (3 - 2 * progress)
            box.size = (round(self.arena.width + (box.width - self.arena.width) * t),
                        round(self.arena.height + (box.height - self.arena.height) * t))
            box.center = self.arena.center
        pygame.draw.rect(surface, "red" if self.attackMode == "sequence" else "white", box, 1)
        if self.phase in ("shrink", "expand"):
            return
        if self.attackMode == "sequence":
            left = box.centerx - len(self.sequence) * 18 // 2
            for index, key in enumerate(self.sequence):
                rect = pygame.Rect(left + index * 18, box.top + 4, 16, 16)
                if index < self.sequenceIndex:
                    pygame.draw.line(surface, "white", (rect.left, rect.bottom + 1),
                                     (rect.right - 1, rect.bottom + 1))
                elif index == self.sequenceIndex and self.phase == "aim":
                    pygame.draw.rect(surface, "red", rect.inflate(2, 2), 1)
                surface.blit(self.keyIcons[key], rect)
            if self.phase == "aim":
                remaining = max(0, 1 - self.elapsed / self.sequenceTime)
                pygame.draw.rect(surface, "white", (box.left + 3, box.bottom - 6, round((box.width - 6) * remaining), 3))
        else:
            surface.blit(self.meter, self.meterRect)
        if self.phase == "aim" and self.attackMode == "sequence":
            message = "WASD in order!"
        elif self.phase == "aim":
            x = self.meterRect.left + self.marker
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
