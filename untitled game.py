import os
import random
import sqlite3
import sys

import pygame

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ninja vs Zombies")

ninja_img = pygame.image.load("data/ninja.png").convert_alpha()
ninja_attack_img = pygame.image.load("data/pixel_ninja_attack_wbackground.png").convert_alpha()
background_img_lvl1 = pygame.image.load("data/dungeonbg.png").convert()
background_img_lvl2 = pygame.image.load("data/forestbg.png").convert()
background_img_lvl3 = pygame.image.load("data/cavebg.png").convert()
background_img_lvl1 = pygame.transform.scale(background_img_lvl1, (WIDTH * 3, HEIGHT))
background_img_lvl2 = pygame.transform.scale(background_img_lvl2, (WIDTH * 3, HEIGHT))
background_img_lvl3 = pygame.transform.scale(background_img_lvl3, (WIDTH * 3, HEIGHT))
zombie_img = pygame.image.load("data/zombie.png").convert_alpha()

attack_sound = pygame.mixer.Sound("data/attack.wav")
zombie_hit_sound = pygame.mixer.Sound("data/zombie_hit.wav")
game_over_sound = pygame.mixer.Sound("data/game_over.wav")
victory_sound = pygame.mixer.Sound("data/victory.mp3")

pygame.mixer.music.load("data/background_music.mp3")
pygame.mixer.music.play(-1)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

zombies_per_screen = 4
max_screens = 3


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

        if 0 <= new_x <= WIDTH * 3 - self.rect.width:
            self.rect.x = new_x

        if 0 <= new_y <= HEIGHT - self.rect.height:
            self.rect.y = new_y


class Zombie(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.image = zombie_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(WIDTH, WIDTH * 3 - self.rect.width)
        self.rect.y = random.randint(0, HEIGHT - self.rect.height)
        self.speed = 2 + level * 0.5
        self.health = 100
        self.damage = 1 + level

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


class LevelSelectScreen(Screen):
    def __init__(self):
        super().__init__()
        self.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 50, "Уровень 1", GRAY, GREEN))
        self.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2, 200, 50, "Уровень 2", GRAY, GREEN))
        self.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Уровень 3", GRAY, GREEN))


main_menu = Screen()
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 - 150, 200, 50, "Начать", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, "Результаты", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Настройки звука", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 50, "Выход", GRAY, RED))

game_over_screen = Screen()
game_over_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Главное меню", GRAY, GREEN))

victory_screen = Screen()

sound_settings = Screen()
sound_settings.add_button(Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 50, "Назад", GRAY, GREEN))

results_screen = Screen()
results_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 50, "Назад", GRAY, GREEN))

level_select_screen = LevelSelectScreen()

nickname_screen = Screen()
nickname_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Сохранить", GRAY, GREEN))

ninja = Ninja()
zombies = pygame.sprite.Group()

clock = pygame.time.Clock()
running = True
current_state = "main_menu"
level = 1
music_volume = 0.5
sfx_volume = 0.5
zombies_killed = 0

font = pygame.font.Font(None, 36)

zombies_per_level = [
    [4, 5, 6],
    [6, 7, 8],
    [8, 9, 10]
]

nickname = ""
input_active = False
selected_level = 1
camera_x = 0
current_screen = 0


def update_volumes():
    pygame.mixer.music.set_volume(music_volume)
    attack_sound.set_volume(sfx_volume)
    zombie_hit_sound.set_volume(sfx_volume)
    game_over_sound.set_volume(sfx_volume)
    victory_sound.set_volume(sfx_volume)


def create_zombies(level, screen):
    zombies = pygame.sprite.Group()
    num_zombies = zombies_per_level[level - 1][screen]
    for _ in range(num_zombies):
        zombie = Zombie(level)
        zombies.add(zombie)
    return zombies


