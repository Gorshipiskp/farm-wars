"""
Pygame overlay for the minesweeper mini-game (uses minesweeper.game).
"""

from __future__ import annotations

import time

import pygame

from minesweeper.game import ClickResult, Minesweeper

# Colors
BG = (252, 248, 238)
PANEL_BORDER = (110, 88, 62)
CELL_HIDDEN = (154, 162, 172)
CELL_REVEALED = (232, 228, 216)
CELL_FLAG = (200, 80, 80)
CELL_MINE = (40, 40, 40)
CELL_BOOM = (195, 55, 55)
TEXT = (42, 36, 30)
NUMBER_COLORS = {
    1: (21, 101, 192),
    2: (46, 125, 50),
    3: (198, 40, 40),
    4: (40, 53, 147),
    5: (74, 20, 140),
    6: (0, 105, 92),
    7: (62, 39, 35),
    8: (97, 97, 97),
}


def run_minesweeper_modal(screen, fonts, *, title: str = "Сапёр") -> str:
    """
    Blocking minesweeper mini-game loop.

    Returns:
        ``"win"`` — player cleared the field,
        ``"cancel"`` — Esc / closed without winning.
    """
    w, h, mines = Minesweeper.preset("easy")
    game = Minesweeper(w, h, mines)

    sw, sh = screen.get_size()
    panel_w = min(sw - 80, max(360, w * 36 + 48))
    panel_h = min(sh - 80, h * 36 + 120)
    panel = pygame.Rect((sw - panel_w) // 2, (sh - panel_h) // 2, panel_w, panel_h)

    grid_size = min((panel_w - 40) // w, (panel_h - 90) // h)
    grid_size = max(24, grid_size)
    grid_w = w * grid_size
    grid_h = h * grid_size
    grid_x = panel.x + (panel_w - grid_w) // 2
    grid_y = panel.y + 56

    show_loss_until = 0.0
    pending_lost_return = False
    clock = pygame.time.Clock()

    while True:
        now = time.time()
        if show_loss_until and now >= show_loss_until:
            show_loss_until = 0.0
            if pending_lost_return:
                return "lost"
            game.reset()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "cancel"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "cancel"
                if event.key == pygame.K_r:
                    game.reset()
                    show_loss_until = 0.0
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if not panel.collidepoint(mx, my):
                    continue
                gx = (mx - grid_x) // grid_size
                gy = (my - grid_y) // grid_size
                if gx < 0 or gy < 0 or gx >= w or gy >= h:
                    continue
                if show_loss_until:
                    continue
                if event.button == 1:
                    result = game.click(gx, gy)
                    if result == ClickResult.WIN:
                        return "win"
                    if result == ClickResult.LOST:
                        show_loss_until = now + 1.5
                        pending_lost_return = True
                elif event.button == 3:
                    game.toggle_flag(gx, gy)
                    if game.is_won():
                        return "win"

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((25, 35, 25, 190))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, BG, panel, border_radius=12)
        pygame.draw.rect(screen, PANEL_BORDER, panel, 3, border_radius=12)

        title_surf = fonts["medium"].render(title, True, TEXT)
        screen.blit(title_surf, (panel.x + 16, panel.y + 12))

        stats = f"Флаги: {game.get_flagged_count()}/{mines}  |  Esc — выход  |  R — заново"
        stats_surf = fonts["small"].render(stats, True, TEXT)
        screen.blit(stats_surf, (panel.x + 16, panel.y + 36))

        if show_loss_until:
            loss = fonts["small"].render("Взрыв! Новая попытка…", True, CELL_BOOM)
            screen.blit(loss, (panel.x + 16, panel.y + panel_h - 28))

        board = game.get_board()
        for y in range(h):
            for x in range(w):
                cell = board[y][x]
                rect = pygame.Rect(
                    grid_x + x * grid_size,
                    grid_y + y * grid_size,
                    grid_size - 2,
                    grid_size - 2,
                )
                color = CELL_HIDDEN
                label = ""
                if cell["is_flagged"] and not cell["is_revealed"]:
                    color = CELL_FLAG
                    label = "F"
                elif cell["is_revealed"]:
                    if cell["is_exploded"]:
                        color = CELL_BOOM
                        label = "*"
                    elif cell["is_mine"]:
                        color = CELL_MINE
                        label = "o"
                    else:
                        color = CELL_REVEALED
                        n = cell["adjacent_mines"]
                        if n > 0:
                            label = str(n)
                pygame.draw.rect(screen, color, rect, border_radius=4)
                pygame.draw.rect(screen, PANEL_BORDER, rect, 1, border_radius=4)
                if label:
                    num_color = NUMBER_COLORS.get(int(label), TEXT) if label.isdigit() else TEXT
                    if label == "F":
                        num_color = (220, 40, 40)
                    surf = fonts["small"].render(label, True, num_color)
                    screen.blit(surf, surf.get_rect(center=rect.center))

        pygame.display.flip()
        clock.tick(60)
