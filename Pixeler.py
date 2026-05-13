import pygame
import sys
import os
import math

# --- 1. INITIALIZATION ---
pygame.init()
monitor_info = pygame.display.Info()
SCREEN_WIDTH = monitor_info.current_w
SCREEN_HEIGHT = monitor_info.current_h
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("PIXELER")

clock = pygame.time.Clock()
FPS = 60
TILE_SIZE = 60 

# Physics
GRAVITY = 0.8
PLAYER_MOMENTUM = 0.7
PLAYER_JUMP_FORCE = -20.0 
FRICTION = 0.12

# Colors (for fallbacks)
SKY_BLUE = (135, 206, 235)
DIRT, GRASS = (100, 60, 30), (50, 180, 50)
WHITE, BLACK, GOLD = (255, 255, 255), (0, 0, 0), (255, 215, 0)

# --- AVATAR CONFIGURATION ---
# Replace filenames with your actual sprite paths
AVATAR_OPTIONS = [
    {"name": "Sky Blue", "color": (50, 100, 255), "path": "blue_guy.png"},
    {"name": "Forest Green", "color": (34, 139, 34), "path": "green_guy.png"},
    {"name": "Strawberry Red", "color": (220, 50, 50), "path": "red_guy.png"},
    {"name": "Pretty Purple", "color": (150, 50, 255), "path": "purple_guy.png"},
    {"name": "Glorious Gold", "color": (255, 200, 0), "path": "gold_guy.png"}
]

# --- 2. THE MAP DATA ---
LEVELS = [
    [ # LEVEL 1
        "..................................................",
        "..................................................",
        "..................C..C..C.........................",
        "..................1111111.......................G.",
        ".........................................E........",
        "......................................111111111111",
        "11111111111111111111111111111111111111111111111111",
    ],
    [ # LEVEL 2
        "..................................................",
        ".......................C..........................",
        ".....................11111........................",
        ".........C.........................C..............",
        "......111111....................111111............",
        "................E.........E.....................G.",
        "...111.......1111111.....1111111.......11111111111",
        "11111111............11111.......111111111111111111",
    ],
    [ # LEVEL 3
        "..................................................",
        "................................C.................",
        "................E............111111...............",
        "..............111111..............................",
        ".......C...............E...............C..........",
        "....111111...........111111.........111111........",
        "................................................G.",
        "..........E...................E...........11111111",
        "........111111..............111111................",
        "111111..........1111111111..........11111111111111",
    ],
    [ # LEVEL 4
        "........................C.........................",
        ".......................111........................",
        "............E.........................E...........",
        "..........11111.....................11111.........",
        "...................C.........C....................",
        ".................1111.......1111..................",
        "....C..........................................G..",
        "..1111..........E........E.........E.......1111111",
        "..............1111......1111......1111............",
        "111....11111.......111.......111.......11111111111",
    ]
]

# --- 3. CLASSES ---

