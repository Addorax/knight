import pygame
import sys
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("untitled game.py")

ninja_img = pygame.image.load("ninja.png").convert_alpha()
ninja_attack_img = pygame.image.load("pixel_ninja_attack_wbackground.png").convert_alpha()
background_img = pygame.image.load("dungeonbg.png").convert()
zombie_img = pygame.image.load("zombie.png").convert_alpha()

white = (255, 255, 255)
black = (0, 0, 0)
gray = (200, 200, 200)
red = (255, 0, 0)
green = (0, 255, 0)


class Ninja(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.normal_image = ninja_img
        self.attack_image = ninja_attack_img
        self.image = self.normal_image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.speed = 5
        self.attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 60
        self.cooldown_timer = 0

    def attack(self):
        if not self.attacking and self.cooldown_timer == 0:
            self.attacking = True
            self.image = self.attack_image
            self.attack_timer = 30
            self.cooldown_timer = self.attack_cooldown

    def update(self):
        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False
                self.image = self.normal_image

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1


class Zombie(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = zombie_img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = HEIGHT - 250
        self.speed = 2

    def update(self, ninja_x):
        if abs(self.rect.x - ninja_x) < 200:
            if self.rect.x < ninja_x:
                self.rect.x += self.speed
            elif self.rect.x > ninja_x:
                self.rect.x -= self.speed


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
        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.text, True, black)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return True
        return False


class Screen:
    def __init__(self):
        self.buttons = []

    def add_button(self, button):
        self.buttons.append(button)

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)

    def handle_events(self, event):
        for button in self.buttons:
            button.check_hover(pygame.mouse.get_pos())
            if button.handle_event(event):
                return button.text
        return None


main_menu = Screen()
main_menu.add_button(Button(300, 200, 200, 50, "Начать", gray, green))
main_menu.add_button(Button(300, 300, 200, 50, "Выход", gray, red))

game_screen = Screen()

name_screen = Screen()
name_screen.add_button(Button(300, 200, 200, 50, "Продолжить", gray, green))

ninja = Ninja()
zombies = pygame.sprite.Group()
bg_width = background_img.get_width()
tiles = int(WIDTH / bg_width) + 2
scroll = 0


def create_zombie():
    x = random.randint(0, bg_width - 1) + scroll
    zombie = Zombie(x)
    zombies.add(zombie)


for a in range(tiles):
    create_zombie()

clock = pygame.time.Clock()
running = True
current_screen = main_menu

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        action = current_screen.handle_events(event)
        if action == "Начать":
            current_screen = game_screen
        elif action == "Выход":
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and current_screen == game_screen:
                ninja.attack()

    if current_screen == game_screen:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            scroll += ninja.speed
        if keys[pygame.K_d]:
            scroll -= ninja.speed

        ninja.update()
        zombies.update(WIDTH // 2 - scroll)

        for i in range(0, tiles):
            screen.blit(background_img, (i * bg_width + scroll, 0))

        if abs(scroll) > bg_width:
            scroll = scroll % bg_width
            create_zombie()

        for zombie in zombies:
            screen.blit(zombie.image, (zombie.rect.x + scroll, zombie.rect.y))

        screen.blit(ninja.image, ninja.rect)
    else:
        current_screen.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
