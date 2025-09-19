import sys 
import random
from collections import deque

import pygame

# ----------------------------
# Basic settings and constants
# ----------------------------

TILE = 26
GRID_W, GRID_H = 26, 20  # board size in cells
SIDEPANEL = 220          # right-side UI panel width

WIDTH = GRID_W * TILE + SIDEPANEL
HEIGHT = GRID_H * TILE

FPS_BASE = 10            # base speed (frames per second)
MAX_FPS = 22

# Colors (RGB)
BG_DARK = (18, 24, 28)
BG_LIGHT = (30, 36, 42)
UI_ACCENT = (70, 190, 255)
UI_TEXT = (235, 240, 245)
UI_MUTED = (150, 160, 170)
RED = (230, 60, 60)
GREEN = (65, 200, 120)
GOLD = (255, 200, 60)

# ---------------------------------
# Small helpers for color & drawing
# ---------------------------------

def clamp(x, a, b):
    return max(a, min(b, x))

def lighten(c, amount):
    r, g, b = c
    return (clamp(r + amount, 0, 255),
            clamp(g + amount, 0, 255),
            clamp(b + amount, 0, 255))

def darken(c, amount):
    return lighten(c, -amount)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))

# ----------------
# UI primitives
# ----------------

class Button:
    def __init__(self, rect, text, font, callback, hotkey=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.hotkey = hotkey

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
        if self.hotkey and event.type == pygame.KEYUP and event.key == self.hotkey:
            self.callback()

    def draw(self, surf):
        mouse = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse)
        base = lerp_color(UI_ACCENT, (255,255,255), 0.15) if hovered else UI_ACCENT

        # shadow
        shadow = pygame.Rect(self.rect.x+3, self.rect.y+3, self.rect.w, self.rect.h)
        pygame.draw.rect(surf, darken(base, 80), shadow, border_radius=10)

        # body with bevel
        pygame.draw.rect(surf, base, self.rect, border_radius=10)
        border = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h)
        pygame.draw.rect(surf, lighten(base, 35), border, width=3, border_radius=10)
        inner = pygame.Rect(self.rect.x+2, self.rect.y+2, self.rect.w-4, self.rect.h-4)
        pygame.draw.rect(surf, darken(base, 40), inner, width=2, border_radius=8)

        # label
        txt = self.font.render(self.text, True, (16, 28, 34))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

