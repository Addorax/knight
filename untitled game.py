import os
import random
import sqlite3
import sys

import pygame

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("untitled game")

ninja_img = pygame.image.load("data/ninja.png").convert_alpha()
ninja_attack_img = pygame.image.load("data/pixel_ninja_attack_wbackground.png").convert_alpha()
platform_img = pygame.image.load("data/platform.png").convert_alpha()
zombie_img_1 = pygame.image.load("data/zombie.png").convert_alpha()
zombie_img_2 = pygame.image.load("data/zombie_2.png").convert_alpha()
zombie_img_3 = pygame.image.load("data/zombie_3.png").convert_alpha()

menu_background = pygame.image.load("data/menu_background.png").convert()
menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))
dungeon_background = pygame.image.load("data/dungeonbg.png").convert()
dungeon_background = pygame.transform.scale(dungeon_background, (WIDTH, HEIGHT))
forest_background = pygame.image.load("data/forestbg.png").convert()
forest_background = pygame.transform.scale(forest_background, (WIDTH, HEIGHT))
cave_background = pygame.image.load("data/cavebg.png").convert()
cave_background = pygame.transform.scale(cave_background, (WIDTH, HEIGHT))

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

GRAVITY = 0.5
JUMP_STRENGTH = -10
ZOMBIE_DETECTION_RADIUS = 200

WORLD_WIDTH = WIDTH * 3


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.camera_speed = 0.1

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        target_x = -target.rect.centerx + int(WIDTH / 2)
        target_x = min(0, target_x)
        target_x = max(-(self.width - WIDTH), target_x)

        self.camera.x += (target_x - self.camera.x) * self.camera_speed
        self.camera.y = 0


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.transform.scale(platform_img, (width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Ninja(pygame.sprite.Sprite):
    def __init__(self, platforms):
        super().__init__()
        self.normal_image = ninja_img
        self.attack_image = ninja_attack_img
        self.image = self.normal_image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.speed = 5
        self.velocity_y = 0
        self.jumping = False
        self.platforms = platforms
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

        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        for platform in self.platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.jumping = False
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0

        if self.rect.bottom > HEIGHT:
            self.health = 0

    def jump(self):
        if not self.jumping:
            self.velocity_y = JUMP_STRENGTH
            self.jumping = True

    def move(self, dx):
        self.rect.x += dx * self.speed
        self.rect.x = max(0, min(self.rect.x, WORLD_WIDTH - self.rect.width))


class Zombie(pygame.sprite.Sprite):
    def __init__(self, platform, level):
        super().__init__()
        if level == 1:
            self.image = zombie_img_1
        elif level == 2:
            self.image = zombie_img_2
        else:
            self.image = zombie_img_3
            self.image = pygame.transform.scale(self.image, (self.image.get_width() // 4, self.image.get_height() // 4))
        self.rect = self.image.get_rect()
        self.platform = platform
        self.rect.bottom = platform.rect.top
        max_x = max(platform.rect.left, platform.rect.right - self.rect.width)
        self.rect.x = random.randint(platform.rect.left, max_x)
        self.speed = 1 + level * 0.5
        self.health = 100
        self.damage = 1 + level

    def update(self, ninja):
        dx = ninja.rect.centerx - self.rect.centerx
        dy = ninja.rect.centery - self.rect.centery
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist <= ZOMBIE_DETECTION_RADIUS:
            if abs(dx) > 0:
                direction = dx / abs(dx)
                new_x = self.rect.x + direction * self.speed
                if self.platform.rect.left <= new_x <= self.platform.rect.right - self.rect.width:
                    self.rect.x = new_x


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


def create_platforms():
    platforms = pygame.sprite.Group()
    platform_width = 200
    platform_height = 20
    base_platform_y = HEIGHT - 200
    gap = 100

    x = 0
    while x < WORLD_WIDTH:
        platform_y = base_platform_y + random.randint(-20, 20)
        platform = Platform(x, platform_y, platform_width, platform_height)
        if platform.rect.right <= WORLD_WIDTH:
            platforms.add(platform)
        x += platform_width + gap

    return platforms


def create_zombies(platforms, level):
    zombies = pygame.sprite.Group()
    if level == 1:
        num_zombies = 15
    elif level == 2:
        num_zombies = 20
    elif level == 3:
        num_zombies = 25

    zombies_per_platform = num_zombies // len(platforms)
    remaining_zombies = num_zombies % len(platforms)

    for platform in platforms:
        for _ in range(zombies_per_platform):
            zombie = Zombie(platform, level)
            zombies.add(zombie)

        if remaining_zombies > 0:
            zombie = Zombie(platform, level)
            zombies.add(zombie)
            remaining_zombies -= 1

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


main_menu = Screen()
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 - 150, 200, 50, "Начать", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, "Результаты", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Настройки звука", GRAY, GREEN))
main_menu.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 50, "Выход", GRAY, RED))

game_over_screen = Screen()
game_over_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Главное меню", GRAY, GREEN))

victory_screen = Screen()
victory_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Дальше", GRAY, GREEN))
victory_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 110, 200, 50, "Главное меню", GRAY, GREEN))

sound_settings = Screen()
sound_settings.add_button(Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 50, "Назад", GRAY, GREEN))

results_screen = Screen()
results_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 50, "Назад", GRAY, GREEN))

