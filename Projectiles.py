from functools import lru_cache
from math import sin, tau
from pathlib import Path

import pygame


@lru_cache(maxsize=128)
def load_sprite(filename, size, vertical=False):
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
def load_dash_art(filename):
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


def draw_projectile(surface, rect, image):
    if image is None:
        pygame.draw.rect(surface, "white", rect)
    else:
        surface.blit(image, rect)


class SineRainProjectile:
    fall_speed = 32
    amplitude = 6
    wavelength = 32
    damage = 4

    def __init__(self, x, y, sprite=None):
        self.start_x = x
        self.start_y = y
        self.distance = 0.0
        self.rect = pygame.Rect(0, 0, 3, 3)
        self.image = load_sprite(sprite, self.rect.size) if sprite else None
        self.rect.center = x, y

    def update(self, dt):
        self.distance += self.fall_speed * dt
        angle = tau * self.distance / self.wavelength
        x = self.start_x + self.amplitude * sin(angle)
        self.rect.center = round(x), round(self.start_y + self.distance)

    def draw(self, surface):
        draw_projectile(surface, self.rect, self.image)


class CenterBeam:
    warning_time = 0.8
    active_time = 0.5

    def __init__(self, arena, orientation="horizontal", x=None, y=None, sprite=None):
        inner = arena.inflate(-2, -2)
        if orientation == "horizontal":
            size = (inner.width, 5)
        elif orientation == "vertical":
            size = (5, inner.height)
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
            self.image = load_sprite(sprite, size, orientation == "vertical")
        full_rect = self.rect
        self.rect = full_rect.clip(inner)
        if self.image is not None and self.rect:
            crop = self.rect.move(-full_rect.left, -full_rect.top)
            self.image = self.image.subsurface(crop)
        self.elapsed = 0.0
        self.hit_player = False

    @property
    def finished(self):
        return self.elapsed >= self.warning_time + self.active_time

    def update(self, player, dt):
        self.elapsed += dt
        if self.warning_time <= self.elapsed and not self.finished:
            if not self.hit_player and self.rect.colliderect(player.rect):
                player.takeDamage(20)
                self.hit_player = True

    def draw(self, surface):
        if not self.rect.width or not self.rect.height:
            return
        if self.elapsed < self.warning_time:
            if self.orientation == "horizontal":
                start = self.rect.midleft
                end = (self.rect.right - 1, self.rect.centery)
            else:
                start = self.rect.midtop
                end = (self.rect.centerx, self.rect.bottom - 1)
            pygame.draw.line(surface, "orange", start, end)
        elif not self.finished:
            draw_projectile(surface, self.rect, self.image)


class SyringeAttack:
    enter_time = 0.65  # Seconds to fly from above the arena to its center.
    spin_time = 0.8
    spin_turns = 2
    warning_time = 0.3
    speed = 160  # Canvas pixels per second (the window scales these up).
    damage = 10

    def __init__(self, arena):
        self.art = load_dash_art("Syringe.png")
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
        self.hit_player = False
        self.phase = "enter"

    def update(self, player, dt):
        if self.finished:
            return
        self.elapsed += dt
        spin_end = self.enter_time + self.spin_time
        dash_start = spin_end + self.warning_time

        if self.elapsed < self.enter_time:
            self.phase = "enter"
            progress = self.elapsed / self.enter_time
            self.position = self.start.lerp(self.center, progress)
        elif self.elapsed < spin_end:
            self.phase = "spin"
            self.position = self.center.copy()
            progress = (self.elapsed - self.enter_time) / self.spin_time
            self.angle = 180 + 360 * self.spin_turns * progress
        else:
            if self.direction is None:
                # Lock the player's location ONCE, after spinning, not at spawn.
                offset = pygame.Vector2(player.rect.center) - self.center
                # A player exactly in the center gives a zero-length vector.
                self.direction = offset.normalize() if offset.length_squared() else pygame.Vector2(0, 1)
                self.end = DashAttack.point_on_edge(self.bounds, self.center, self.direction)
                self.angle = self.direction.angle_to(pygame.Vector2(0, -1))
                self.position = self.center.copy()

            if self.elapsed < dash_start:
                self.phase = "aim"
            else:
                self.phase = "dash"
                previous = self.position.copy()
                distance = self.center.distance_to(self.end)
                traveled = min(self.speed * (self.elapsed - dash_start), distance)
                self.position = self.center + self.direction * traveled
                # Sweep the small hitbox along its path so a slow frame cannot
                # let the syringe skip straight through the player.
                hit_area = player.rect.inflate(self.rect.width - 1, self.rect.height - 1)
                if not self.hit_player and (
                    hit_area.collidepoint(self.position)
                    or hit_area.clipline(previous, self.position)
                ):
                    player.takeDamage(self.damage)
                    self.hit_player = True
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
    warning_time = 0.5
    speed = 120  # Canvas pixels per second

    def __init__(self, arena, player, degrees, sprite=None):
        # Degrees select a fixed spawn point around the arena.
        bounds = arena.inflate(24, 24)
        center = pygame.Vector2(arena.center)
        outward = pygame.Vector2(1, 0).rotate(-degrees)
        self.start = self.point_on_edge(bounds, center, outward)

        self.target = pygame.Vector2(player.rect.center)
        direction = (self.target - self.start).normalize()
        self.end = self.point_on_edge(bounds, self.target, direction)
        self.distance = self.start.distance_to(self.end)
        self.elapsed = 0.0
        self.finished = False
        self.hit_player = False

        self.rect = pygame.Rect(0, 0, 5, 5)
        self.image = None
        if sprite:
            # Sprite art points up. Pygame rotates images counterclockwise.
            angle = direction.angle_to(pygame.Vector2(0, -1))
            self.image = pygame.transform.rotate(load_dash_art(sprite), angle)
        self.rect.center = round(self.start.x), round(self.start.y)

    @staticmethod
    def point_on_edge(bounds, origin, direction):
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
        if self.elapsed < self.warning_time:
            return

        dash_time = self.elapsed - self.warning_time
        traveled = self.speed * dash_time
        progress = min(traveled / self.distance, 1.0) if self.distance else 1.0

        position = self.start.lerp(self.end, progress)
        self.rect.center = round(position.x), round(position.y)

        if not self.hit_player and self.rect.colliderect(player.rect):
            player.takeDamage(10)
            self.hit_player = True

        self.finished = progress >= 1.0

    def draw(self, surface):
        if self.elapsed < self.warning_time:
            pygame.draw.line(surface, "#40B3FF", self.start, self.end)
        if self.image is None:
            pygame.draw.rect(surface, "white", self.rect)
        else:
            surface.blit(self.image, self.image.get_rect(center=self.rect.center))