class Slider:
    """Simple horizontal slider (0..1)."""
    def __init__(self, rect, value=0.5):
        self.rect = pygame.Rect(rect)
        self.value = float(value)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._update_value(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0] and self.rect.collidepoint(event.pos):
                self._update_value(event.pos)

    def _update_value(self, pos):
        x = clamp((pos[0] - self.rect.x) / max(1, self.rect.w), 0.0, 1.0)
        self.value = x

    def draw(self, surf):
        # track
        track = pygame.Rect(self.rect.x, self.rect.y + self.rect.h//2 - 3, self.rect.w, 6)
        pygame.draw.rect(surf, UI_MUTED, track, border_radius=3)
        # knob
        knob_x = int(self.rect.x + self.rect.w * self.value)
        knob = pygame.Rect(knob_x-8, self.rect.y+2, 16, self.rect.h-4)
        pygame.draw.rect(surf, UI_ACCENT, knob, border_radius=6)

# ---------------------------
# Fancy pseudo-3D primitives
# ---------------------------

def draw_beveled_tile(surf, px, py, color, size=TILE):
    """Draw a beveled square with subtle 3D effect and shadow."""
    # drop shadow
    shadow_rect = pygame.Rect(px+4, py+4, size, size)
    pygame.draw.rect(surf, (0,0,0,60), shadow_rect, border_radius=6)

    # base
    rect = pygame.Rect(px, py, size, size)
    base_color = color
    pygame.draw.rect(surf, base_color, rect, border_radius=6)

    # bevel highlights
    pygame.draw.line(surf, lighten(base_color, 45), (px+2, py+2), (px+size-3, py+2), 2)
    pygame.draw.line(surf, lighten(base_color, 45), (px+2, py+2), (px+2, py+size-3), 2)
    pygame.draw.line(surf, darken(base_color, 45), (px+2, py+size-3), (px+size-3, py+size-3), 2)
    pygame.draw.line(surf, darken(base_color, 45), (px+size-3, py+2), (px+size-3, py+size-3), 2)

    # inner glossy gradient (simple radial approximation)
    gloss = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(size//2, 0, -2):
        t = r / (size//2)
        col = (*lighten(base_color, int(80*(1-t))), int(25*(1-t)))
        pygame.draw.circle(gloss, col, (size//2, size//2), r)
    surf.blit(gloss, (px, py))

def draw_apple(surf, px, py, size=TILE):
    """Spherical-looking apple with shine."""
    radius = size//2
    center = (px + radius, py + radius)

    # shadow
    pygame.draw.circle(surf, (0,0,0,80), (center[0]+3, center[1]+3), radius)

    # body gradient
    circle = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        t = r / radius
        col = lerp_color((255,110,90), (180,20,20), 1-t)
        pygame.draw.circle(circle, col, (radius, radius), r)
    surf.blit(circle, (px, py))

    # highlight
    pygame.draw.circle(surf, (255, 255, 255, 90), (px + radius - 6, py + radius - 8), radius//3)

    # leaf
    pygame.draw.ellipse(surf, (40, 160, 80), (px + radius, py + 4, 10, 16))

def build_vignette(size):
    """Radial gradient background vignette to give depth."""
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    cx, cy = w//2, h//2
    maxr = int((w*w + h*h)**0.5 / 2)
    for r in range(maxr, 0, -14):
        t = r / maxr
        alpha = int(200 * (1 - t) ** 2)
        pygame.draw.circle(surf, (0,0,0,alpha), (cx, cy), r)
    return surf

# ---------------
# Game structures
# ---------------

def grid_to_px(x, y):
    return x * TILE, y * TILE

def rand_cell():
    return random.randint(0, GRID_W-1), random.randint(0, GRID_H-1)

class Game:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.font, self.small = fonts
        self.clock = pygame.time.Clock()
        self.reset(full=True)
        
        self.pause_auto_ms = random.randint(3000, 8000)  # от 3 до 8 секунд
        self.pause_started = None

        # UI elements (menu + pause + gameover)
        self.scene = 'menu'  # 'menu', 'play', 'paused', 'help', 'gameover'
        self._build_ui()

        # Background pre-render
        self.board_rect = pygame.Rect(0, 0, GRID_W*TILE, GRID_H*TILE)
        self.vignette = build_vignette(self.board_rect.size)

    # ------------- State & UI -------------

    def reset(self, full=False):
        cx, cy = GRID_W // 2, GRID_H // 2
        self.snake = deque([(cx-2, cy), (cx-1, cy), (cx, cy)])
        self.direction = (1, 0)
        self.next_dir = (1, 0)
        self.ticks = 0
        self.score = 0
        if full:
            self.best = 0
        self.speed = FPS_BASE
        self.speed_pending = FPS_BASE  # BUG: using pending value but not applying live
        self.apples = []
        for _ in range(2):
            self.spawn_apple()

        # Invisible vertical "wall" (BUG behaviour)
        self.invis_x = GRID_W // 3
        self.invis_y1 = 4
        self.invis_y2 = GRID_H - 5

        self.game_over = False

    def _build_ui(self):
        fw = self.font
        bx = GRID_W*TILE + 14
        by = 40

        self.btn_start = Button((bx, by, SIDEPANEL-28, 44), "▶ Start", fw, self.start_game, hotkey=pygame.K_RETURN)
        self.btn_help = Button((bx, by+56, SIDEPANEL-28, 44), "❓ How to Play", fw, self.show_help)
        self.btn_quit = Button((bx, by+112, SIDEPANEL-28, 44), "✖ Quit", fw, self.quit)

        self.btn_resume = Button((bx, by, SIDEPANEL-28, 44), "⏯ Resume (P)", fw, self.resume, hotkey=pygame.K_p)
        self.btn_restart = Button((bx, by+56, SIDEPANEL-28, 44), "↻ Restart (R/Enter)", fw, self.restart, hotkey=pygame.K_r)
        self.btn_menu = Button((bx, by+112, SIDEPANEL-28, 44), "← Main Menu", fw, self.goto_menu)

        # Speed slider (0..1 -> FPS)
        self.slider = Slider((bx, by+190, SIDEPANEL-28, 28), value=(FPS_BASE-6)/(MAX_FPS-6))

    # ------------- Scene controls -------------

    def start_game(self):
        self.scene = 'play'

    def show_help(self):
        self.scene = 'help'

    def goto_menu(self):
        self.scene = 'menu'

    def resume(self):
        self.scene = 'play'
        self.pause_started = None
        self.pause_auto_ms = random.randint(3000, 8000)

    def restart(self):
        self.reset(full=False)
        # Apply slider to speed only on restart (buggy latency by design)
        preview = int(max(6, min(MAX_FPS, int(lerp(6, MAX_FPS, self.slider.value)))))
        self.speed = preview
        self.scene = 'play'
        self.pause_started = None
        self.pause_auto_ms = random.randint(3000, 8000)

    def quit(self):
        pygame.quit()
        sys.exit()

    # ------------- Game logic -------------

    def spawn_apple(self):
        """Spawn an apple. BUG: sometimes allow on-snake spawn."""
        bypass = random.random() < 0.22  # BUG probability
        for _ in range(200):
            x, y = rand_cell()
            if bypass or (x, y) not in self.snake and (x, y) not in self.apples:
                self.apples.append((x, y))
                return

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE,):
                    self.goto_menu()
                if e.key in (pygame.K_p,):
                    if self.scene == 'play':
                        self.scene = 'paused'
                    elif self.scene == 'paused':
                        self.scene = 'play'
                if self.scene in ('play', 'paused', 'gameover'):
                    if e.key in (pygame.K_r, pygame.K_RETURN):
                        self.restart()

                # Direction control
                if self.scene == 'play':
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        self.next_dir = (-1, 0)
                    elif e.key in (pygame.K_RIGHT, pygame.K_d):
                        self.next_dir = (1, 0)
                    elif e.key in (pygame.K_UP, pygame.K_w):
                        self.next_dir = (0, -1)
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.next_dir = (0, 1)

            # UI
            if self.scene == 'menu':
                self.btn_start.handle(e); self.btn_help.handle(e); self.btn_quit.handle(e)
            elif self.scene == 'paused':
                self.btn_resume.handle(e); self.btn_restart.handle(e); self.btn_menu.handle(e)
                self.slider.handle(e)  # BUG: value won't apply until restart
            elif self.scene == 'gameover':
                self.btn_restart.handle(e); self.btn_menu.handle(e); self.btn_quit.handle(e)

    def step(self):
        """Advance the game by one tick."""
        self.ticks += 1

        # Apply next_dir but avoid immediate 180° reversal... except sometimes (BUG)
        ndx, ndy = self.next_dir
        dx, dy = self.direction
        if (ndx, ndy) != (-dx, -dy) or (self.ticks % 12 == 0):  # BUG: on every 12th tick, reversal allowed
            self.direction = (ndx, ndy)

        # "Invisible wall": If next cell is at a specific x-range, block move but do not die (BUG)
        hx, hy = self.snake[-1]
        nx, ny = hx + self.direction[0], hy + self.direction[1]

        # border collision
        if not (0 <= nx < GRID_W and 0 <= ny < GRID_H):
            self.game_over = True
            self.scene = 'gameover'
            self.best = max(self.best, self.score)
            return

        # invisible barrier check (blocks but no death)
        if nx == self.invis_x and self.invis_y1 <= ny <= self.invis_y2:
            # simply skip movement this frame and return (BUG behaviour)
            return

        # normal move
        self.snake.append((nx, ny))

        # apple check (with phantom bug)
        ate = False
        for i, (ax, ay) in enumerate(list(self.apples)):
            if nx == ax and ny == ay:
                # Phantom apple condition (BUG): when approaching from LEFT on even row
                if self.direction == (-1, 0) and (ay % 2 == 0):
                    # Do NOT increase score, do NOT grow, do NOT remove apple;
                    # BUT spawn a new one -> duplicate apples appear (BUG)
                    self.spawn_apple()
                    ate = False
                else:
                    ate = True
                    self.score += 1
                    del self.apples[i]
                    self.spawn_apple()
                break

        if not ate:
            self.snake.popleft()  # move forward without growing

        # self-collision
        body = list(self.snake)[:-1]
        if self.snake[-1] in body:
            self.game_over = True
            self.scene = 'gameover'
            self.best = max(self.best, self.score)

    # ------------- Rendering -------------

    def draw_board(self):
        # background
        self.screen.fill(BG_DARK)
        pygame.draw.rect(self.screen, BG_LIGHT, self.board_rect)
        # grid
        for x in range(GRID_W):
            for y in range(GRID_H):
                if (x + y) % 2 == 0:
                    rx, ry = grid_to_px(x, y)
                    r = pygame.Rect(rx, ry, TILE, TILE)
                    pygame.draw.rect(self.screen, darken(BG_LIGHT, 6), r)
        # vignette
        self.screen.blit(self.vignette, (0, 0))

        # apples
        for ax, ay in self.apples:
            px, py = grid_to_px(ax, ay)
            draw_apple(self.screen, px, py, TILE)

        # snake
        for (x, y) in list(self.snake)[:-1]:
            px, py = grid_to_px(x, y)
            draw_beveled_tile(self.screen, px, py, GREEN, TILE)

        # head with gold tint
        hx, hy = self.snake[-1]
        px, py = grid_to_px(hx, hy)
        draw_beveled_tile(self.screen, px, py, lerp_color(GREEN, GOLD, 0.25), TILE)

        # DEBUG OPTION (commented): show invisible wall
        # for y in range(self.invis_y1, self.invis_y2+1):
        #     rx, ry = grid_to_px(self.invis_x, y)
        #     pygame.draw.rect(self.screen, (255,0,0), (rx, ry, TILE, TILE), 1)

    def draw_sidepanel(self):
        panel = pygame.Rect(GRID_W*TILE, 0, SIDEPANEL, HEIGHT)
        pygame.draw.rect(self.screen, (24,28,34), panel)

        # Title
        title = self.font.render("Snake 3D-ish", True, UI_TEXT)
        self.screen.blit(title, (GRID_W*TILE + 14, 6))

        # Score box
        score_label = self.small.render("Score", True, UI_MUTED)
        best_label = self.small.render("Best", True, UI_MUTED)
        self.screen.blit(score_label, (GRID_W*TILE + 14, 36))
        self.screen.blit(best_label, (GRID_W*TILE + 14, 66))

        score_val = self.font.render(str(self.score), True, UI_TEXT)
        best_val = self.font.render(str(self.best), True, UI_TEXT)
        self.screen.blit(score_val, (GRID_W*TILE + 100, 30))
        self.screen.blit(best_val, (GRID_W*TILE + 100, 60))

        # Scene-specific widgets
        if self.scene == 'menu':
            self.btn_start.draw(self.screen)
            self.btn_help.draw(self.screen)
            self.btn_quit.draw(self.screen)

        elif self.scene == 'paused':
            self.btn_resume.draw(self.screen)
            self.btn_restart.draw(self.screen)
            self.btn_menu.draw(self.screen)

            label = self.small.render("Game Speed", True, UI_MUTED)
            self.screen.blit(label, (GRID_W*TILE + 14, 160))
            self.slider.draw(self.screen)

            # BUG: show the speed preview but do not apply live
            preview = int(lerp(6, MAX_FPS, self.slider.value))
            pv_txt = self.small.render(f"Preview: {preview} FPS", True, UI_TEXT)
            self.screen.blit(pv_txt, (GRID_W*TILE + 14, 224))

        elif self.scene == 'help':
            y = 40
            lines = [
                "Controls:",
                "  Arrow keys / WASD — move",
                "  P — pause/resume, R — restart",
                "  Esc — main menu",
                "",
                "Goal: eat apples to grow and score.",
                "The look is 'pseudo 3D' with beveled tiles.",
                "",
                "Note: this build intentionally contains defects",
                "for black-box testing practice."
            ]
            for ln in lines:
                txt = self.small.render(ln, True, UI_TEXT)
                self.screen.blit(txt, (GRID_W*TILE + 14, y))
                y += 24

        elif self.scene == 'gameover':
            over = self.font.render("Game Over", True, RED)
            self.screen.blit(over, (GRID_W*TILE + 14, 40))
            self.btn_restart.draw(self.screen)
            self.btn_menu.draw(self.screen)
            self.btn_quit.draw(self.screen)

    def draw(self):
        self.draw_board()
        self.draw_sidepanel()
        pygame.display.flip()

    # ------------- Main loop -------------

    def run(self):
        running = True
        while running:
            # Events
            self.handle_events()

            if self.scene == 'play':
                # game tick
                self.step()

            # Apply FPS based on current speed (which doesn't change live)
            self.clock.tick(self.speed)

            # draw
            self.draw()

# ----------------------
# App bootstrap / main
# ----------------------

def main():
    pygame.init()
    pygame.display.set_caption("Snake 3D-ish — bugged build for testing")
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.SCALED)

    # Fonts
    try:
        font = pygame.font.SysFont("Segoe UI", 26)
        small = pygame.font.SysFont("Segoe UI", 20)
    except:
        font = pygame.font.Font(None, 26)
        small = pygame.font.Font(None, 20)

    game = Game(screen, (font, small))

    # Read slider to speed only once on startup (matches 'restart only' behaviour)
    preview = int(lerp(6, MAX_FPS, game.slider.value))
    game.speed = clamp(preview, 6, MAX_FPS)

    while True:
        if game.scene == 'menu':
            # Allow updating speed preview on menu too (no buttons here though)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                game.btn_start.handle(e); game.btn_help.handle(e); game.btn_quit.handle(e)
            game.draw_board()
            game.draw_sidepanel()
            pygame.display.flip()
            game.clock.tick(60)
        else:
            game.run()

if __name__ == "__main__":
    main()
