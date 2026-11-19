from functools import lru_cache
from math import sin, tau
from pathlib import Path

import pygame


@lru_cache(maxsize=128)
def loadSprite(filename, size, vertical=False):
    path = Path(__file__).parent / "Assets" / filename
    image = pygame.image.load(path).convert_alpha()
    if vertical:
        image = pygame.transform.rotate(image, 90)
    scaled = pygame.transform.scale(image, size)
    if not scaled.get_bounding_rect():
        # Thin artwork can fall between samples when shrunk to a few pixels.
        scaled = pygame.transform.smoothscale(image, size)
    return scaled


@lru_cache(maxsize=32)
def loadDashArt(filename):
    path = Path(__file__).parent / "Assets" / filename
    image = pygame.image.load(path).convert_alpha()
    bounds = image.get_bounding_rect()
    if not bounds:
        return image
    image = image.subsurface(bounds)
    if filename == "Knife.png":
        # The knife PNG contains only its white outline.
        filled = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        outline = pygame.mask.from_surface(image).outline()
        if len(outline) >= 3:
            pygame.draw.polygon(filled, (125, 135, 148), outline)
        filled.blit(image, (0, 0))
        return filled
    return image


def drawProjectile(surface, rect, image):
    if image is None:
        pygame.draw.rect(surface, "white", rect)
    else:
        surface.blit(image, rect)


class SineRainProjectile:
    fallSpeed = 32
    amplitude = 6
    wavelength = 32
    damage = 4

    def __init__(self, x, y, sprite=None):
        self.startX = x
        self.startY = y
        self.distance = 0.0
        self.rect = pygame.Rect(0, 0, 3, 3)
        self.image = loadSprite(sprite, self.rect.size) if sprite else None
        self.rect.center = x, y

    def update(self, dt):
        self.distance += self.fallSpeed * dt
        angle = tau * self.distance / self.wavelength
        x = self.startX + self.amplitude * sin(angle)
        self.rect.center = round(x), round(self.startY + self.distance)

    def draw(self, surface):
        drawProjectile(surface, self.rect, self.image)


class CenterBeam:
    damage = 6
    warningTime = 0.8
    activeTime = 0.5

    def __init__(self, arena, orientation="horizontal", x=None, y=None, sprite=None):
        inner = arena.inflate(-2, -2)
        if orientation == "horizontal":
            size = (inner.width, 3)
        elif orientation == "vertical":
            size = (3, inner.height)
        else:
            raise ValueError("Beam orientation must be 'horizontal' or 'vertical'")
        self.orientation = orientation
        self.rect = pygame.Rect((0, 0), size)
        self.rect.center = (
            arena.centerx if x is None else arena.left + x,
            arena.centery if y is None else arena.top + y,
        )
        self.image = None
        if sprite:
            self.image = loadSprite(sprite, size, orientation == "vertical")
        fullRect = self.rect
        self.rect = fullRect.clip(inner)
        if self.image is not None and self.rect:
            crop = self.rect.move(-fullRect.left, -fullRect.top)
            self.image = self.image.subsurface(crop)
        self.elapsed = 0.0
        self.hitPlayer = False

    @property
    def finished(self):
        return self.elapsed >= self.warningTime + self.activeTime

    def update(self, player, dt):
        self.elapsed += dt
        if self.warningTime <= self.elapsed and not self.finished:
            if not self.hitPlayer and self.rect.colliderect(player.rect):
                player.takeDamage(self.damage)
                self.hitPlayer = True

    def draw(self, surface):
        if not self.rect.width or not self.rect.height:
            return
        if self.elapsed < self.warningTime:
            if self.orientation == "horizontal":
                start = self.rect.midleft
                end = (self.rect.right - 1, self.rect.centery)
            else:
                start = self.rect.midtop
                end = (self.rect.centerx, self.rect.bottom - 1)
            pygame.draw.line(surface, "orange", start, end, 2)
        elif not self.finished:
            drawProjectile(surface, self.rect, self.image)


