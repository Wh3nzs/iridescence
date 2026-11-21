from pathlib import Path

import pygame

from Character import Player
from DeathScreen import DeathScreen
from DexterBattle import DexterBattle
from DexterSprite import DexterSprite
from Effects import Lunge, Shake
from PlayerAttack import PlayerAttack

    
screenWidth, screenHeight = 800,600

pygame.init()

canvas = pygame.Surface((200,150))
shakeFrame = canvas.copy()
window = pygame.display.set_mode((screenWidth,screenHeight))
font = pygame.font.Font(None,14)
pygame.display.set_caption("Iridescence")
icon = pygame.image.load("assets/Heart.png").convert_alpha()
pygame.display.set_icon(icon)

dexterSprite = DexterSprite()
enemySprites = {}
placeholderEnemy = pygame.Surface((24, 24))
placeholderEnemy.fill("white")

deathScreen = DeathScreen()
winScreen = pygame.image.load(Path(__file__).parent / "Assets" / "WinScreen.png").convert_alpha()
winHint = pygame.font.Font(None, 24).render("Enter / Esc to return to menu", True, "white")
clock = pygame.time.Clock()


player = Player()
dexterBattle = None
fights = [
    # Name, description, enemy health (change each fight's last number).
    ("Emperess of Light", " Doge all her attacks", 50),
    ("Dexter Morgan", "Surive the Night", 50),
    ("Benjaman Nettenyaho", "Don't get bombed", 30)
    
]

tries = [0,0,0]
selected = 0
mode = "menu"
card = pygame.Rect(8,50,184,48)


def label(words,x,y):
    canvas.blit(font.render(words,True, "white"), (x,y))

arena = pygame.draw.rect(canvas,"white", (70,70,60,60), 1)
def startFight():
    global mode, screenShake, enemyShake, enemyLunge, playerTurn, dexterBattle
    tries[selected] += 1
    player.health = player.maxHealth
    mode = "battle"
    screenShake = Shake()
    enemyShake = Shake()
    enemyLunge = Lunge()
    player.spawn(arena)
    dexterSprite.reset()
    playerTurn = PlayerAttack(arena, enemyHp=fights[selected][2])
    dexterBattle = DexterBattle(arena, playerTurn) if fights[selected][0] == "Dexter Morgan" else None
    player.health = player.health
    if dexterBattle is None:
        playerTurn.start()


running = True
while running:

    dt = clock.tick(60) / 1000
    healthBefore = player.health
    
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
                    startFight()
                    healthBefore = player.health

        elif mode == "dead":
            action = deathScreen.actionFor(event)
            if action == "retry":
                startFight()
                healthBefore = player.health
            elif action == "menu":
                mode = "menu"

        elif mode == "win":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                mode = "menu"

        elif mode == "battle":
            if playerTurn.handleEvent(event):
                screenShake.trigger(0.5 if playerTurn.attackMode == "sequence" else 1.0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mode = "menu"

                elif event.key == pygame.K_SPACE:
                    if not playerTurn.active and dexterBattle is None:
                        playerTurn.start()
                 

        selected %= len(fights)
    if mode == "dead":
        deathScreen.draw(window)
        pygame.display.flip()
        continue

    if mode == "win":
        window.fill("black")
        pygame.transform.scale(winScreen, window.get_size(), window)
        window.blit(winHint, winHint.get_rect(midbottom=(window.get_width() // 2, window.get_height() - 20)))
        pygame.display.flip()
        continue

    canvas.fill((0,0,0))
    name, discription, enemyHp = fights[selected]


    if mode == "menu":
        previousIndex = (selected - 1) % len(fights)
        nextIndex = (selected + 1) % len(fights)

        # Previous fight
        pygame.draw.rect(canvas, (25, 25, 25), (8, 22, 184, 24))
        label(fights[previousIndex][0], 14, 28)

        # Selected fight
        pygame.draw.rect(canvas, (70, 50, 60), card)
        pygame.draw.rect(canvas, "white", card, 1)
        label(name, 14, 58)
        label(discription, 14, 78)
        label(f"Tryt: {tries[selected]}", 14,88)

        # Next fight
        pygame.draw.rect(canvas, (25, 25, 25), (8, 102, 184, 24))
        label(fights[nextIndex][0], 14, 108)
    else:

        attackStarted = False
        if playerTurn.active:
            playerTurn.update(dt)
        else:
            enemyShake.update(dt)
            enemyLunge.update(dt)
            player.update(pygame.key.get_pressed(), arena, dt)
            if dexterBattle is not None:
                attackStarted = dexterBattle.update(player, dt)
        if player.health < healthBefore:
            enemyShake.trigger()

        enemy = (dexterSprite.update(dt, playerTurn.hp) if name == "Dexter Morgan"
                 else enemySprites.get(name, placeholderEnemy))
        enemyRect = enemy.get_rect(midbottom=(arena.centerx, arena.top - 16))
        if attackStarted:
            # Aim from the portrait's feet through the top edge toward the heart.
            dx = player.rect.centerx - enemyRect.centerx
            dy = player.rect.centery - enemyRect.bottom
            reach = arena.top - enemyRect.bottom
            enemyLunge.trigger((round(dx * reach / dy), reach))
        enemyRect.move_ip(*enemyLunge.offset)
        enemyRect.move_ip(*enemyShake.offset)
        canvas.blit(enemy, enemyRect)

        if playerTurn.active:
            playerTurn.draw(canvas, font)
        else:
            if dexterBattle is not None:
                dexterBattle.draw(canvas)
            player.draw(canvas)
            pygame.draw.rect(canvas, "white", arena, 1)
            if dexterBattle is None:
                label("Space to attack", 70, 120)
            if player.health <= 0:
                deathScreen.show(playerTurn.hp, playerTurn.maxHp)
                mode = "dead"
                player.health = player.maxHealth
            elif playerTurn.hp <= 0 or (dexterBattle and dexterBattle.finished):
                mode = "win"

        hpLabel = font.render(f"H: {playerTurn.hp} / {playerTurn.maxHp}", True, "white")
        canvas.blit(hpLabel, hpLabel.get_rect(topright=(canvas.get_width() - 3, 7)))
        label(name,0,7)
        label("esc to return", 0,140)

        label("esc to return", 0,140)
        label(f" H: {player.health} / {player.maxHealth}",150,120)
        


    frame = canvas
    if mode == "battle":
        offset = screenShake.offset
        if offset != (0, 0):
            shakeFrame.fill("black")
            shakeFrame.blit(canvas, offset)
            frame = shakeFrame
        screenShake.update(dt)
    pygame.transform.scale(frame, window.get_size(), window)
    pygame.display.flip()

pygame.quit()
