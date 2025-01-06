import pygame
import sys

pygame.init()
width, height = 1920, 1000
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


main_screen = Screen()
main_screen.add_button(Button(412, 300, 200, 50, "Старт", gray, green))
main_screen.add_button(Button(412, 400, 200, 50, "Настройки", gray, white))
main_screen.add_button(Button(412, 500, 200, 50, "Рекорды", gray, white))
main_screen.add_button(Button(412, 600, 200, 50, "Выход", gray, red))

game_screen = Screen()
game_background = pygame.image.load("trueblack_screen.png")
game_background = pygame.transform.scale(game_background, (width, height))
ninja = pygame.image.load("pixel_ninja_standing_wbackground.png")
ninja_rect = ninja.get_rect(center=(width // 2, height // 2))
game_screen.add_button(Button(412, 900, 200, 50, "Назад", gray, red))

settings_menu = Screen()
settings_menu.add_button(Button(412, 400, 200, 50, "Звук", gray, white))
settings_menu.add_button(Button(412, 500, 200, 50, "Графика", gray, white))
settings_menu.add_button(Button(412, 600, 200, 50, "Назад", gray, red))

records_menu = Screen()
records_menu.add_button(Button(412, 400, 200, 50, "Рекорды игрока", gray, white))
records_menu.add_button(Button(412, 500, 200, 50, "Топ 10", gray, white))
records_menu.add_button(Button(412, 600, 200, 50, "Назад", gray, red))

info_window = Screen()
info_window.add_button(Button(412, 400, 200, 50, "Закрыть", gray, red))

graphics_menu = Screen()
graphics_menu.add_button(Button(412, 500, 200, 50, "Назад", gray, red))

sound_menu = Screen()
sound_menu.add_button(Button(412, 500, 200, 50, "Назад", gray, red))

current_screen = main_screen
show_ninja = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        action = current_screen.handle_events(event)
        if action == "Назад":
            if current_screen in [graphics_menu, sound_menu, records_menu]:
                current_screen = settings_menu
            elif current_screen == settings_menu:
                current_screen = main_screen
            elif current_screen == info_window:
                current_screen = main_screen
            elif current_screen == game_screen:
                current_screen = main_screen
                show_ninja = False
        elif action == "Старт":
            current_screen = game_screen
            show_ninja = True
        elif action == "Настройки":
            current_screen = settings_menu
        elif action == "Рекорды":
            current_screen = records_menu
        elif action == "Закрыть":
            current_screen = main_screen
        elif action == "Звук":
            current_screen = sound_menu
        elif action == "Графика":
            current_screen = graphics_menu
        elif action == "Топ 10":
            current_screen = records_menu
        elif action == "Выход":
            pygame.quit()
            sys.exit()

    if current_screen == game_screen:
        screen.blit(game_background, (0, 0))
        if show_ninja:
            screen.blit(ninja, ninja_rect)
    else:
        screen.blit(background, (0, 0))

    current_screen.draw(screen)
    pygame.display.flip()
