import pygame
import random
import sys
import math

# SECTION 1: INITIALIZATION & SETUP

pygame.init()

# Screen dimensions and layout
WIDTH = 800
HEIGHT = 600

BOTTOM_PANEL = 115
PLAY_HEIGHT = HEIGHT - BOTTOM_PANEL

CELL_SIZE = 20
DOT_STEP = 6

# Grid dimensions
COLS = WIDTH // CELL_SIZE
ROWS = PLAY_HEIGHT // CELL_SIZE

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jump Game")

clock = pygame.time.Clock()

# Colors
BLACK = (8, 10, 15)
WHITE = (230, 230, 240)
RED = (220, 50, 45)
YELLOW = (235, 210, 55)
BLUE = (50, 130, 230)
GREEN = (65, 205, 75)
GRID_DOT = (75, 85, 100)
GREEN_TEXT = (90, 220, 75)
DARK = (28, 32, 42)

# Fonts
font_big = pygame.font.SysFont("consolas", 25, bold=True)
font_mid = pygame.font.SysFont("consolas", 19, bold=True)
font_small = pygame.font.SysFont("consolas", 14, bold=True)
arrow_font = pygame.font.SysFont("Segoe UI Symbol", 34, bold=True)

# SECTION 2: PLAYER CLASS
class Player:
    def __init__(self, title, tint, start_x, start_y):
        self.across = start_x
        self.down = start_y
        self.dx = 0
        self.dy = 0
        self.olddx = 0
        self.olddy = 0
        self.score = 0
        self.flag = WHITE
        self.tint = tint
        self.title = title
        self.last_across = start_x
        self.last_down = start_y
        self.has_blue = False
        self.has_green = False
        self.history = [[start_x, start_y]]
        self.crashed = False
    
    @property
    def pos(self):
        return [self.across, self.down]
    
    @pos.setter
    def pos(self, value):
        self.across, self.down = value
    
    @property
    def last_pos(self):
        return [self.last_across, self.last_down]
    
    @last_pos.setter
    def last_pos(self, value):
        self.last_across, self.last_down = value
    
    def add_history(self):
        if [self.across, self.down] not in self.history[-3:]:
            self.history.append([self.across, self.down])
    
    def trigger_crash(self):
        self.crashed = True