class PlasticWrapAttack:
    """Unroll a tiled strip, trapping touched players until the strip expires."""

    damage = 3  # Applied once when caught; 0 means the wrap only traps.

    def __init__(self, arena, orientation="horizontal", x=None, y=None,
                 width=12, rollTime=1.0, holdTime=2.0, warningTime=0.8):
        if orientation not in ("horizontal", "vertical"):
            raise ValueError("Wrap orientation must be 'horizontal' or 'vertical'")
        if width < 1 or rollTime <= 0 or holdTime < 0 or warningTime < 0:
            raise ValueError("Width and roll_time must be positive; other times nonnegative")
        self.orientation = orientation
        self.inner = arena.inflate(-2, -2)
        vertical = orientation == "vertical"
        size = (int(width), self.inner.height) if vertical else (self.inner.width, int(width))
        self.lane = pygame.Rect((0, 0), size)
        self.lane.center = (arena.centerx if x is None else arena.left + x,
                            arena.centery if y is None else arena.top + y)
        self.warningTime = warningTime
        self.rollTime = rollTime
        self.holdTime = holdTime
        self.elapsed = 0.0
        self.rect = pygame.Rect(self.lane.topleft, (0, 0))
        self.caughtPlayers = set()

        # The trail artwork tiles horizontally; rotate the finished strip for vertical use.
        path = Path(__file__).parent / "Assets"
        tile = pygame.image.load(path / "PlasticWrapTrail.png").convert_alpha()
        # Remove vertical padding while keeping both horizontal tiling edges.
        bounds = tile.get_bounding_rect()
        if bounds:
            tile = tile.subsurface((0, bounds.top, tile.get_width(), bounds.height))
        tileWidth = max(1, round(tile.get_width() * int(width) / tile.get_height()))
        # Filter first so thin source lines survive the reduction, then turn
        # coverage into solid white pixels instead of leaving blurred gray edges.
        tile = pygame.transform.smoothscale(tile, (tileWidth, int(width)))
        coverage = pygame.mask.from_surface(tile, threshold=32)
        tile = coverage.to_surface(setcolor=(255, 255, 255, 255),
                                   unsetcolor=(0, 0, 0, 0))
        length = self.lane.height if vertical else self.lane.width
        strip = pygame.Surface((length, int(width)), pygame.SRCALPHA)
        for offset in range(0, length, tileWidth):
            strip.blit(tile, (offset, 0))
        self.image = pygame.transform.rotate(strip, -90) if vertical else strip
        roll = pygame.image.load(path / "PlasticWrapRoll.png").convert_alpha()
        bounds = roll.get_bounding_rect()
        if bounds:
            roll = roll.subsurface(bounds)
        rollHeight = int(width) + 4
        roll = pygame.transform.scale(roll, (max(1, round(roll.get_width() * rollHeight / roll.get_height())), rollHeight))
        self.rollImage = pygame.transform.rotate(roll, -90) if vertical else roll
        self.rollPosition = self.lane.midtop if vertical else self.lane.midleft

    @property
    def finished(self):
        return self.elapsed >= self.warningTime + self.rollTime + self.holdTime

    def update(self, player, dt):
        self.elapsed += dt
        if self.finished:
            for caught in self.caughtPlayers:
                caught.movementLocks.discard(self)
            self.caughtPlayers.clear()
            self.rect.size = (0, 0)
            return
        if self.elapsed < self.warningTime:
            return
        progress = min(1.0, (self.elapsed - self.warningTime) / self.rollTime)
        revealed = self.lane.copy()
        if self.orientation == "horizontal":
            revealed.width = round(self.lane.width * progress)
            self.rollPosition = (revealed.right, self.lane.centery)
        else:
            revealed.height = round(self.lane.height * progress)
            self.rollPosition = (self.lane.centerx, revealed.bottom)
        self.rect = revealed.clip(self.inner)
        if self.rect.colliderect(player.rect):
            if player not in self.caughtPlayers:
                player.takeDamage(self.damage)
            player.movementLocks.add(self)
            self.caughtPlayers.add(player)

    def draw(self, surface):
        if self.finished:
            return
        oldClip = surface.get_clip()
        surface.set_clip(oldClip.clip(self.inner))
        try:
            if self.elapsed < self.warningTime:
                if self.orientation == "horizontal":
                    start, end = self.lane.midleft, self.lane.midright
                else:
                    start, end = self.lane.midtop, self.lane.midbottom
                pygame.draw.line(surface, "orange", start, end)
            else:
                if self.rect:
                    crop = self.rect.move(-self.lane.left, -self.lane.top)
                    surface.blit(self.image, self.rect, crop)
                if self.elapsed < self.warningTime + self.rollTime:
                    surface.blit(self.rollImage, self.rollImage.get_rect(center=self.rollPosition))
        finally:
            surface.set_clip(oldClip)


