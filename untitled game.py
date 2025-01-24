import sqlite3
import sys

import pygame

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Untitled game")

ninja_img = pygame.image.load("ninja.png").convert_alpha()
ninja_attack_img = pygame.image.load("pixel_ninja_attack_wbackground.png").convert_alpha()
background_img = pygame.image.load("dungeonbg.png").convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
zombie_img = pygame.image.load("zombie.png").convert_alpha()

attack_sound = pygame.mixer.Sound("attack.wav")
zombie_hit_sound = pygame.mixer.Sound("zombie_hit.wav")
game_over_sound = pygame.mixer.Sound("game_over.wav")
victory_sound = pygame.mixer.Sound("victory.mp3")

pygame.mixer.music.load("background_music.mp3")
pygame.mixer.music.play(-1)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


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
        self.health = 100
        self.score = 0

    def attack(self):
        if not self.attacking and self.cooldown_timer == 0:
            self.attacking = True
            self.image = self.attack_image
            self.attack_timer = 30
            self.cooldown_timer = self.attack_cooldown
            attack_sound.play()

    def update(self):
        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False
                self.image = self.normal_image

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

    def move(self, dx, dy):
        new_x = self.rect.x + dx * self.speed
        new_y = self.rect.y + dy * self.speed

        if 0 <= new_x <= WIDTH - self.rect.width:
            self.rect.x = new_x

        if 0 <= new_y <= HEIGHT - self.rect.height:
            self.rect.y = new_y


class Zombie(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = zombie_img
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.speed = 2
        self.health = 100

    def update(self, ninja_x, ninja_y):
        dx = ninja_x - self.rect.centerx
        dy = ninja_y - self.rect.centery
        dist = max(abs(dx), abs(dy))
        if dist != 0:
            self.rect.x += self.speed * dx / dist
            self.rect.y += self.speed * dy / dist


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
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=12)
        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.text, True, BLACK)
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

    def clear_buttons(self):
        self.buttons = []


main_menu = Screen()
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 - 150, 200, 50, "Начать", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, "Результаты", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Настройки звука", GRAY,
                            GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 50, "Выход", GRAY, RED))

game_screen = Screen()

game_over_screen = Screen()
game_over_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Главное меню", GRAY,
                                   GREEN))

victory_screen = Screen()

sound_settings = Screen()
sound_settings.add_button(Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 50, "Назад", GRAY, GREEN))

second_screen = Screen()
second_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 170, 200, 50, "Сохранить результат",
                                GRAY, GREEN))

nickname_screen = Screen()
nickname_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Сохранить", GRAY,
                                  GREEN))

results_screen = Screen()
results_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 50, "Назад", GRAY, GREEN))

ninja = Ninja()
zombies = pygame.sprite.Group()

clock = pygame.time.Clock()
running = True
current_screen = main_menu
level = 1
zombie_spawn_timer = 0
music_volume = 0.5
sfx_volume = 0.5
zombies_killed = 0
screens_cleared = 0
zombies_per_screen = 3
max_screens = 3

font = pygame.font.Font(None, 36)


def update_volumes():
    pygame.mixer.music.set_volume(music_volume)
    attack_sound.set_volume(sfx_volume)
    zombie_hit_sound.set_volume(sfx_volume)
    game_over_sound.set_volume(sfx_volume)
    victory_sound.set_volume(sfx_volume)


def create_zombie():
    global zombies_killed, screens_cleared, current_screen
    if zombies_killed >= zombies_per_screen:
        zombies_killed = 0
        screens_cleared += 1
        if screens_cleared >= max_screens:
            current_screen = victory_screen
            victory_sound.play()
        else:
            zombies.empty()
    zombie = Zombie()
    zombies.add(zombie)