# Create players
players = [Player("Player 1", RED, 3, ROWS // 2), Player("Player 2", YELLOW, 3, ROWS // 2 + 2)]

# SECTION 3: GAME STATE VARIABLES
game_state = "intro"
is_random_track = False
current_player = 0
winner = None
blue_box = None
green_box = None
track_cells = []
obstacle_cells = []
pending_dx = 0
pending_dy = 0
turn_count = 0
running = True

# SECTION 4: PLAYABLE RACE TRACK

def create_playable_race_track():
    """Create a proper, playable race track with clear path"""
    global track_cells, blue_box, green_box
    
    track_cells = []
    
    # Top straight
    for x in range(6, 37):
        for y in range(5, 8):
            track_cells.append([x, y])
    
    # Bottom straight
    for x in range(6, 37):
        for y in range(18, 21):
            track_cells.append([x, y])
    
    # Left curve
    for y in range(5, 21):
        for x in range(4, 7):
            track_cells.append([x, y])
    
    # Right curve
    for y in range(5, 21):
        for x in range(35, 38):
            track_cells.append([x, y])
    
    # Inner track - middle section
    for x in range(10, 33):
        for y in range(10, 16):
            track_cells.append([x, y])
    
    # Connecting paths
    for x in range(7, 11):
        for y in range(8, 11):
            track_cells.append([x, y])
    
    for x in range(7, 11):
        for y in range(15, 18):
            track_cells.append([x, y])
    
    for x in range(32, 36):
        for y in range(8, 11):
            track_cells.append([x, y])
    
    for x in range(32, 36):
        for y in range(15, 18):
            track_cells.append([x, y])
    
    # Chicane section
    for x in range(18, 25):
        track_cells.append([x, 9])
        track_cells.append([x, 10])
    
    for x in range(18, 25):
        track_cells.append([x, 16])
        track_cells.append([x, 17])
    
    # Start area
    for y in range(9, 17):
        for x in range(2, 6):
            track_cells.append([x, y])
    
    # Make sure player start positions are on track
    for player in players:
        if player.pos not in track_cells:
            track_cells.append(player.pos)
    
    # ONE blue and ONE green collectible
    blue_box = [12, 12]
    green_box = [30, 12]
    
    # Remove duplicates
    track_cells = list({(cell[0], cell[1]) for cell in track_cells})
    track_cells = [[cell[0], cell[1]] for cell in track_cells]
    
    print(f"Race track created with {len(track_cells)} safe cells")

def create_random_track():
    """Generate random obstacle course with ONE blue and ONE green"""
    global track_cells, obstacle_cells, blue_box, green_box
    
    track_cells = []
    obstacle_cells = []
    
    # ONE blue box
    blue_box = [random.randint(8, COLS - 8), random.randint(3, ROWS - 3)]
    while blue_box in [players[0].pos, players[1].pos]:
        blue_box = [random.randint(8, COLS - 8), random.randint(3, ROWS - 3)]
    
    # ONE green box
    green_box = [random.randint(8, COLS - 8), random.randint(3, ROWS - 3)]
    distance = abs(blue_box[0] - green_box[0]) + abs(blue_box[1] - green_box[1])
    while (green_box == blue_box or green_box in [players[0].pos, players[1].pos] or distance < 8):
        green_box = [random.randint(8, COLS - 8), random.randint(3, ROWS - 3)]
        distance = abs(blue_box[0] - green_box[0]) + abs(blue_box[1] - green_box[1])
    
    # Many red obstacles
    num_obstacles = random.randint(60, 80)
    for _ in range(num_obstacles):
        obs = [random.randint(1, COLS - 2), random.randint(1, ROWS - 2)]
        if (obs != players[0].pos and obs != players[1].pos and 
            obs != blue_box and obs != green_box and 
            obs not in obstacle_cells):
            obstacle_cells.append(obs)
    
    print(f"Random track created with {len(obstacle_cells)} obstacles")

def setup_track():
    """Setup track based on selection"""
    global track_cells, obstacle_cells, blue_box, green_box, is_random_track
    
    if is_random_track:
        create_random_track()
    else:
        create_playable_race_track()
        obstacle_cells = []

def reset_for_menu():
    """Clean reset when returning to menu"""
    global pending_dx, pending_dy, turn_count, current_player, winner, game_state
    pending_dx = 0
    pending_dy = 0
    turn_count = 0
    current_player = 0
    winner = None

def reset_game():
    """Full game reset - clears crash effects"""
    global current_player, winner, pending_dx, pending_dy, turn_count, game_state, blue_box, green_box
    
    players[0].across = 3
    players[0].down = ROWS // 2
    players[0].dx = 0
    players[0].dy = 0
    players[0].score = 0
    players[0].has_blue = False
    players[0].has_green = False
    players[0].last_across = 3
    players[0].last_down = ROWS // 2
    players[0].history = [[3, ROWS // 2]]
    players[0].crashed = False
    
    players[1].across = 3
    players[1].down = ROWS // 2 + 2
    players[1].dx = 0
    players[1].dy = 0
    players[1].score = 0
    players[1].has_blue = False
    players[1].has_green = False
    players[1].last_across = 3
    players[1].last_down = ROWS // 2 + 2
    players[1].history = [[3, ROWS // 2 + 2]]
    players[1].crashed = False
    
    current_player = 0
    winner = None
    pending_dx = 0
    pending_dy = 0
    turn_count = 0
    
    setup_track()

def find_nearest_track_cell(pos):
    """Find nearest valid track cell"""
    if not track_cells:
        return pos
    
    best_dist = float('inf')
    best_cell = pos
    
    for cell in track_cells:
        dist = abs(cell[0] - pos[0]) + abs(cell[1] - pos[1])
        if dist < best_dist:
            best_dist = dist
            best_cell = cell
    
    return best_cell

def switch_track(new_is_random):
    """Switch tracks during gameplay"""
    global is_random_track, track_cells, obstacle_cells, blue_box, green_box, players
    
    p1_pos = players[0].pos[:]
    p2_pos = players[1].pos[:]
    p1_score = players[0].score
    p2_score = players[1].score
    p1_has_blue = players[0].has_blue
    p2_has_blue = players[1].has_blue
    p1_has_green = players[0].has_green
    p2_has_green = players[1].has_green
    p1_dx = players[0].dx
    p1_dy = players[0].dy
    p2_dx = players[1].dx
    p2_dy = players[1].dy
    p1_history = players[0].history[:]
    p2_history = players[1].history[:]
    p1_crashed = players[0].crashed
    p2_crashed = players[1].crashed
    
    is_random_track = new_is_random
    setup_track()
    
    players[0].pos = p1_pos
    players[1].pos = p2_pos
    players[0].score = p1_score
    players[1].score = p2_score
    players[0].has_blue = p1_has_blue
    players[1].has_blue = p2_has_blue
    players[0].has_green = p1_has_green
    players[1].has_green = p2_has_green
    players[0].dx = p1_dx
    players[0].dy = p1_dy
    players[1].dx = p2_dx
    players[1].dy = p2_dy
    players[0].history = p1_history
    players[1].history = p2_history
    players[0].crashed = p1_crashed
    players[1].crashed = p2_crashed
    
    if not is_random_track and track_cells:
        for player in players:
            if player.pos not in track_cells:
                new_pos = find_nearest_track_cell(player.pos)
                player.pos = new_pos
                player.add_history()

def draw_explosion(surface, x, y):
    """Draw static explosion effect"""
    for i in range(4):
        offset = i * 3
        color = (255, 150 - i * 30, 0)
        pygame.draw.circle(surface, color, (x, y), 15 + offset, 2)
    
    pygame.draw.circle(surface, (255, 200, 0), (x, y), 8)
    pygame.draw.circle(surface, (255, 100, 0), (x, y), 5)
    pygame.draw.circle(surface, (255, 255, 255), (x, y), 3)
    
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        sparkle_x = x + int(18 * math.cos(rad))
        sparkle_y = y + int(18 * math.sin(rad))
        pygame.draw.circle(surface, (255, 150, 0), (sparkle_x, sparkle_y), 2)
        
        sparkle_x2 = x + int(25 * math.cos(rad + 15))
        sparkle_y2 = y + int(25 * math.sin(rad + 15))
        pygame.draw.circle(surface, (255, 80, 0), (sparkle_x2, sparkle_y2), 1)

# SECTION 5: MAIN GAME LOOP
while running:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            
            if game_state == "intro":
                if event.key == pygame.K_n:
                    is_random_track = True
                elif event.key == pygame.K_m:
                    is_random_track = False
                elif event.key == pygame.K_RETURN:
                    reset_game()
                    game_state = "playing"
            
            elif game_state == "playing":
                active = players[current_player]
                
                if event.key == pygame.K_n:
                    switch_track(True)
                elif event.key == pygame.K_m:
                    switch_track(False)
                elif event.key == pygame.K_LEFT:
                    pending_dx = -1 if pending_dx != -1 else 0
                elif event.key == pygame.K_RIGHT:
                    pending_dx = 1 if pending_dx != 1 else 0
                elif event.key == pygame.K_UP:
                    pending_dy = -1 if pending_dy != -1 else 0
                elif event.key == pygame.K_DOWN:
                    pending_dy = 1 if pending_dy != 1 else 0
                elif event.key == pygame.K_RETURN:
                    active.dx += pending_dx
                    active.dy += pending_dy
                    
                    active.last_across = active.across
                    active.last_down = active.down
                    new_pos = [active.across + active.dx, active.down + active.dy]
                    
                    collision = False
                    if new_pos[0] < 0 or new_pos[0] >= COLS:
                        collision = True
                    if new_pos[1] < 0 or new_pos[1] >= ROWS:
                        collision = True
                    
                    if is_random_track:
                        if new_pos in obstacle_cells:
                            collision = True
                    else:
                        if new_pos not in track_cells:
                            collision = True
                    
                    if new_pos == players[1 - current_player].pos:
                        collision = True
                    
                    if collision:
                        active.score -= 10
                        players[1 - current_player].score += turn_count
                        winner = 2 - current_player
                        active.trigger_crash()
                        game_state = "game_over"
                    else:
                        active.across, active.down = new_pos
                        active.add_history()
                        
                        if [active.across, active.down] == blue_box and not active.has_blue:
                            active.has_blue = True
                            active.score += 5
                        
                        if [active.across, active.down] == green_box and active.has_blue and not active.has_green:
                            active.has_green = True
                            active.score += 10
                            active.score += turn_count
                            winner = current_player + 1
                            game_state = "game_over"
                        else:
                            current_player = 1 - current_player
                    
                    pending_dx = 0
                    pending_dy = 0
                    turn_count += 1
            
            elif game_state == "game_over":
                if event.key == pygame.K_r:
                    game_state = "intro"
                elif event.key == pygame.K_ESCAPE:
                    running = False
            
            if event.key == pygame.K_i and game_state != "intro":
                reset_for_menu()
                game_state = "intro"
    
    # RENDERING
    screen.fill(BLACK)
    
    if game_state == "intro":
        title = font_big.render("Welcome to Jump", True, GREEN_TEXT)
        screen.blit(title, (35, 25))
        
        preview_box = pygame.Rect(30, 70, WIDTH - 60, 90)
        pygame.draw.rect(screen, WHITE, preview_box, 2)
        
        # Preview dots
        for x in range(40, WIDTH - 40, 6):
            for y in range(80, 150, 6):
                pygame.draw.circle(screen, GRID_DOT, (x, y), 1)
        
        preview_blue = pygame.Rect(360, 100, 20, 20)
        preview_green = pygame.Rect(WIDTH - 95, 100, 20, 20)
        pygame.draw.rect(screen, BLUE, preview_blue)
        pygame.draw.rect(screen, GREEN, preview_green)
        
        track_name = "RANDOM" if is_random_track else "RACE TRACK"
        lines = [
            "The object of this game is to navigate from your starting position",
            "to the blue and green squares before your opponent does.",
            "",
            "First collect BLUE. Then collect GREEN.",
            "",
            "Each player has saved velocity.",
            "Press arrow keys to adjust velocity",
            "Press ENTER to move and switch player.",
            "",
            "Press N for random track",
            "Press M for race track",
            "Press I to return to menu at any time",
            "",
            f"Current Track: {track_name}",
            "",
            "Press ENTER to start"
        ]
        
        y = 180
        for line in lines:
            text = font_mid.render(line, True, GREEN_TEXT)
            screen.blit(text, (35, y))
            y += 20
    
    else:
        # Draw white border
        pygame.draw.rect(screen, WHITE, (8, 8, WIDTH - 16, PLAY_HEIGHT - 16), 2)
        
        # STEP 1: Draw background grid dots EVERYWHERE
        for x in range(0, WIDTH, 6):
            for y in range(0, PLAY_HEIGHT, 6):
                pygame.draw.circle(screen, GRID_DOT, (x, y), 1)
        
        if is_random_track:
            # Random track: draw RED obstacles OVER the grid
            for cell in obstacle_cells:
                pygame.draw.rect(screen, RED, (
                    cell[0] * CELL_SIZE, cell[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        else:
            # Race track: cover UNSAFE cells with BLACK (but keep grid in safe cells)
            for x in range(COLS):
                for y in range(ROWS):
                    if [x, y] not in track_cells:
                        pygame.draw.rect(screen, BLACK, (
                            x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # Draw collectibles - these will cover the grid dots in their cells
        if blue_box:
            pygame.draw.rect(screen, BLUE, (
                blue_box[0] * CELL_SIZE, blue_box[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, WHITE, (
                blue_box[0] * CELL_SIZE, blue_box[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
        
        if green_box:
            pygame.draw.rect(screen, GREEN, (
                green_box[0] * CELL_SIZE, green_box[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, WHITE, (
                green_box[0] * CELL_SIZE, green_box[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
        
        # Draw movement history
        for i, player in enumerate(players):
            color = (200, 45, 40) if i == 0 else (200, 170, 35)
            for hist_pos in player.history[:-1]:
                pygame.draw.circle(screen, color, (
                    hist_pos[0] * CELL_SIZE + CELL_SIZE // 2,
                    hist_pos[1] * CELL_SIZE + CELL_SIZE // 2), 4)
        
        # Draw player positions
        for i, player in enumerate(players):
            color = RED if i == 0 else YELLOW
            x = player.across * CELL_SIZE + CELL_SIZE // 2
            y = player.down * CELL_SIZE + CELL_SIZE // 2
            
            if player.crashed:
                draw_explosion(screen, x, y)
            
            pygame.draw.circle(screen, color, (x, y), 7)
            pygame.draw.circle(screen, WHITE, (x, y), 2)
        
        # BOTTOM PANEL
        panel_y = PLAY_HEIGHT
        pygame.draw.rect(screen, BLACK, (0, panel_y, WIDTH, BOTTOM_PANEL))
        pygame.draw.line(screen, WHITE, (0, panel_y), (WIDTH, panel_y), 2)
        
        left_box = pygame.Rect(10, panel_y + 8, 375, BOTTOM_PANEL - 16)
        right_box = pygame.Rect(410, panel_y + 8, 380, BOTTOM_PANEL - 16)
        
        if current_player == 0:
            pygame.draw.rect(screen, RED, left_box, 2)
            pygame.draw.rect(screen, DARK, right_box, 2)
        else:
            pygame.draw.rect(screen, DARK, left_box, 2)
            pygame.draw.rect(screen, YELLOW, right_box, 2)
        
        screen.blit(font_mid.render("Player 1", True, WHITE), (25, panel_y + 15))
        screen.blit(font_mid.render("Player 2", True, WHITE), (420, panel_y + 15))
        
        # VELOCITY HUD
        for i, player in enumerate(players):
            preview_vx = player.dx + (pending_dx if current_player == i else 0)
            preview_vy = player.dy + (pending_dy if current_player == i else 0)
            
            left_val = abs(preview_vx) if preview_vx < 0 else 0
            right_val = abs(preview_vx) if preview_vx > 0 else 0
            up_val = abs(preview_vy) if preview_vy < 0 else 0
            down_val = abs(preview_vy) if preview_vy > 0 else 0
            
            if i == 0:
                base_color = RED
                highlight = GREEN_TEXT
                
                left_color = highlight if (current_player == i and pending_dx == -1) else base_color
                right_color = highlight if (current_player == i and pending_dx == 1) else base_color
                up_color = highlight if (current_player == i and pending_dy == -1) else base_color
                down_color = highlight if (current_player == i and pending_dy == 1) else base_color
                
                screen.blit(arrow_font.render("←", True, left_color), (140, panel_y + 25))
                screen.blit(arrow_font.render("→", True, right_color), (185, panel_y + 25))
                screen.blit(arrow_font.render("↑", True, up_color), (230, panel_y + 25))
                screen.blit(arrow_font.render("↓", True, down_color), (275, panel_y + 25))
                
                screen.blit(font_small.render(str(left_val), True, left_color), (148, panel_y + 73))
                screen.blit(font_small.render(str(right_val), True, right_color), (193, panel_y + 73))
                screen.blit(font_small.render(str(up_val), True, up_color), (238, panel_y + 73))
                screen.blit(font_small.render(str(down_val), True, down_color), (283, panel_y + 73))
            else:
                base_color = YELLOW
                highlight = GREEN_TEXT
                
                left_color = highlight if (current_player == i and pending_dx == -1) else base_color
                right_color = highlight if (current_player == i and pending_dx == 1) else base_color
                up_color = highlight if (current_player == i and pending_dy == -1) else base_color
                down_color = highlight if (current_player == i and pending_dy == 1) else base_color
                
                screen.blit(arrow_font.render("←", True, left_color), (535, panel_y + 25))
                screen.blit(arrow_font.render("→", True, right_color), (580, panel_y + 25))
                screen.blit(arrow_font.render("↑", True, up_color), (625, panel_y + 25))
                screen.blit(arrow_font.render("↓", True, down_color), (670, panel_y + 25))
                
                screen.blit(font_small.render(str(left_val), True, left_color), (543, panel_y + 73))
                screen.blit(font_small.render(str(right_val), True, right_color), (588, panel_y + 73))
                screen.blit(font_small.render(str(up_val), True, up_color), (633, panel_y + 73))
                screen.blit(font_small.render(str(down_val), True, down_color), (678, panel_y + 73))
        
        # Scores
        screen.blit(font_mid.render(f"Score: {players[0].score}", True, WHITE), (310, panel_y + 35))
        screen.blit(font_mid.render(f"Score: {players[1].score}", True, WHITE), (700, panel_y + 35))
        
        # Collected indicators
        if players[0].has_blue:
            pygame.draw.rect(screen, BLUE, (70, panel_y + 62, 18, 18))
            pygame.draw.rect(screen, WHITE, (70, panel_y + 62, 18, 18), 1)
        if players[0].has_green:
            pygame.draw.rect(screen, GREEN, (95, panel_y + 62, 18, 18))
            pygame.draw.rect(screen, WHITE, (95, panel_y + 62, 18, 18), 1)
        if players[1].has_blue:
            pygame.draw.rect(screen, BLUE, (465, panel_y + 62, 18, 18))
            pygame.draw.rect(screen, WHITE, (465, panel_y + 62, 18, 18), 1)
        if players[1].has_green:
            pygame.draw.rect(screen, GREEN, (490, panel_y + 62, 18, 18))
            pygame.draw.rect(screen, WHITE, (490, panel_y + 62, 18, 18), 1)
        
        # Track info
        if is_random_track:
            track_info = font_small.render("RANDOM", True, RED)
            screen.blit(track_info, (WIDTH - 70, panel_y + 85))
        else:
            track_info = font_small.render("RACE", True, BLUE)
            screen.blit(track_info, (WIDTH - 70, panel_y + 85))
        
        # GAME OVER OVERLAY
        if game_state == "game_over":
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            box = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 60, 440, 120)
            pygame.draw.rect(screen, DARK, box)
            pygame.draw.rect(screen, WHITE, box, 3)
            screen.blit(font_big.render(f"Player {winner} wins!", True, GREEN_TEXT), (box.x + 110, box.y + 25))
            screen.blit(font_small.render("Press R to restart or ESC to quit", True, WHITE), (box.x + 80, box.y + 75))
    
    pygame.display.flip()

pygame.quit()
sys.exit()