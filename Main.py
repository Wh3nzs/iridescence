import pygame
WIDTH, HIGHT = 800,600

pygame.init()

canvas = pygame.Surface((200,150))
window = pygame.display.set_mode((WIDTH,HIGHT))
font = pygame.font.Font(None,14)
pygame.display.set_caption("gmammama")

clock = pygame.time.Clock()



fights = [

    ("Emperess of Light", " Doge all her attacks"),
    ("Dexter Morgan", "Surive the Night"),
    ("Benjaman Nettenyaho", "Don't get bombed")
    
]
selected = 0
mode = "menu"
card = pygame.Rect(8,50,184,48)


def label(words,x,y):
    canvas.blit(font.render(words,True, "white"), (x,y))


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if mode == "menu":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    selected += 1
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    selected -= 1
                elif event.key == pygame.K_RETURN:
                    mode = "battle"

        elif mode == "battle":
             if event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_ESCAPE:
                     mode = "menu"
        
        if event.type == pygame.KEYDOWN and pygame.K_g:
            print(mode)
        selected %= len(fights)
        
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

        # Next fight
        pygame.draw.rect(canvas, (25, 25, 25), (8, 102, 184, 24))
        label(fights[next_index][0], 14, 108)
    else:
        label(name,15,17)
        pygame.draw.rect(canvas,"white", (60,40,80,80), 1)
        label("esc to return", 10,132)


    pygame.transform.scale(canvas, window.get_size(), window)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()