class SyringeAttack:
    enterTime = 0.65  # Seconds to fly from above the arena to its center.
    spinTime = 0.8
    spinTurns = 2
    warningTime = 0.3
    speed = 160  # Canvas pixels per second (the window scales these up).
    damage = 10

    def __init__(self, arena, spinTime = 0.8, spinTurns = 2):
        self.spinTime = spinTime
        self.spinTurns = spinTurns
        
        self.art = loadDashArt("Syringe.png")
        # Leave enough room for the whole sprite to disappear past an edge.
        margin = max(self.art.get_size()) + 8
        self.bounds = arena.inflate(margin * 2, margin * 2)
        self.center = pygame.Vector2(arena.center)
        self.start = pygame.Vector2(arena.centerx, self.bounds.top)
        self.position = self.start.copy()
        self.rect = pygame.Rect(0, 0, 5, 5)
        self.rect.center = self.position
        self.elapsed = 0.0
        self.angle = 180.0  # The original art points up; enter pointing down.
        self.direction = None
        self.end = None
        self.finished = False
        self.hitPlayer = False
        self.phase = "enter"

    def update(self, player, dt):
        if self.finished:
            return
        self.elapsed += dt
        spinEnd = self.enterTime + self.spinTime
        dashStart = spinEnd + self.warningTime

        if self.elapsed < self.enterTime:
            self.phase = "enter"
            progress = self.elapsed / self.enterTime
            self.position = self.start.lerp(self.center, progress)
        elif self.elapsed < spinEnd:
            self.phase = "spin"
            self.position = self.center.copy()
            progress = (self.elapsed - self.enterTime) / self.spinTime
            self.angle = 180 + 360 * self.spinTurns * progress
        else:
            if self.direction is None:
                # Lock the player's location ONCE, after spinning, not at spawn.
                offset = pygame.Vector2(player.rect.center) - self.center
                # A player exactly in the center gives a zero-length vector.
                self.direction = offset.normalize() if offset.length_squared() else pygame.Vector2(0, 1)
                self.end = DashAttack.pointOnEdge(self.bounds, self.center, self.direction)
                self.angle = self.direction.angle_to(pygame.Vector2(0, -1))
                self.position = self.center.copy()

            if self.elapsed < dashStart:
                self.phase = "aim"
            else:
                self.phase = "dash"
                previous = self.position.copy()
                distance = self.center.distance_to(self.end)
                traveled = min(self.speed * (self.elapsed - dashStart), distance)
                self.position = self.center + self.direction * traveled
                # Sweep the small hitbox along its path so a slow frame cannot
                # let the syringe skip straight through the player.
                hitArea = player.rect.inflate(self.rect.width - 1, self.rect.height - 1)
                if not self.hitPlayer and (
                    hitArea.collidepoint(self.position)
                    or hitArea.clipline(previous, self.position)
                ):
                    player.takeDamage(self.damage)
                    self.hitPlayer = True
                self.finished = traveled >= distance

        self.rect.center = round(self.position.x), round(self.position.y)

    def draw(self, surface):
        if self.finished:
            return
        if self.phase == "aim":
            pygame.draw.line(surface, "#40B3FF", self.center, self.end)
        # Always rotate the original art, preserving its quality and center.
        image = pygame.transform.rotate(self.art, self.angle % 360)
        surface.blit(image, image.get_rect(center=self.rect.center))


class DashAttack:
    damage = 4
    warningTime = 0.5
    speed = 120  # Canvas pixels per second

    def __init__(self, arena, player, degrees, sprite=None):
        # Degrees select a fixed spawn point around the arena.
        bounds = arena.inflate(24, 24)
        center = pygame.Vector2(arena.center)
        outward = pygame.Vector2(1, 0).rotate(-degrees)
        self.start = self.pointOnEdge(bounds, center, outward)

        self.target = pygame.Vector2(player.rect.center)
        direction = (self.target - self.start).normalize()
        self.end = self.pointOnEdge(bounds, self.target, direction)
        self.distance = self.start.distance_to(self.end)
        self.elapsed = 0.0
        self.finished = False
        self.hitPlayer = False

        self.rect = pygame.Rect(0, 0, 5, 5)
        self.image = None
        if sprite:
            # Sprite art points up. Pygame rotates images counterclockwise.
            angle = direction.angle_to(pygame.Vector2(0, -1))
            self.image = pygame.transform.rotate(loadDashArt(sprite), angle)
        self.rect.center = round(self.start.x), round(self.start.y)

    @staticmethod
    def pointOnEdge(bounds, origin, direction):
        distances = []
        if direction.x:
            x = bounds.right - 1 if direction.x > 0 else bounds.left
            distances.append((x - origin.x) / direction.x)
        if direction.y:
            y = bounds.bottom - 1 if direction.y > 0 else bounds.top
            distances.append((y - origin.y) / direction.y)
        return origin + direction * min(distances)

    def update(self, player, dt):
        self.elapsed += dt
        if self.elapsed < self.warningTime:
            return

        dashTime = self.elapsed - self.warningTime
        traveled = self.speed * dashTime
        progress = min(traveled / self.distance, 1.0) if self.distance else 1.0

        position = self.start.lerp(self.end, progress)
        self.rect.center = round(position.x), round(position.y)

        if not self.hitPlayer and self.rect.colliderect(player.rect):
            player.takeDamage(self.damage)
            self.hitPlayer = True

        self.finished = progress >= 1.0

    def draw(self, surface):
        if self.elapsed < self.warningTime:
            pygame.draw.line(surface, "#40B3FF", self.start, self.end)
        if self.image is None:
            pygame.draw.rect(surface, "white", self.rect)
        else:
            surface.blit(self.image, self.image.get_rect(center=self.rect.center))