level_select_screen = LevelSelectScreen()

nickname_screen = Screen()
nickname_screen.add_button(Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Сохранить", GRAY, GREEN))

platforms = create_platforms()
ninja = Ninja(platforms)
zombies = create_zombies(platforms, 1)
camera = Camera(WORLD_WIDTH, HEIGHT)

clock = pygame.time.Clock()
running = True
current_state = "main_menu"
level = 1
music_volume = 0.5
sfx_volume = 0.5
zombies_killed = 0
total_score = 0
background_x = 0

font = pygame.font.Font(None, 36)

zombies_per_level = [
    [4, 5, 6],
    [6, 7, 8],
    [8, 9, 10]
]

nickname = ""
input_active = False
selected_level = 1


def update_volumes():
    pygame.mixer.music.set_volume(music_volume)
    attack_sound.set_volume(sfx_volume)
    zombie_hit_sound.set_volume(sfx_volume)
    game_over_sound.set_volume(sfx_volume)
    victory_sound.set_volume(sfx_volume)


def reset_player_position():
    ninja.rect.center = (WIDTH // 2, HEIGHT // 2)


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
                reset_player_position()
                platforms = create_platforms()
                ninja = Ninja(platforms)
                zombies = create_zombies(platforms, selected_level)
                camera = Camera(WORLD_WIDTH, HEIGHT)
        if current_state == "victory":
            if selected_level < 3:
                selected_level += 1
                current_state = "game"
                ninja.health = 100
                zombies_killed = 0
                reset_player_position()
                platforms = create_platforms()
                ninja = Ninja(platforms)
                zombies = create_zombies(platforms, selected_level)
                camera = Camera(WORLD_WIDTH, HEIGHT)
            else:
                current_state = "nickname"
                victory_sound.play()

        elif current_state == "game":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    ninja.jump()
                elif event.key == pygame.K_ESCAPE:
                    current_state = "main_menu"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ninja.attack()

        elif current_state == "game_over":
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
                    save_score(nickname, total_score)
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
        ninja.move(dx)

        background_x = 0
        background_x -= dx * 0.5
        background_x = max(-(WORLD_WIDTH - WIDTH), min(0, background_x))

        ninja.update()
        zombies.update(ninja)
        camera.update(ninja)

        if selected_level == 1:
            screen.blit(dungeon_background, (background_x, 0))
        elif selected_level == 2:
            screen.blit(forest_background, (background_x, 0))
        else:
            screen.blit(cave_background, (background_x, 0))

        for platform in platforms:
            screen.blit(platform.image, camera.apply(platform))
        for zombie in zombies:
            screen.blit(zombie.image, camera.apply(zombie))
        screen.blit(ninja.image, camera.apply(ninja))

        for zombie in zombies:
            if ninja.attacking and ninja.rect.colliderect(zombie.rect):
                zombie.health -= 10
                if zombie.health <= 0:
                    zombies.remove(zombie)
                    ninja.score += 10
                    total_score += 10
                    zombies_killed += 1
                    zombie_hit_sound.play()

            if ninja.rect.colliderect(zombie.rect) and not ninja.attacking:
                ninja.health -= zombie.damage
                if ninja.health <= 0:
                    current_state = "game_over"
                    game_over_sound.play()

        if len(zombies) == 0:
            if selected_level < 3:
                current_state = "victory"
                victory_sound.play()
            else:
                current_state = "nickname"
                victory_sound.play()

        if ninja.rect.bottom > HEIGHT:
            current_state = "game_over"
            game_over_sound.play()

        zombies_text = font.render(f"Зомби: {zombies_killed}/{len(zombies) + zombies_killed}", True, WHITE)
        health_text = font.render(f"Здоровье: {ninja.health}", True, WHITE)
        score_text = font.render(f"Счет: {total_score}", True, WHITE)
        level_text = font.render(f"Уровень: {selected_level}", True, WHITE)
        screen.blit(health_text, (10, 10))
        screen.blit(score_text, (10, 50))
        screen.blit(level_text, (10, 90))
        screen.blit(zombies_text, (10, 130))

        pygame.draw.rect(screen, RED, (WIDTH - 210, 10, 200, 20))
        pygame.draw.rect(screen, GREEN, (WIDTH - 210, 10, ninja.health * 2, 20))

    elif current_state == "game_over":
        screen.blit(menu_background, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        game_over_text = font.render("Игра окончена", True, WHITE)
        final_score_text = font.render(f"Финальный счет: {total_score}", True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 50))
        game_over_screen.draw(screen)

    elif current_state == "victory":
        screen.blit(menu_background, (0, 0))
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

        victory_screen.draw(screen)

    elif current_state == "sound_settings":
        screen.blit(menu_background, (0, 0))
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
        screen.blit(menu_background, (0, 0))
        main_menu.draw(screen)

    elif current_state == "results":
        screen.blit(menu_background, (0, 0))
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
        screen.blit(menu_background, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        level_select_text = font.render("Выберите уровень", True, WHITE)
        screen.blit(level_select_text, (WIDTH // 2 - level_select_text.get_width() // 2, HEIGHT // 2 - 200))
        level_select_screen.draw(screen)

    elif current_state == "nickname":
        screen.blit(menu_background, (0, 0))
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
