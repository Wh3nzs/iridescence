from math import sin, tau
from pathlib import Path

import pygame


class DexterSprite:
    """Layered portrait with mirrored arms and a time-based breathing loop."""

    idlePeriod = 2.4
    hitRaiseTime = 0.07
    hitReturnTime = 0.25
    hitArmAngle = 75

    def __init__(self):
        assets = Path(__file__).parent / "Assets"

        def part(name, size):
            image = pygame.image.load(assets / name).convert_alpha()
            bounds = image.get_bounding_rect()
            if bounds:
                image = image.subsurface(bounds)
            return pygame.transform.scale(image, size)

        self.body = part("DexterShirt.png", (26, 20))
        self.head = part("DexterFace.png", (22, 22))
        self.leftArm = part("DexterArm.png", (16, 14))
        self.rightArm = pygame.transform.flip(self.leftArm, True, False)
        self.image = pygame.Surface((60, 48), pygame.SRCALPHA)
        self.elapsed = 0.0
        self.hitElapsed = self.hitRaiseTime + self.hitReturnTime
        self.previousHp = None

    def reset(self):
        self.elapsed = 0.0
        self.hitElapsed = self.hitRaiseTime + self.hitReturnTime
        self.previousHp = None

    @property
    def hitAmount(self):
        if self.hitElapsed < self.hitRaiseTime:
            t = self.hitElapsed / self.hitRaiseTime
            return 1 - (1 - t) ** 3
        t = min(1, (self.hitElapsed - self.hitRaiseTime) / self.hitReturnTime)
        return 1 - t * t * (3 - 2 * t)

    def drawArm(self, art, pivot, shoulder, angle):
        # Rotate about the shoulder, so the attached end stays in place.
        centerOffset = pygame.Vector2(art.get_rect().center) - pivot
        center = pygame.Vector2(shoulder) + centerOffset.rotate(-angle)
        rotated = pygame.transform.rotate(art, angle)
        self.image.blit(rotated, rotated.get_rect(center=(round(center.x), round(center.y))))

    def update(self, dt, enemyHp=None):
        # Observe actual damage, including partial hits resolved by a timeout.
        # Individual WASD presses and misses do not reduce HP or trigger this.
        if enemyHp is not None:
            if self.previousHp is not None and enemyHp < self.previousHp:
                self.hitElapsed = 0.0
            self.previousHp = enemyHp
        self.hitElapsed += dt
        self.elapsed = (self.elapsed + dt) % self.idlePeriod
        phase = tau * self.elapsed / self.idlePeriod
        bodyY = 24 + round(0.7 * sin(phase))
        headY = 4 + round(0.8 * sin(phase - 0.45))
        sway = 4 * sin(phase + 0.4)
        armAngle = sway - self.hitArmAngle * self.hitAmount
        self.image.fill((0, 0, 0, 0))
        # Arms behind the shirt keep the shoulder seams covered.
        self.drawArm(self.leftArm, pygame.Vector2(14, 2), (20, bodyY + 3), armAngle)
        self.drawArm(self.rightArm, pygame.Vector2(2, 2), (40, bodyY + 3), -armAngle)
        self.image.blit(self.body, (17, bodyY))
        self.image.blit(self.head, (19, headY))
        return self.image
