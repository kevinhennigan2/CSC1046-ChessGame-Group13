# chess_pygame.py
# Pygame GUI for the chess_engine

import sys
import pygame
from chess_engine import Game, Move

# --- Settings ---
TILE_SIZE = 80
BOARD_SIZE = TILE_SIZE * 8
FPS = 60

LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)
MOVE_DOT_COLOR = (50, 50, 50)
SELECT_COLOR = (246, 246, 105)
BG_COLOR = (30, 30, 30)


def load_piece_images():
    """Load all PNG chess piece images into a dictionary."""
    pieces = {}
    names = ["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]

    abbrev = {
        "King": "k",
        "Queen": "q",
        "Rook": "r",
        "Bishop": "b",
        "Knight": "n",
        "Pawn": "p",
    }

    for name in names:
        wfile = f"Chess_{abbrev[name]}lt60.png"  # white
        bfile = f"Chess_{abbrev[name]}dt60.png"  # black

        try:
            white_img = pygame.image.load(wfile)
            black_img = pygame.image.load(bfile)

            white_img = pygame.transform.scale(white_img, (TILE_SIZE, TILE_SIZE))
            black_img = pygame.transform.scale(black_img, (TILE_SIZE, TILE_SIZE))

            pieces[("White", name)] = white_img
            pieces[("Black", name)] = black_img
        except Exception as e:
            print(f"Error loading {name} images:", e)

    return pieces


def board_to_screen(x, y):
    """Map board coords (0-7,0-7 with y=0 white back rank) to screen pixels."""
    sx = x * TILE_SIZE
    sy = (7 - y) * TILE_SIZE  # invert y so white is at bottom
    return sx, sy


def screen_to_board(px, py):
    """Map pixel coords to board coords (x,y). Return None if out of board."""
    if not (0 <= px < BOARD_SIZE and 0 <= py < BOARD_SIZE):
        return None
    file_x = px // TILE_SIZE
    rank_screen = py // TILE_SIZE
    rank_y = 7 - rank_screen
    return int(file_x), int(rank_y)


def draw_board(screen, game, selected, legal_moves_from_selected, piece_images, status_text, small_font):
    # Background
    screen.fill(BG_COLOR)

    # Draw 8x8 board
    for x in range(8):
        for y in range(8):
            sx, sy = board_to_screen(x, y)
            is_light = (x + y) % 2 == 0
            color = LIGHT_COLOR if is_light else DARK_COLOR
            rect = pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, color, rect)

    # Highlight selected square
    if selected is not None:
        sx, sy = board_to_screen(*selected)
        pygame.draw.rect(screen, SELECT_COLOR, (sx, sy, TILE_SIZE, TILE_SIZE), 4)

    # Highlight legal target squares (dots)
    for mv in legal_moves_from_selected:
        tx, ty = mv.to_x, mv.to_y
        sx, sy = board_to_screen(tx, ty)
        center = (sx + TILE_SIZE // 2, sy + TILE_SIZE // 2)
        pygame.draw.circle(screen, MOVE_DOT_COLOR, center, TILE_SIZE // 8)

    # Draw pieces
    for x in range(8):
        for y in range(8):
            sq = game.board.squares[x][y]
            p = sq.piece
            if not p:
                continue
            img = piece_images.get((p.color, p.name))
            if img:
                sx, sy = board_to_screen(x, y)
                screen.blit(img, (sx, sy))

    # Status line (turn / result)
    status_y = BOARD_SIZE + 5
    text = small_font.render(status_text, True, (220, 220, 220))
    screen.blit(text, (5, status_y))


def draw_main_menu(screen, big_font, small_font):
    screen.fill(BG_COLOR)

    title = big_font.render("Chess Game", True, (255, 255, 255))
    subtitle = small_font.render("Click 'Start Game' to play", True, (220, 220, 220))

    screen.blit(title, title.get_rect(center=(BOARD_SIZE // 2, BOARD_SIZE // 2 - 80)))
    screen.blit(subtitle, subtitle.get_rect(center=(BOARD_SIZE // 2, BOARD_SIZE // 2 - 40)))

    button_rect = pygame.Rect(0, 0, 220, 60)
    button_rect.center = (BOARD_SIZE // 2, BOARD_SIZE // 2 + 20)
    pygame.draw.rect(screen, (100, 200, 100), button_rect, border_radius=10)

    btn_text = big_font.render("Start Game", True, (0, 0, 0))
    screen.blit(btn_text, btn_text.get_rect(center=button_rect.center))

    return button_rect


def draw_game_over_overlay(screen, game, big_font, small_font):
    # Dim the screen
    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE + 40), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    title = big_font.render("Game Over", True, (255, 255, 255))
    reason = game.game_over_reason or "Result"

    reason_surf = small_font.render(reason, True, (230, 230, 230))

    screen.blit(title, title.get_rect(center=(BOARD_SIZE // 2, BOARD_SIZE // 2 - 80)))
    screen.blit(reason_surf, reason_surf.get_rect(center=(BOARD_SIZE // 2, BOARD_SIZE // 2 - 40)))

    # Buttons
    play_rect = pygame.Rect(0, 0, 200, 50)
    menu_rect = pygame.Rect(0, 0, 200, 50)
    play_rect.center = (BOARD_SIZE // 2, BOARD_SIZE // 2 + 10)
    menu_rect.center = (BOARD_SIZE // 2, BOARD_SIZE // 2 + 70)

    pygame.draw.rect(screen, (100, 200, 100), play_rect, border_radius=10)
    pygame.draw.rect(screen, (200, 120, 120), menu_rect, border_radius=10)

    play_text = small_font.render("Play Again", True, (0, 0, 0))
    menu_text = small_font.render("Main Menu", True, (0, 0, 0))
    screen.blit(play_text, play_text.get_rect(center=play_rect.center))
    screen.blit(menu_text, menu_text.get_rect(center=menu_rect.center))

    return play_rect, menu_rect


def draw_promotion_overlay(screen, promotion_moves, promotion_rects, piece_images, color):
    # Dim the board
    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # Panel
    panel_width = 4 * TILE_SIZE + 40
    panel_height = TILE_SIZE + 40
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    panel_rect.center = (BOARD_SIZE // 2, BOARD_SIZE // 2)
    pygame.draw.rect(screen, (230, 230, 230), panel_rect, border_radius=10)

    # Options
    start_x = panel_rect.left + 20
    y = panel_rect.top + 20
    promotion_rects.clear()

    for i, move in enumerate(promotion_moves):
        piece_name = move.promotion
        img = piece_images.get((color, piece_name))
        r = pygame.Rect(start_x + i * TILE_SIZE, y, TILE_SIZE, TILE_SIZE)
        promotion_rects.append(r)
        pygame.draw.rect(screen, (200, 200, 200), r, border_radius=5)
        if img:
            screen.blit(img, (r.x, r.y))


def main():
    pygame.init()
    pygame.display.set_caption("Chess - Pygame")

    piece_images = load_piece_images()

    window_height = BOARD_SIZE + 40
    screen = pygame.display.set_mode((BOARD_SIZE, window_height))

    clock = pygame.time.Clock()

    big_font = pygame.font.SysFont("DejaVu Sans", 40, bold=True)
    small_font = pygame.font.SysFont("DejaVu Sans", 20)

    # UI states: "menu", "playing", "promotion", "game_over"
    ui_state = "menu"
    game = None

    selected_square = None
    legal_moves_from_selected = []

    # Main menu button rect
    start_button_rect = None

    # Promotion state
    promotion_moves = []
    promotion_rects = []
    promotion_color = None

    # Game over buttons
    play_again_rect = None
    menu_rect = None

    running = True
    while running:
        clock.tick(FPS)

        # ---- DRAW FIRST (so we have button rects) ----
        if ui_state == "menu":
            start_button_rect = draw_main_menu(screen, big_font, small_font)

        else:
            if game and game.game_over and ui_state in ("playing", "promotion"):
                ui_state = "game_over"

            if game:
                if not game.game_over:
                    status_text = f"Turn: {game.state.turn}"
                else:
                    status_text = game.game_over_reason
                draw_board(
                    screen,
                    game,
                    selected_square,
                    legal_moves_from_selected,
                    piece_images,
                    status_text,
                    small_font,
                )

                if ui_state == "promotion":
                    draw_promotion_overlay(screen, promotion_moves, promotion_rects, piece_images, promotion_color)

                if ui_state == "game_over":
                    play_again_rect, menu_rect = draw_game_over_overlay(screen, game, big_font, small_font)

        pygame.display.flip()

        # ---- HANDLE EVENTS AFTER DRAW ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break

            # MENU state
            if ui_state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button_rect and start_button_rect.collidepoint(event.pos):
                        game = Game()
                        game.start_game()
                        ui_state = "playing"
                        selected_square = None
                        legal_moves_from_selected = []

            # PLAYING state
            elif ui_state == "playing":
                if game and not game.game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    coords = screen_to_board(*pos)
                    if coords is None:
                        continue
                    bx, by = coords
                    sq = game.board.squares[bx][by]
                    current_color = game.state.turn

                    if selected_square is None:
                        # Select piece
                        if sq.piece and sq.piece.color == current_color:
                            selected_square = (bx, by)
                            all_legal = game.get_legal_moves_for_current_player()
                            legal_moves_from_selected = [
                                m for m in all_legal if m.from_x == bx and m.from_y == by
                            ]
                    else:
                        # Click same square -> deselect
                        if (bx, by) == selected_square:
                            selected_square = None
                            legal_moves_from_selected = []
                        else:
                            # Try move
                            candidate_moves = [
                                m for m in legal_moves_from_selected
                                if m.to_x == bx and m.to_y == by
                            ]
                            if candidate_moves:
                                # Multiple moves with different promotion pieces -> choose
                                if len(candidate_moves) > 1 and candidate_moves[0].promotion is not None:
                                    promotion_moves = candidate_moves
                                    promotion_color = current_color
                                    ui_state = "promotion"
                                else:
                                    move = candidate_moves[0]
                                    game.make_move(move)
                                    selected_square = None
                                    legal_moves_from_selected = []
                            else:
                                # Maybe select another own piece
                                if sq.piece and sq.piece.color == current_color:
                                    selected_square = (bx, by)
                                    all_legal = game.get_legal_moves_for_current_player()
                                    legal_moves_from_selected = [
                                        m for m in all_legal if m.from_x == bx and m.from_y == by
                                    ]
                                else:
                                    selected_square = None
                                    legal_moves_from_selected = []

            # PROMOTION state
            elif ui_state == "promotion":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for rect, move in zip(promotion_rects, promotion_moves):
                        if rect.collidepoint(mx, my):
                            if game:
                                game.make_move(move)
                            ui_state = "playing"
                            promotion_moves = []
                            promotion_rects = []
                            selected_square = None
                            legal_moves_from_selected = []
                            break

            # GAME OVER state
            elif ui_state == "game_over":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if play_again_rect and play_again_rect.collidepoint(mx, my):
                        game = Game()
                        game.start_game()
                        ui_state = "playing"
                        selected_square = None
                        legal_moves_from_selected = []
                    elif menu_rect and menu_rect.collidepoint(mx, my):
                        game = None
                        ui_state = "menu"
                        selected_square = None
                        legal_moves_from_selected = []

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