def initialize_database():
    db_path = 'data/game_scores.db'
    if not os.path.exists('data'):
        os.makedirs('data')

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
    table_exists = c.fetchone()

    if not table_exists:
        c.execute('''CREATE TABLE scores
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nickname TEXT,
                      score INTEGER,
                      date TEXT)''')
    else:
        c.execute("PRAGMA table_info(scores)")
        columns = [column[1] for column in c.fetchall()]
        required_columns = ['id', 'nickname', 'score', 'date']

        for column in required_columns:
            if column not in columns:
                c.execute(f"ALTER TABLE scores ADD COLUMN {column} TEXT")

    conn.commit()
    conn.close()


def save_score(nickname, score):
    initialize_database()
    conn = sqlite3.connect('data/game_scores.db')
    c = conn.cursor()
    c.execute("INSERT INTO scores (nickname, score, date) VALUES (?, ?, datetime('now'))", (nickname, score))
    conn.commit()
    conn.close()


def get_top_scores(limit=10):
    initialize_database()
    conn = sqlite3.connect('data/game_scores.db')
    c = conn.cursor()
    c.execute("SELECT nickname, score, date FROM scores ORDER BY score DESC LIMIT ?", (limit,))
    results = c.fetchall()
    conn.close()
    return results


def reset_player_position():
    ninja.rect.x = WIDTH // 2
    ninja.rect.y = HEIGHT // 2
    global camera_x
    camera_x = 0


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if current_state == "main_menu":
            action = main_menu.handle_events(event)
            if action == "Начать":
                current_state = "level_select"
            elif action == "Результаты":
                current_state = "results"
            elif action == "Настройки звука":
                current_state = "sound_settings"
            elif action == "Выход":
                running = False

        elif current_state == "level_select":
            action = level_select_screen.handle_events(event)
            if action in ["Уровень 1", "Уровень 2", "Уровень 3"]:
                selected_level = int(action.split()[-1])
                current_state = "game"
                ninja.health = 100
                ninja.score = 0
                zombies_killed = 0
                camera_x = 0
                ninja.rect.x = WIDTH // 2
                ninja.rect.y = HEIGHT // 2
                current_screen = 0
                zombies = create_zombies(selected_level, current_screen)

        elif current_state == "game":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ninja.attack()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_state = "main_menu"

        elif current_state == "game_over" or current_state == "victory":
            action = game_over_screen.handle_events(event)
            if action == "Главное меню":
                current_state = "nickname"
                reset_player_position()

        elif current_state == "sound_settings":
            action = sound_settings.handle_events(event)
            if action == "Назад":
                current_state = "main_menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[1] < HEIGHT // 2:
                    music_volume = max(0, min(1, (event.pos[0] - 100) / (WIDTH - 200)))
                else:
                    sfx_volume = max(0, min(1, (event.pos[0] - 100) / (WIDTH - 200)))
                update_volumes()

        elif current_state == "results":
            action = results_screen.handle_events(event)
            if action == "Назад":
                current_state = "main_menu"

        elif current_state == "nickname":
            action = nickname_screen.handle_events(event)
            if action == "Сохранить":
                if nickname:
                    save_score(nickname, ninja.score)
                    nickname = ""
                    current_state = "main_menu"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_state = "main_menu"
                elif event.key == pygame.K_RETURN:
                    if nickname:
                        save_score(nickname, ninja.score)
                        nickname = ""
                        current_state = "main_menu"
                elif event.key == pygame.K_BACKSPACE:
                    nickname = nickname[:-1]
                else:
                    nickname += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                input_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50)
                if input_rect.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False

    if current_state == "game":
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_d] - keys[pygame.K_a]
        dy = keys[pygame.K_s] - keys[pygame.K_w]
        ninja.move(dx, dy)

        camera_x = max(0, min(ninja.rect.x - WIDTH // 2, WIDTH * 2))

        ninja.update()
        zombies.update(ninja.rect.centerx, ninja.rect.centery)

        if selected_level == 1:
            screen.blit(background_img_lvl1, (-camera_x, 0))
        elif selected_level == 2:
            screen.blit(background_img_lvl2, (-camera_x, 0))
        else:
            screen.blit(background_img_lvl3, (-camera_x, 0))

        for zombie in zombies:
            if ninja.attacking and ninja.rect.colliderect(zombie.rect):
                zombie.health -= 10
                if zombie.health <= 0:
                    zombies.remove(zombie)
                    ninja.score += 10
                    zombies_killed += 1
                    zombie_hit_sound.play()

            if ninja.rect.colliderect(zombie.rect) and not ninja.attacking:
                ninja.health -= zombie.damage
                if ninja.health <= 0:
                    current_state = "game_over"
                    game_over_sound.play()

        if len(zombies) == 0:
            current_screen += 1
            if current_screen > 2:
                current_state = "victory"
                victory_sound.play()
            else:
                zombies = create_zombies(selected_level, current_screen)

        for zombie in zombies:
            screen.blit(zombie.image, (zombie.rect.x - camera_x, zombie.rect.y))
        screen.blit(ninja.image, (ninja.rect.x - camera_x, ninja.rect.y))

        zombies_text = font.render(f"Зомби: {zombies_killed}/{sum(zombies_per_level[selected_level - 1])}", True, WHITE)
        health_text = font.render(f"Здоровье: {ninja.health}", True, WHITE)
        score_text = font.render(f"Счет: {ninja.score}", True, WHITE)
        level_text = font.render(f"Уровень: {selected_level}", True, WHITE)
        screen.blit(health_text, (10, 10))
        screen.blit(score_text, (10, 50))
        screen.blit(level_text, (10, 90))
        screen.blit(zombies_text, (10, 130))

        pygame.draw.rect(screen, RED, (WIDTH - 210, 10, 200, 20))
        pygame.draw.rect(screen, GREEN, (WIDTH - 210, 10, ninja.health * 2, 20))

    elif current_state == "game_over":
        screen.blit(background_img_lvl1, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        game_over_text = font.render("Игра окончена", True, WHITE)
        final_score_text = font.render(f"Финальный счет: {ninja.score}", True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 50))
        game_over_screen.draw(screen)
    elif current_state == "victory":
        screen.blit(background_img_lvl1, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        victory_text = font.render("Победа!", True, WHITE)
        final_score_text = font.render(f"Финальный счет: {ninja.score}", True, WHITE)
        level_completed_text = font.render(f"Уровень пройден: {selected_level}", True, WHITE)
        zombies_killed_text = font.render(f"Всего зомби убито: {zombies_killed}", True, WHITE)
        screen.blit(victory_text, (WIDTH // 2 - victory_text.get_width() // 2, HEIGHT // 2 - 150))
        screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(level_completed_text, (WIDTH // 2 - level_completed_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(zombies_killed_text, (WIDTH // 2 - zombies_killed_text.get_width() // 2, HEIGHT // 2))

        if selected_level < 3:
            victory_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Дальше", GRAY, GREEN))
        victory_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 110, 200, 50, "Главное меню", GRAY, GREEN))
        victory_screen.draw(screen)

        action = victory_screen.handle_events(event)
        if action == "Дальше":
            selected_level += 1
            current_state = "level_select"
            victory_screen.clear_buttons()
        elif action == "Главное меню":
            current_state = "nickname"
            reset_player_position()

    elif current_state == "sound_settings":
        screen.blit(background_img_lvl1, (0, 0))
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

        sound_settings.draw(screen)
    elif current_state == "main_menu":
        screen.blit(background_img_lvl1, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        main_menu.draw(screen)
    elif current_state == "results":
        screen.blit(background_img_lvl1, (0, 0))
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

        results_screen.draw(screen)
    elif current_state == "level_select":
        screen.blit(background_img_lvl1, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        level_select_text = font.render("Выберите уровень", True, WHITE)
        screen.blit(level_select_text, (WIDTH // 2 - level_select_text.get_width() // 2, HEIGHT // 2 - 200))
        level_select_screen.draw(screen)
    elif current_state == "nickname":
        screen.blit(background_img_lvl1, (0, 0))
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

        nickname_screen.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
