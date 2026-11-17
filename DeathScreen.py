from math import sin, tau
from pathlib import Path

import pygame


class DeathScreen:
    def __init__(self):
        assets = Path(__file__).parent / "Assets"
        self.background = pygame.image.load(assets / "died screen.png").convert_alpha()
        marker = pygame.image.load(assets / "DeathScreenPlayer.png").convert_alpha()
        self.marker = marker.subsurface(marker.get_bounding_rect())
        retry = pygame.image.load(assets / "RetryButton.png").convert_alpha()
        menu = pygame.image.load(assets / "MenuButton.png").convert_alpha()
        # Both supplied buttons say Menu. Keep the drawn silhouette for Retry.
        if pygame.image.tobytes(retry, "RGBA") == pygame.image.tobytes(menu, "RGBA"):
            retry.fill("white", special_flags=pygame.BLEND_RGB_MAX)
            text = pygame.font.Font(None, 26).render("Retry", True, "black")
            retry.blit(text, text.get_rect(center=retry.get_bounding_rect().center))
        self.buttons = {}
        for action, image, x in (("retry", retry, 328), ("menu", menu, 472)):
            image = image.subsurface(image.get_bounding_rect())
            self.buttons[action] = (image, image.get_rect(center=(x, 433)))
        self.selected = "retry"
        self.focus_started = pygame.time.get_ticks()
        self.hit_rects = {action: rect for action, (_, rect) in self.buttons.items()}
        self.marker_rect = self.marker.get_rect()

    def show(self, hp, max_hp):
        progress = max(0, min(1, (max_hp - hp) / max_hp))
        # Feet follow the painted line from its left end to the flagpole.
        self.marker_rect.midbottom = (round(104 + progress * (699 - 104)),
                                      round(304 - 3 * progress))
        self.selected = "retry"
        self.focus_started = pygame.time.get_ticks()
        for action, (_, rect) in self.buttons.items():
            self.hit_rects[action] = rect

    def select(self, action):
        if self.selected != action:
            self.selected = action
            self.focus_started = pygame.time.get_ticks()

    def action_for(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                             pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
                self.select("menu" if self.selected == "retry" else "retry")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.selected
            elif event.key == pygame.K_ESCAPE:
                return "menu"
        elif event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            for action, rect in self.hit_rects.items():
                if rect.collidepoint(event.pos):
                    self.select(action)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        return action
        return None

    def draw(self, window):
        window.fill("black")
        window.blit(self.background, (0, 0))
        window.blit(self.marker, self.marker_rect)
        elapsed = (pygame.time.get_ticks() - self.focus_started) / 1000
        for action, (image, rect) in self.buttons.items():
            if action == self.selected:
                grow = min(elapsed / 0.12, 1.0)
                angle = 4 * sin(tau * elapsed * 1.5) * grow
                image = pygame.transform.scale_by(image, 1 + 0.18 * grow)
                image = pygame.transform.rotate(image, angle)
                rect = image.get_rect(center=rect.center)
            self.hit_rects[action] = rect
            window.blit(image, rect)
