import pygame

class Player():
    def __init__(self):
        heart = pygame.image.load("assets/Heart.png").convert_alpha()
        scaled = pygame.transform.scale(heart, (8, 8))
        self.image = scaled.subsurface(scaled.get_bounding_rect()).copy()
        self.rect = self.image.get_rect()
        self.position = pygame.Vector2(self.rect.center)
        self.speed = 60
        self.health = 32
    def spawn(self, arena):
        self.position.update(arena.center)
        self.rect.center = arena.center

    def takeDamage(self,damage):
        self.health -= damage

    def update(self,keys,arena, dt):
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        up = keys[pygame.K_w] or keys[pygame.K_UP]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]

        direction = pygame.Vector2(int(right) - int(left), int(down) - int(up))

        if direction.length_squared() > 0:
            self.position += direction.normalize() * self.speed * dt


        self.rect.center = round(self.position.x), round(self.position.y)
        before = self.rect.center
        self.rect.clamp_ip(arena.inflate(-2, -2))

        if self.rect.centerx != before[0]:
            self.position.x = self.rect.centerx
        if self.rect.centery != before[1]:
            self.position.y = self.rect.centery

        print(self.position)

    def showHealth(self):
        return str(self.health)
    def draw(self, surface):
        surface.blit(self.image, self.rect)