def save_score(nickname, score):
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores
                 (nickname TEXT, score INTEGER, date TEXT)''')
    c.execute("INSERT INTO scores VALUES (?, ?, datetime('now'))", (nickname, score))
    conn.commit()
    conn.close()


def get_top_scores(limit=10):
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute("SELECT nickname, score, date FROM scores ORDER BY score DESC LIMIT ?", (limit,))
    results = c.fetchall()
    conn.close()
    return results


nickname = ""
input_active = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        action = current_screen.handle_events(event)
        if action == "Начать":
            current_screen = game_screen
            ninja.health = 100
            ninja.score = 0
            level = 1
            zombies_killed = 0
            screens_cleared = 0
            zombies.empty()
            create_zombie()
        elif action == "Выход":
            running = False
        elif action == "Главное меню":
            current_screen = main_menu
        elif action == "Настройки звука":
            current_screen = sound_settings
        elif action == "Назад":
            current_screen = main_menu
        elif action == "Второй раунд":
            current_screen = second_screen
            ninja.health = 100
            level = 1
            zombies_killed = 0
            screens_cleared = 0
            zombies.empty()
            create_zombie()
        elif action == "Сохранить результат":
            current_screen = nickname_screen
        elif action == "Сохранить":
            if nickname:
                save_score(nickname, ninja.score)
                nickname = ""
                current_screen = main_menu
        elif action == "Результаты":
            current_screen = results_screen
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and (current_screen == game_screen or current_screen == second_screen):
                ninja.attack()
            elif current_screen == sound_settings:
                if event.pos[1] < HEIGHT // 2:
                    music_volume = max(0, min(1, (event.pos[0] - 100) / (WIDTH - 200)))
                else:
                    sfx_volume = max(0, min(1, (event.pos[0] - 100) / (WIDTH - 200)))
                update_volumes()
            elif current_screen == nickname_screen:
                input_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50)
                if input_rect.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                current_screen = main_menu
            elif current_screen == nickname_screen:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        nickname = nickname[:-1]
                    else:
                        nickname += event.unicode

    if current_screen == game_screen or current_screen == second_screen:
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_d] - keys[pygame.K_a]
        dy = keys[pygame.K_s] - keys[pygame.K_w]
        ninja.move(dx, dy)

        ninja.update()
        zombies.update(ninja.rect.centerx, ninja.rect.centery)

        zombie_spawn_timer += 1
        if zombie_spawn_timer >= 180:
            create_zombie()
            zombie_spawn_timer = 0

        for zombie in zombies:
            if ninja.attacking and ninja.rect.colliderect(zombie.rect):
                zombie.health -= 10
                if zombie.health <= 0:
                    zombies.remove(zombie)
                    ninja.score += 10
                    zombies_killed += 1
                    zombie_hit_sound.play()
                    if zombies_killed >= zombies_per_screen:
                        create_zombie()

            if ninja.rect.colliderect(zombie.rect) and not ninja.attacking:
                ninja.health -= 1
                if ninja.health <= 0:
                    current_screen = nickname_screen
                    game_over_sound.play()

        if not zombies:
            create_zombie()

        screen.blit(background_img, (0, 0))
        zombies.draw(screen)
        screen.blit(ninja.image, ninja.rect)

        health_text = font.render(f"Здоровье: {ninja.health}", True, WHITE)
        score_text = font.render(f"Счет: {ninja.score}", True, WHITE)
        level_text = font.render(f"Экран: {screens_cleared + 1}/{max_screens}", True, WHITE)
        zombies_text = font.render(f"Зомби: {zombies_killed}/{zombies_per_screen}", True, WHITE)
        screen.blit(health_text, (10, 10))
        screen.blit(score_text, (10, 50))
        screen.blit(level_text, (10, 90))
        screen.blit(zombies_text, (10, 130))

        pygame.draw.rect(screen, RED, (WIDTH - 210, 10, 200, 20))
        pygame.draw.rect(screen, GREEN, (WIDTH - 210, 10, ninja.health * 2, 20))

        if current_screen == second_screen and screens_cleared >= max_screens:
            current_screen = victory_screen
            victory_sound.play()

    elif current_screen == game_over_screen:
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        game_over_text = font.render("Игра окончена", True, WHITE)
        final_score_text = font.render(f"Финальный счет: {ninja.score}", True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 50))
        current_screen.draw(screen)
    elif current_screen == victory_screen:
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        victory_text = font.render("Победа!", True, WHITE)
        final_score_text = font.render(f"Финальный счет: {ninja.score}", True, WHITE)
        screens_cleared_text = font.render(f"Уровней пройдено: {screens_cleared}", True, WHITE)
        zombies_killed_text = font.render(f"Всего зомби убито: {screens_cleared * zombies_per_screen}", True, WHITE)
        screen.blit(victory_text, (WIDTH // 2 - victory_text.get_width() // 2, HEIGHT // 2 - 150))
        screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(screens_cleared_text, (WIDTH // 2 - screens_cleared_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(zombies_killed_text, (WIDTH // 2 - zombies_killed_text.get_width() // 2, HEIGHT // 2))
        victory_screen.clear_buttons()
        victory_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Второй раунд", GRAY, GREEN))
        victory_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 110, 200, 50, "Главное меню", GRAY, GREEN))
        current_screen.draw(screen)
    elif current_screen == sound_settings:
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        music_text = font.render("Громкость музыки", True, WHITE)
        sfx_text = font.render("Громкость эффектов", True, WHITE)
        screen.blit(music_text, (100, HEIGHT // 2 - 100))
        screen.blit(sfx_text, (100, HEIGHT // 2 + 50))

        pygame.draw.rect(screen, GRAY, (100, HEIGHT // 2 - 50, WIDTH - 200, 20))
        pygame.draw.rect(screen, GREEN, (100, HEIGHT // 2 - 50, int(music_volume * (WIDTH - 200)), 20))

        pygame.draw.rect(screen, GRAY, (100, HEIGHT // 2 + 100, WIDTH - 200, 20))
        pygame.draw.rect(screen, GREEN, (100, HEIGHT // 2 + 100, int(sfx_volume * (WIDTH - 200)), 20))

        current_screen.draw(screen)
    elif current_screen == main_menu:
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        main_menu.draw(screen)
    elif current_screen == nickname_screen:
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        input_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50)
        pygame.draw.rect(screen, WHITE, input_rect)
        pygame.draw.rect(screen, BLACK, input_rect, 2)

        nickname_text = font.render(nickname, True, BLACK)
        screen.blit(nickname_text, (input_rect.x + 5, input_rect.y + 5))

        prompt_text = font.render("Введите свой ник:", True, WHITE)
        screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 75))

        current_screen.draw(screen)
    elif current_screen == results_screen:
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        results = get_top_scores()
        title_text = font.render("Лучшие результаты", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))

        for i, (nickname, score, date) in enumerate(results):
            result_text = font.render(f"{i + 1}. {nickname}: {score} ({date})", True, WHITE)
            screen.blit(result_text, (WIDTH // 2 - result_text.get_width() // 2, 100 + i * 40))

        current_screen.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
