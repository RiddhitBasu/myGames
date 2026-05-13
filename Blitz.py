import pygame
import random
import sys
import os

# --- Configuration & Constants ---
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (200, 0, 0)
BLUE  = (0, 100, 255)
GOLD  = (255, 215, 0) 
SKY_TOP = (135, 206, 235)
SKY_BOTTOM = (255, 255, 255)
HILL_COLOR = (34, 139, 34)

GRAVITY = 0.8
JUMP_STRENGTH = -16
BASE_OBSTACLE_SPEED = 6
SPAWN_RATE = 1500 

# --- NEW: High Score Persistence Functions ---
def load_high_score():
    """Reads the high score from a local text file."""
    if os.path.exists("highscore.txt"):
        with open("highscore.txt", "r") as f:
            try:
                return int(f.read())
            except ValueError:
                return 0
    return 0

def save_high_score(score):
    """Writes the new high score to a local text file."""
    with open("highscore.txt", "w") as f:
        f.write(str(score))

class Background:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.hills = [[i * (screen_w // 5), random.randint(screen_h // 2, screen_h - 100)] for i in range(10)]

    def update(self, speed):
        scroll_speed = speed * 0.4
        for hill in self.hills:
            hill[0] -= scroll_speed
            if hill[0] < -600:
                hill[0] = self.screen_w + random.randint(50, 200)
                hill[1] = random.randint(self.screen_h // 2, self.screen_h - 100)

    def draw(self, surface):
        for y in range(self.screen_h):
            progress = y / self.screen_h
            r = SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * progress
            g = SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * progress
            b = SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * progress
            pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (self.screen_w, y))
        for x, y in self.hills:
            pygame.draw.ellipse(surface, HILL_COLOR, (x, y, 600, 400))

class Player:
    def __init__(self, screen_h):
        self.rect = pygame.Rect(100, screen_h - 100, 60, 60)
        self.vel_y = 0
        self.is_jumping = False
        self.speed = 5.0 
        self.image = None
        self.sprite_loaded = False
        
        if os.path.exists('player.png'):
            try:
                loaded_image = pygame.image.load('player.png').convert_alpha()
                self.image = pygame.transform.scale(loaded_image, (60, 60))
                self.sprite_loaded = True
            except: pass

    def handle_input(self, screen_w):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < screen_w:
            self.rect.x += self.speed

    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_STRENGTH
            self.is_jumping = True

    def apply_gravity(self, screen_h):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        if self.rect.bottom >= screen_h - 20:
            self.rect.bottom = screen_h - 20
            self.is_jumping = False

    def draw(self, surface):
        if self.sprite_loaded:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, BLUE, self.rect)

class Obstacle:
    shared_image = None
    image_found = False

    def __init__(self, screen_w, screen_h):
        self.width = 50
        self.height = random.randint(60, 120)
        self.rect = pygame.Rect(screen_w, screen_h - 20 - self.height, self.width, self.height)
        
        if Obstacle.shared_image is None and os.path.exists('obstacle.png'):
            try:
                Obstacle.shared_image = pygame.image.load('obstacle.png').convert_alpha()
                Obstacle.image_found = True
            except: pass
        
        if Obstacle.image_found:
            self.image = pygame.transform.scale(Obstacle.shared_image, (self.width, self.height))

    def update(self, speed):
        self.rect.x -= speed

    def draw(self, surface):
        if Obstacle.image_found:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, RED, self.rect)

class Coin:
    shared_image = None
    image_found = False

    def __init__(self, screen_w, screen_h):
        self.size = 40
        y_pos = random.randint(screen_h - 250, screen_h - 70)
        self.rect = pygame.Rect(screen_w, y_pos, self.size, self.size)
        
        if Coin.shared_image is None and os.path.exists('coin.png'):
            try:
                Coin.shared_image = pygame.image.load('coin.png').convert_alpha()
                Coin.image_found = True
            except: pass
        
        if Coin.image_found:
            self.image = pygame.transform.scale(Coin.shared_image, (self.size, self.size))

    def update(self, speed):
        self.rect.x -= speed

    def draw(self, surface):
        if Coin.image_found:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.circle(surface, GOLD, self.rect.center, self.size // 2)

def main():
    pygame.init()
    monitor_info = pygame.display.Info()
    SW, SH = monitor_info.current_w, monitor_info.current_h
    screen = pygame.display.set_mode((SW, SH), pygame.FULLSCREEN)
    
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 40)

    # --- INITIALIZE SCORES ---
    high_score = load_high_score()
    
    bg = Background(SW, SH)
    player = Player(SH)
    obstacles = []
    coins = [] 
    distance_score = 0
    coin_score = 0 
    game_active = True
    current_obstacle_speed = BASE_OBSTACLE_SPEED

    # Timers
    obstacle_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(obstacle_timer, SPAWN_RATE)
    
    coin_timer = pygame.USEREVENT + 2 
    pygame.time.set_timer(coin_timer, 2000) 

    while True:
        # Calculate live total score using: $Total = Distance + (Coins \times 5)$
        current_total_score = distance_score + (coin_score * 5)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key in [pygame.K_SPACE, pygame.K_UP]:
                    if game_active:
                        player.jump()
                    else:
                        # Reset Game
                        game_active = True
                        obstacles.clear()
                        coins.clear()
                        distance_score = 0
                        coin_score = 0
                        player.speed = 5.0
                        current_obstacle_speed = BASE_OBSTACLE_SPEED
                        player.rect.x = 100
                        player.rect.bottom = SH - 20
                        # Reload high score just in case
                        high_score = load_high_score()
                
            if game_active:
                if event.type == obstacle_timer:
                    obstacles.append(Obstacle(SW, SH))
                if event.type == coin_timer:
                    coins.append(Coin(SW, SH))

        if game_active:
            if player.speed < 18: player.speed += 0.003
            current_obstacle_speed = BASE_OBSTACLE_SPEED + (distance_score * 0.1)
            
            bg.update(current_obstacle_speed)
            player.handle_input(SW)
            player.apply_gravity(SH)
            
            # Update Obstacles
            for obstacle in obstacles[:]:
                obstacle.update(current_obstacle_speed)
                if obstacle.rect.right < 0:
                    obstacles.remove(obstacle)
                    distance_score += 1
                if player.rect.colliderect(obstacle.rect):
                    # GAME OVER TRIGGER
                    game_active = False
                    # Check and Save High Score
                    if current_total_score > high_score:
                        high_score = current_total_score
                        save_high_score(high_score)

            # Update and Collect Coins
            for coin in coins[:]:
                coin.update(current_obstacle_speed)
                if coin.rect.right < 0:
                    coins.remove(coin)
                
                if player.rect.colliderect(coin.rect):
                    coins.remove(coin)
                    coin_score += 1 

            # Drawing Gameplay
            bg.draw(screen) 
            pygame.draw.line(screen, BLACK, (0, SH - 20), (SW, SH - 20), 4)
            
            for coin in coins: coin.draw(screen)
            player.draw(screen)
            for obstacle in obstacles: obstacle.draw(screen)

            # Display UI (Updated to show High Score)
            score_text = f"Distance: {distance_score}  |  Coins: {coin_score}  |  High score: {high_score}"
            score_surf = font.render(score_text, True, BLACK)
            screen.blit(score_surf, (30, 30))
        else:
            # Game Over Screen
            screen.fill(BLACK)
            msg = font.render(f"GAME OVER! | Your Score: {current_total_score} | High Score: {high_score}", True, WHITE)
            restart_msg = font.render("Press SPACE to Restart", True, GOLD)
            
            msg_rect = msg.get_rect(center=(SW // 2, SH // 2 - 20))
            restart_rect = restart_msg.get_rect(center=(SW // 2, SH // 2 + 40))
            
            screen.blit(msg, msg_rect)
            screen.blit(restart_msg, restart_rect)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()