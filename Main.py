import pygame

from Character import Player
from DeathScreen import DeathScreen
from DexterBattle import DexterBattle
from Effects import Lunge, Shake
from PlayerAttack import PlayerAttack

    
WIDTH, HIGHT = 800,600

pygame.init()

canvas = pygame.Surface((200,150))
shake_frame = canvas.copy()
window = pygame.display.set_mode((WIDTH,HIGHT))
font = pygame.font.Font(None,14)
pygame.display.set_caption("Iridescence")
icon = pygame.image.load("assets/Heart.png").convert_alpha()
pygame.display.set_icon(icon)

enemy_sprites = {
    "Dexter Morgan": pygame.transform.scale(
        pygame.image.load("Assets/Dexter.png").convert_alpha(), (40, 40)
    ),
}
placeholder_enemy = pygame.Surface((24, 24))
placeholder_enemy.fill("white")

death_screen = DeathScreen()
clock = pygame.time.Clock()


player = Player()
dexter_battle = None
fights = [

    ("Emperess of Light", " Doge all her attacks"),
    ("Dexter Morgan", "Surive the Night"),
    ("Benjaman Nettenyaho", "Don't get bombed")
    
]

tries = [0,0,0]
selected = 0
mode = "menu"
card = pygame.Rect(8,50,184,48)


def label(words,x,y):
    canvas.blit(font.render(words,True, "white"), (x,y))

arena = pygame.draw.rect(canvas,"white", (70,70,60,60), 1)
def start_fight():
    global mode, screen_shake, enemy_shake, enemy_lunge, player_turn, dexter_battle
    tries[selected] += 1
    player.health = player.maxHealth
    mode = "battle"
    screen_shake = Shake()
    enemy_shake = Shake()
    enemy_lunge = Lunge()
    player.spawn(arena)
    player_turn = PlayerAttack(arena)
    dexter_battle = DexterBattle(arena, player_turn) if fights[selected][0] == "Dexter Morgan" else None
    player.health = player.health
    if dexter_battle is None:
        player_turn.start()


running = True
while running:

    dt = clock.tick(60) / 1000
    health_before = player.health
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif mode == "menu":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    selected += 1
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    selected -= 1
                elif event.key == pygame.K_RETURN:
                    start_fight()
                    health_before = player.health

        elif mode == "dead":
            action = death_screen.action_for(event)
            if action == "retry":
                start_fight()
                health_before = player.health
            elif action == "menu":
                mode = "menu"

        elif mode == "battle":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mode = "menu"

                elif event.key == pygame.K_SPACE:
                    if player_turn.active:
                        if player_turn.strike():
                            screen_shake.trigger()
                    elif dexter_battle is None:
                        player_turn.start()
                 

        selected %= len(fights)
    if mode == "dead":
        death_screen.draw(window)
        pygame.display.flip()
        continue

    canvas.fill((0,0,0))
    name, discription = fights[selected]


    if mode == "menu":
        previous_index = (selected - 1) % len(fights)
        next_index = (selected + 1) % len(fights)

        # Previous fight
        pygame.draw.rect(canvas, (25, 25, 25), (8, 22, 184, 24))
        label(fights[previous_index][0], 14, 28)

        # Selected fight
        pygame.draw.rect(canvas, (70, 50, 60), card)
        pygame.draw.rect(canvas, "white", card, 1)
        label(name, 14, 58)
        label(discription, 14, 78)
        label(f"Tryt: {tries[selected]}", 14,88)

        # Next fight
        pygame.draw.rect(canvas, (25, 25, 25), (8, 102, 184, 24))
        label(fights[next_index][0], 14, 108)
    else:

        attack_started = False
        if player_turn.active:
            player_turn.update(dt)
        else:
            enemy_shake.update(dt)
            enemy_lunge.update(dt)
            player.update(pygame.key.get_pressed(), arena, dt)
            if dexter_battle is not None:
                attack_started = dexter_battle.update(player, dt)
        if player.health < health_before:
            enemy_shake.trigger()

        enemy = enemy_sprites.get(name, placeholder_enemy)
        enemy_rect = enemy.get_rect(midbottom=(arena.centerx, arena.top - 16))
        if attack_started:
            # Aim from the portrait's feet through the top edge toward the heart.
            dx = player.rect.centerx - enemy_rect.centerx
            dy = player.rect.centery - enemy_rect.bottom
            reach = arena.top - enemy_rect.bottom
            enemy_lunge.trigger((round(dx * reach / dy), reach))
        enemy_rect.move_ip(*enemy_lunge.offset)
        enemy_rect.move_ip(*enemy_shake.offset)
        canvas.blit(enemy, enemy_rect)

        if player_turn.active:
            player_turn.draw(canvas, font)
        else:
            if dexter_battle is not None:
                dexter_battle.draw(canvas)
            player.draw(canvas)
            pygame.draw.rect(canvas, "white", arena, 1)
            if dexter_battle is None:
                label("Space to attack", 70, 120)
            if player.health <= 0:
                death_screen.show(player_turn.hp, player_turn.max_hp)
                mode = "dead"
                player.health = player.maxHealth
            elif player_turn.hp <= 0 or (dexter_battle and dexter_battle.finished):
                mode = "menu"

        hp_label = font.render(f"H: {player_turn.hp} / {player_turn.max_hp}", True, "white")
        canvas.blit(hp_label, hp_label.get_rect(topright=(canvas.get_width() - 3, 7)))
        label(name,0,7)
        label("esc to return", 0,140)

        label("esc to return", 0,140)
        label(f" H: {player.health} / {player.maxHealth}",150,120)
        


    frame = canvas
    if mode == "battle":
        offset = screen_shake.offset
        if offset != (0, 0):
            shake_frame.fill("black")
            shake_frame.blit(canvas, offset)
            frame = shake_frame
        screen_shake.update(dt)
    pygame.transform.scale(frame, window.get_size(), window)
    pygame.display.flip()

pygame.quit()