class Player(pygame.sprite.Sprite):
    def __init__(self, avatar_data):
        super().__init__()
        # Try to load sprite, otherwise draw a box
        if os.path.exists(avatar_data["path"]):
            self.image = pygame.image.load(avatar_data["path"]).convert_alpha()
            self.image = pygame.transform.scale(self.image, (50, 70))
        else:
            self.image = pygame.Surface((50, 70))
            self.image.fill(avatar_data["color"])
            pygame.draw.circle(self.image, WHITE, (15, 20), 4)
            pygame.draw.circle(self.image, WHITE, (35, 20), 4)

        self.rect = self.image.get_rect()
        self.vel_x, self.vel_y = 0, 0
        self.on_ground = False
        self.score, self.lives = 0, 3

    def reset_pos(self):
        self.rect.topleft = (150, SCREEN_HEIGHT - 450)
        self.vel_x, self.vel_y = 0, 0

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.vel_x -= PLAYER_MOMENTUM
        elif keys[pygame.K_RIGHT]: self.vel_x += PLAYER_MOMENTUM
        else: self.vel_x *= (1 - FRICTION)

        self.vel_x = max(-9, min(9, self.vel_x))
        self.vel_y += GRAVITY
        
        # Physics Collision
        self.rect.x += self.vel_x
        for block in platforms:
            if self.rect.colliderect(block.rect):
                if self.vel_x > 0: self.rect.right = block.rect.left
                elif self.vel_x < 0: self.rect.left = block.rect.right
                self.vel_x = 0

        self.on_ground = False
        self.rect.y += self.vel_y
        for block in platforms:
            if self.rect.colliderect(block.rect):
                if self.vel_y > 0:
                    self.rect.bottom = block.rect.top
                    self.on_ground = True
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = block.rect.bottom
                    self.vel_y = 0

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = PLAYER_JUMP_FORCE

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        if os.path.exists('enemy.png'):
            self.image = pygame.image.load('enemy.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (50, 50))
        else:
            self.image = pygame.Surface((50, 50))
            self.image.fill((200, 50, 50))
            
        self.rect = self.image.get_rect(topleft=(x, y))
        self.direction, self.speed = 1, 3

    def update(self, platforms):
        self.rect.x += self.direction * self.speed
        if any(self.rect.colliderect(p.rect) for p in platforms):
            self.direction *= -1
        
        # Ledge Check
        look_ahead = self.rect.right if self.direction > 0 else self.rect.left
        test_rect = pygame.Rect(look_ahead, self.rect.bottom + 1, 1, 1)
        if not any(test_rect.colliderect(p.rect) for p in platforms):
            self.direction *= -1

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        if os.path.exists('coin.png'):
            self.image = pygame.image.load('coin.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (40, 40))
        else:
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(self.image, GOLD, (15, 15), 15)
        self.rect = self.image.get_rect(center=(x + TILE_SIZE//2, y + TILE_SIZE//2))

class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        if os.path.exists('goal.png'):
            self.image = pygame.image.load('goal.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (60, 120))
        else:
            self.image = pygame.Surface((60, 120), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (200, 200, 200), (25, 0, 10, 120)) 
            pygame.draw.polygon(self.image, (255, 50, 50), [(25, 0), (60, 25), (25, 50)]) 
        self.rect = self.image.get_rect(topleft=(x, y - 60))

# --- CAMERA & HELPERS ---

class Camera:
    def __init__(self):
        self.offset = 0
    def update(self, target, level_width):
        self.offset = -target.rect.centerx + SCREEN_WIDTH // 2
        self.offset = min(0, max(self.offset, -(level_width - SCREEN_WIDTH)))
    def apply(self, entity):
        return entity.rect.move(self.offset, 0)

def load_level(level_index, player, groups):
    for g in groups: g.empty()
    all_sprites, platforms, enemies, coins, goals = groups
    level_map = LEVELS[level_index]
    level_width = len(level_map[0]) * TILE_SIZE
    all_sprites.add(player); player.reset_pos()
    v_offset = SCREEN_HEIGHT - (len(level_map) * TILE_SIZE)

    for r_idx, row in enumerate(level_map):
        for c_idx, char in enumerate(row):
            x, y = c_idx * TILE_SIZE, r_idx * TILE_SIZE + v_offset
            if char == '1':
                is_grass = r_idx > 0 and level_map[r_idx-1][c_idx] == '.'
                p = pygame.sprite.Sprite()
                p.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                p.image.fill(GRASS if is_grass else DIRT)
                p.rect = p.image.get_rect(topleft=(x, y))
                platforms.add(p); all_sprites.add(p)
            elif char == 'E':
                e = Enemy(x, y + 10); enemies.add(e); all_sprites.add(e)
            elif char == 'C':
                c = Coin(x, y); coins.add(c); all_sprites.add(c)
            elif char == 'G':
                g = Goal(x, y); goals.add(g); all_sprites.add(g)
    return level_width

def draw_text(screen, text, size, color, x, y):
    font = pygame.font.SysFont("Arial", size, bold=True)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(x, y)))

# --- 5. MAIN LOOP ---

def main():
    selected_avatar_idx = 0
    player = None
    groups = [pygame.sprite.Group() for _ in range(5)]
    camera = Camera()
    game_state = "START_MENU"
    current_level = 0
    level_width = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
                
                if game_state == "START_MENU":
                    if event.key == pygame.K_LEFT:
                        selected_avatar_idx = (selected_avatar_idx - 1) % len(AVATAR_OPTIONS)
                    elif event.key == pygame.K_RIGHT:
                        selected_avatar_idx = (selected_avatar_idx + 1) % len(AVATAR_OPTIONS)
                    elif event.key == pygame.K_SPACE:
                        player = Player(AVATAR_OPTIONS[selected_avatar_idx])
                        level_width = load_level(current_level, player, groups)
                        game_state = "PLAYING"
                
                elif game_state != "PLAYING" and event.key == pygame.K_SPACE:
                    player.lives, player.score, current_level = 3, 0, 0
                    level_width = load_level(current_level, player, groups)
                    game_state = "PLAYING"

        if game_state == "START_MENU":
            screen.fill(SKY_BLUE)
            draw_text(screen, "PIXELER", 120, BLACK, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150)
            draw_text(screen, "CHOOSE YOUR CHARACTER", 30, (50, 50, 50), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)
            
            # --- Avatar Preview ---
            avatar_data = AVATAR_OPTIONS[selected_avatar_idx]
            if os.path.exists(avatar_data["path"]):
                preview_img = pygame.image.load(avatar_data["path"]).convert_alpha()
                preview_img = pygame.transform.scale(preview_img, (100, 140))
                preview_rect = preview_img.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
                screen.blit(preview_img, preview_rect)
            else:
                # Preview fallback box
                p_surf = pygame.Surface((80, 110)); p_surf.fill(avatar_data["color"])
                screen.blit(p_surf, p_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60)))
            
            draw_text(screen, avatar_data["name"], 25, BLACK, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150)
            pulse = math.sin(pygame.time.get_ticks() * 0.005) * 10
            draw_text(screen, "Press SPACE to Begin", 35, (50, 50, 50), SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 250 + int(pulse))

        elif game_state == "PLAYING":
            player.update(groups[1]); groups[2].update(groups[1]); camera.update(player, level_width)

            if pygame.sprite.spritecollide(player, groups[4], False):
                current_level += 1
                if current_level < len(LEVELS): level_width = load_level(current_level, player, groups)
                else: game_state = "VICTORY"

            if pygame.sprite.spritecollide(player, groups[3], True): player.score += 10

            for enemy in pygame.sprite.spritecollide(player, groups[2], False):
                if player.vel_y > 0 and player.rect.bottom < enemy.rect.centery + 15:
                    enemy.kill(); player.vel_y = -14
                else:
                    player.lives -= 1
                    if player.lives > 0: player.reset_pos()
                    else: game_state = "GAME_OVER"

            if player.rect.top > SCREEN_HEIGHT:
                player.lives -= 1
                if player.lives > 0: player.reset_pos()
                else: game_state = "GAME_OVER"

            screen.fill(SKY_BLUE)
            for sprite in groups[0]: screen.blit(sprite.image, camera.apply(sprite))
            draw_text(screen, f"Lives: {player.lives} | Gold: {player.score} | Level: {current_level+1}", 30, BLACK, SCREEN_WIDTH//2, 40)

        elif game_state == "GAME_OVER":
            screen.fill(BLACK)
            draw_text(screen, "GAME OVER", 100, (255, 50, 50), SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            draw_text(screen, "Press SPACE to Restart", 32, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)

        elif game_state == "VICTORY":
            screen.fill((40, 120, 40))
            draw_text(screen, "PIXELER SUPREME", 100, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            draw_text(screen, "Press SPACE to Replay", 32, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()