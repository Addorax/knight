import pygame
import sys

pygame.init()

width, height = 1024, 1024
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Главное меню")

white = (255, 255, 255)
black = (0, 0, 0)
gray = (200, 200, 200)
red = (255, 0, 0)
green = (0, 255, 0)

background = pygame.image.load("preview.jpg")
background = pygame.transform.scale(background, (width, height))

font = pygame.font.Font(None, 36)


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, black, self.rect, 2, border_radius=12)
        text_surface = font.render(self.text, True, black)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return True
        return False


buttons = [
    Button(412, 300, 200, 50, "Старт", gray, green),
    Button(412, 400, 200, 50, "Настройки", gray, white),
    Button(412, 500, 200, 50, "Рекорды", gray, white),
    Button(412, 600, 200, 50, "Выход", gray, red)
]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        for button in buttons:
            if button.handle_event(event):
                if button.text == "Выход":
                    running = False

    screen.blit(background, (0, 0))

    for button in buttons:
        button.check_hover(pygame.mouse.get_pos())
        button.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
