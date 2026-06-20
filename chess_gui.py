from turtle import color

import chess
import random
import pygame
import sys
import os
import importlib.util
import tkinter as tk
from tkinter import filedialog

# -- Constants --------------------------------------------------------------
BOARD_SIZE   = 640
SQUARE_SIZE  = BOARD_SIZE // 8
PANEL_WIDTH  = 260
WIN_WIDTH    = BOARD_SIZE + PANEL_WIDTH
WIN_HEIGHT   = BOARD_SIZE

FPS = 30

# Palette
LIGHT_SQ     = (240, 217, 181)
DARK_SQ      = (181, 136,  99)
HIGHLIGHT    = (247, 247, 105, 180)   # selected square (with alpha)
LEGAL_DOT    = (0,   0,   0,  60)
LAST_MOVE    = (205, 210,  55, 140)
CHECK_COLOR  = (220,  50,  50, 160)

PANEL_BG     = ( 30,  30,  30)
PANEL_LIGHT  = ( 50,  50,  50)
TEXT_WHITE   = (240, 240, 240)
TEXT_GRAY    = (160, 160, 160)
ACCENT       = ( 99, 179, 237)
BTN_BG       = ( 60,  60,  60)
BTN_HOVER    = ( 80,  80,  80)
BTN_TEXT     = (220, 220, 220)

PIECE_SYMBOLS = {
    (chess.PAWN,   chess.WHITE): "♙",
    (chess.KNIGHT, chess.WHITE): "♘",
    (chess.BISHOP, chess.WHITE): "♗",
    (chess.ROOK,   chess.WHITE): "♖",
    (chess.QUEEN,  chess.WHITE): "♕",
    (chess.KING,   chess.WHITE): "♔",
    (chess.PAWN,   chess.BLACK): "♟",
    (chess.KNIGHT, chess.BLACK): "♞",
    (chess.BISHOP, chess.BLACK): "♝",
    (chess.ROOK,   chess.BLACK): "♜",
    (chess.QUEEN,  chess.BLACK): "♛",
    (chess.KING,   chess.BLACK): "♚",
}


# -- Constants --------------------------------------------------------------
def square_to_px(sq, flipped=False):
    """Top-left pixel of a chess square."""
    col = chess.square_file(sq)
    row = chess.square_rank(sq)
    if not flipped:
        row = 7 - row
    return col * SQUARE_SIZE, row * SQUARE_SIZE


def px_to_square(x, y, flipped=False):
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    rank = row if flipped else 7 - row
    if 0 <= col <= 7 and 0 <= rank <= 7:
        return chess.square(col, rank)
    return None


def draw_alpha_rect(surface, color, rect):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    s.fill(color)
    surface.blit(s, (rect[0], rect[1]))


# -- Main app --------------------------------------------------------------
class ChessApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Chess vs Random Bot")
        self.screen  = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.clock   = pygame.time.Clock()

        # Fonts — fall back gracefully on systems without the emoji font
        self._load_fonts()
        # Bot defaults — keep across resets so a loaded bot isn't cleared
        self.bot = None
        self.bot_name = "Da Beginner Bot"

        self.reset()

    def start_prompt(self):
        # Prompt the user to choose a color and start the game
        self.color_prompt()
        while True:
            # Draw the start screen
            self.screen.fill((20, 20, 20, 128))
            new_game_btn = self._draw_button("Start New Game", WIN_WIDTH//2 - 80, WIN_HEIGHT//2 - 40)
            make_position_btn = self._draw_button("Make Position", WIN_WIDTH//2 - 80, WIN_HEIGHT//2 + 40)
            pygame.display.flip()

            # Check for button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if new_game_btn.collidepoint(event.pos):
                        # Handle "Start New Game" button click
                        self.board = chess.Board()
                    if make_position_btn.collidepoint(event.pos):
                        # Handle "Make Position" button click
                        self.board = chess.Board(None)
                        self.enter_edit_mode()
                    
                    self.choose_bot_prompt()
                    return

    def color_prompt(self):
        # Prompt the user to choose a color (white, black or random)
        while True:
            # Draw the color selection screen
            self.screen.fill((20, 20, 20, 128))
            white_btn = self._draw_button("Play as White", WIN_WIDTH//2 - 100, WIN_HEIGHT//2 - 60)
            black_btn = self._draw_button("Play as Black", WIN_WIDTH//2 - 100, WIN_HEIGHT//2)
            random_btn = self._draw_button("Random Color", WIN_WIDTH//2 - 100, WIN_HEIGHT//2 + 60)
            pygame.display.flip()

            # Check for button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if white_btn.collidepoint(event.pos):
                        self.player_color = chess.WHITE
                        self.status_msg = "Playing as White"
                        return
                    if black_btn.collidepoint(event.pos):
                        self.player_color = chess.BLACK
                        self.status_msg = "Playing as Black"
                        return
                    if random_btn.collidepoint(event.pos):
                        self.player_color = random.choice([chess.WHITE, chess.BLACK])
                        if self.player_color == chess.WHITE:
                            self.status_msg = "Playing as White"
                        else:
                            self.status_msg = "Playing as Black"
                        return
                    
    def choose_bot_prompt(self):
        # Prompt the user to choose a bot file
        while True:
            self.screen.fill((20, 20, 20))
            load_bot_btn = self._draw_button("Load Bot", WIN_WIDTH//2 - 80, WIN_HEIGHT//2 - 20)
            pygame.display.flip()

            # Check for button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if load_bot_btn.collidepoint(event.pos):
                        self.load_bot()
                        return

    def place_piece(board: chess.Board, square: str, piece_type: int, color: bool):
        # Place a piece on a square.
        sq = chess.parse_square(square)
        board.set_piece_at(sq, chess.Piece(piece_type, color))

    def _load_fonts(self):
        # Try to find a font that renders chess unicode symbols
        candidates = ["segoeuisymbol", "symbola", "dejavusans", "freesans",
                      "notosans", "arial", None]
        self.piece_font = None
        for name in candidates:
            try:
                f = pygame.font.SysFont(name, int(SQUARE_SIZE * 0.82), bold=False)
                # Quick render test
                f.render("♙", True, (0, 0, 0))
                self.piece_font = f
                break
            except Exception:
                continue
        if self.piece_font is None:
            self.piece_font = pygame.font.Font(None, int(SQUARE_SIZE * 0.82))

        self.label_font   = pygame.font.SysFont("segoeui,helvetica,arial", 14)
        self.heading_font = pygame.font.SysFont("segoeui,helvetica,arial", 17, bold=True)
        self.move_font    = pygame.font.SysFont("consolasmono,couriernew,monospace", 13)
        self.btn_font     = pygame.font.SysFont("segoeui,helvetica,arial", 14, bold=True)
        self.status_font  = pygame.font.SysFont("segoeui,helvetica,arial", 15, bold=True)

    def reset(self):
        self.start_prompt()
        self.selected_sq  = None
        self.legal_targets= set()
        self.last_move    = None
        self.move_history = []   # list of SAN strings
        self.scroll_offset= 0
        self.game_over    = self.board.is_game_over()
        self.flipped      = False
        self.bot_delay    = 10    # ms countdown before bot moves

        # Edit mode state
        self.edit_mode      = False
        self.edit_selection = None   # (piece_type, color) or "EMPTY" or None

    # -- Drawing --------------------------------------------------------------
    def draw_board(self):
        for rank in range(8):
            for file in range(8):
                sq  = chess.square(file, rank)
                col = file
                row = rank if self.flipped else 7 - rank
                x, y = col * SQUARE_SIZE, row * SQUARE_SIZE
                light = (file + rank) % 2 == 0
                pygame.draw.rect(self.screen,
                                 LIGHT_SQ if light else DARK_SQ,
                                 (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # last-move highlight
        if self.last_move:
            for sq in (self.last_move.from_square, self.last_move.to_square):
                x, y = square_to_px(sq, self.flipped)
                draw_alpha_rect(self.screen, LAST_MOVE,
                                (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # check highlight
        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                x, y = square_to_px(king_sq, self.flipped)
                draw_alpha_rect(self.screen, CHECK_COLOR,
                                (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # selected square
        if self.selected_sq is not None:
            x, y = square_to_px(self.selected_sq, self.flipped)
            draw_alpha_rect(self.screen, HIGHLIGHT,
                            (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # legal move dots
        for sq in self.legal_targets:
            x, y = square_to_px(sq, self.flipped)
            cx, cy = x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2
            if self.board.piece_at(sq):
                # ring for captures
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(s, LEGAL_DOT,
                                   (SQUARE_SIZE//2, SQUARE_SIZE//2),
                                   SQUARE_SIZE//2 - 3, 5)
                self.screen.blit(s, (x, y))
            else:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(s, LEGAL_DOT,
                                   (SQUARE_SIZE//2, SQUARE_SIZE//2),
                                   SQUARE_SIZE // 6)
                self.screen.blit(s, (x, y))

        # rank / file labels
        for i in range(8):
            rank_label = str(i + 1) if not self.flipped else str(8 - i)
            file_label = "abcdefgh"[i] if not self.flipped else "hgfedcba"[i]
            col = (7 - i) if not self.flipped else i
            light_edge = (i % 2 == 0) if not self.flipped else (i % 2 != 0)
            txt_color  = DARK_SQ if light_edge else LIGHT_SQ

            r = self.label_font.render(rank_label, True, txt_color)
            self.screen.blit(r, (3, col * SQUARE_SIZE + 3))

            f = self.label_font.render(file_label, True, txt_color)
            self.screen.blit(f, (i * SQUARE_SIZE + SQUARE_SIZE - f.get_width() - 3,
                                 BOARD_SIZE - f.get_height() - 3))

    def draw_pieces(self):
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece is None:
                continue
            sym = PIECE_SYMBOLS.get((piece.piece_type, piece.color), "?")
            x, y = square_to_px(sq, self.flipped)
            cx = x + SQUARE_SIZE // 2
            cy = y + SQUARE_SIZE // 2

            # shadow
            shadow = self.piece_font.render(sym, True, (0, 0, 0))
            sr = shadow.get_rect(center=(cx + 2, cy + 2))
            shadow.set_alpha(80)
            self.screen.blit(shadow, sr)

            color = (255, 255, 255) if piece.color == chess.WHITE else (30, 30, 30)
            surf  = self.piece_font.render(sym, True, color)
            r     = surf.get_rect(center=(cx, cy))
            self.screen.blit(surf, r)

    def draw_panel(self):
        px = BOARD_SIZE
        pygame.draw.rect(self.screen, PANEL_BG,
                         (px, 0, PANEL_WIDTH, WIN_HEIGHT))

        # Title
        t = self.heading_font.render("Chess vs Beginner's Luck", True, ACCENT)
        self.screen.blit(t, (px + 12, 14))

        # Status
        pygame.draw.rect(self.screen, PANEL_LIGHT,
                         (px + 8, 40, PANEL_WIDTH - 16, 32), border_radius=6)
        s = self.status_font.render(self.status_msg, True, TEXT_WHITE)
        self.screen.blit(s, (px + 12, 47))
        if self.edit_mode:
            self._draw_edit_palette(px)
        else:
            self._draw_move_history(px)

        # Buttons
        self.btn_new  = self._draw_button("New Game",   px + 8,  WIN_HEIGHT - 46)
        self.btn_flip = self._draw_button("Flip Board", px + 8,  WIN_HEIGHT - 86)
        self.btn_load = self._draw_button("Load Bot", px + 8, WIN_HEIGHT - 166)
        edit_label = "Done Editing" if self.edit_mode else "Edit Board"
        self.btn_edit = self._draw_button(edit_label, px + 8, WIN_HEIGHT - 126,
                                          active=self.edit_mode)
        
    def _draw_move_history(self, px):
        # Move history label
        h = self.heading_font.render("Move History", True, TEXT_GRAY)
        self.screen.blit(h, (px + 12, 84))
 
        # Move history box
        box_y = 108
        box_h = WIN_HEIGHT - box_y - 180
        pygame.draw.rect(self.screen, PANEL_LIGHT,
                         (px + 8, box_y, PANEL_WIDTH - 16, box_h),
                         border_radius=6)
 
        # Render move pairs
        line_h = 18
        visible = box_h // line_h
        pairs   = []
        for i in range(0, len(self.move_history), 2):
            w = self.move_history[i]
            b = self.move_history[i + 1] if i + 1 < len(self.move_history) else ""
            pairs.append(f"{i//2+1:>3}. {w:<8} {b}")
 
        max_scroll = max(0, len(pairs) - visible)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
        visible_pairs = pairs[self.scroll_offset: self.scroll_offset + visible]
 
        # Clip to box
        clip = pygame.Rect(px + 8, box_y, PANEL_WIDTH - 16, box_h)
        self.screen.set_clip(clip)
        for i, line in enumerate(visible_pairs):
            c = (210, 210, 210) if i % 2 == 0 else (180, 180, 180)
            t = self.move_font.render(line, True, c)
            self.screen.blit(t, (px + 12, box_y + i * line_h + 4))
        self.screen.set_clip(None)
 
        # Scrollbar
        if len(pairs) > visible:
            sb_x = px + PANEL_WIDTH - 14
            sb_h = box_h
            thumb_h = max(20, int(sb_h * visible / len(pairs)))
            thumb_y = box_y + int((sb_h - thumb_h) * self.scroll_offset / max_scroll)
            pygame.draw.rect(self.screen, (80, 80, 80),
                             (sb_x, box_y, 6, sb_h), border_radius=3)
            pygame.draw.rect(self.screen, ACCENT,
                             (sb_x, thumb_y, 6, thumb_h), border_radius=3)
            
    def _draw_edit_palette(self, px):
        """Piece palette shown while in edit mode. Click a piece, then click
        a board square to place it. Click the eraser to clear squares."""
        h = self.heading_font.render("Select a Piece", True, TEXT_GRAY)
        self.screen.blit(h, (px + 12, 84))
 
        piece_order = [chess.KING, chess.QUEEN, chess.ROOK,
                       chess.BISHOP, chess.KNIGHT, chess.PAWN]
 
        cell = 50
        gap  = 8
        start_y = 110
        self.palette_rects = {}  # selection_key -> rect
 
        for col_i, color in enumerate((chess.WHITE, chess.BLACK)):
            col_x = px + 16 + col_i * (cell + gap)
            label = "White" if color == chess.WHITE else "Black"
            lbl = self.label_font.render(label, True, TEXT_GRAY)
            self.screen.blit(lbl, (col_x, start_y - 18))
 
            for row_i, piece_type in enumerate(piece_order):
                y = start_y + row_i * (cell + gap)
                rect = pygame.Rect(col_x, y, cell, cell)
 
                key = (piece_type, color)
                selected = self.edit_selection == key
                bg = ACCENT if selected else PANEL_LIGHT
                pygame.draw.rect(self.screen, bg, rect, border_radius=8)
                if selected:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect,
                                     width=2, border_radius=8)
 
                sym = PIECE_SYMBOLS[(piece_type, color)]
                fcolor = (255, 255, 255) if color == chess.WHITE else (25, 25, 25)
                surf = self.piece_font.render(sym, True, fcolor)
                # scale font down a touch for the smaller cell if needed
                r = surf.get_rect(center=rect.center)
                self.screen.blit(surf, r)
 
                self.palette_rects[key] = rect
 
        # Eraser button
        eraser_y = start_y + len(piece_order) * (cell + gap) + 6
        eraser_rect = pygame.Rect(px + 16, eraser_y, 2 * cell + gap, 38)
        selected = self.edit_selection == "EMPTY"
        bg = ACCENT if selected else PANEL_LIGHT
        pygame.draw.rect(self.screen, bg, eraser_rect, border_radius=8)
        if selected:
            pygame.draw.rect(self.screen, (255, 255, 255), eraser_rect,
                             width=2, border_radius=8)
        lbl = self.btn_font.render("Erase (empty square)", True, BTN_TEXT)
        self.screen.blit(lbl, lbl.get_rect(center=eraser_rect.center))
        self.palette_rects["EMPTY"] = eraser_rect
 
        # Clear board / Start position quick actions
        actions_y = eraser_y + 50
        self.btn_clear_board = self._draw_button("Clear Board", px + 8, actions_y)
        self.btn_start_pos   = self._draw_button("Starting Position", px + 8, actions_y + 40)
 
        # Side-to-move toggle
        turn_y = actions_y + 88
        turn_label = "Side to move: White" if self.board.turn == chess.WHITE \
                    else "Side to move: Black"
        self.btn_turn = self._draw_button(turn_label, px + 8, turn_y)

    def _draw_button(self, label, x, y, active=False):
        # Draw a button with the given label at the specified position.
        w, h = PANEL_WIDTH - 16, 34
        rect = pygame.Rect(x, y, w, h)
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        if active:
            bg = ACCENT
        else:
            bg = BTN_HOVER if hover else BTN_BG
        pygame.draw.rect(self.screen, BTN_HOVER if hover else BTN_BG, rect, border_radius=7)
        t = self.btn_font.render(label, True, BTN_TEXT)
        self.screen.blit(t, t.get_rect(center=rect.center))
        return rect

    # -- Logic --------------------------------------------------------------
    def handle_click(self, pos):
        x, y = pos
        if x >= BOARD_SIZE:
            return  # panel click handled elsewhere

        sq = px_to_square(x, y, self.flipped)
        if sq is None:
            return
        
        if self.edit_mode:
            self.handle_edit_click(sq)
            return

        if self.game_over or self.board.turn != self.player_color:
            return

        piece = self.board.piece_at(sq)

        if self.selected_sq is None:
            if piece and piece.color == self.player_color:
                self.selected_sq   = sq
                self.legal_targets = {m.to_square for m in self.board.legal_moves
                                      if m.from_square == sq}
        else:
            if sq in self.legal_targets:
                self._make_player_move(self.selected_sq, sq)
            elif piece and piece.color == self.player_color:
                self.selected_sq   = sq
                self.legal_targets = {m.to_square for m in self.board.legal_moves
                                      if m.from_square == sq}
            else:
                self.selected_sq   = None
                self.legal_targets = set()

    def handle_edit_click(self, sq):
        """Place or clear the currently selected palette piece on a square."""
        if self.edit_selection is None:
            return
        if self.edit_selection == "EMPTY":
            self.board.remove_piece_at(sq)
        else:
            piece_type, color = self.edit_selection
            self.board.set_piece_at(sq, chess.Piece(piece_type, color))

    def handle_palette_click(self, pos):
        """Handle clicks on the piece palette / quick action buttons in edit mode."""
        for key, rect in getattr(self, "palette_rects", {}).items():
            if rect.collidepoint(pos):
                self.edit_selection = key
                return
 
        if hasattr(self, "btn_clear_board") and self.btn_clear_board.collidepoint(pos):
            self.board.clear()  # empty board, keeps turn/castling defaults reset
            self.status_msg = "Board cleared"
            return
 
        if hasattr(self, "btn_start_pos") and self.btn_start_pos.collidepoint(pos):
            self.board.reset()
            self.status_msg = "Starting position loaded"
            return
 
        if hasattr(self, "btn_turn") and self.btn_turn.collidepoint(pos):
            self.board.turn = not self.board.turn
            return
        
    def enter_edit_mode(self):
        self.edit_mode      = True
        self.edit_selection = (chess.PAWN, chess.WHITE)
        self.selected_sq    = None
        self.legal_targets  = set()
        self.status_msg     = "Editing: click a piece, then a square"
 
    def exit_edit_mode(self):
        self.edit_mode      = False
        self.edit_selection = None
 
        if not self.board.is_valid():
            # Keep editing but warn — most common cause: missing/duplicate kings
            self.status_msg = f"Invalid position: {self.board.status().name} — still editing"
            self.edit_mode  = True
            return
 
        self.game_over   = False
        self.last_move   = None
        self.move_history = []
        self.scroll_offset = 0
        turn_str = "White" if self.board.turn == self.player_color else "Bot"
        self.status_msg  = "Your turn  (White)" if self.board.turn == chess.WHITE \
                           else "Your turn  (Black)"
 
        self.pick_turn()
        if self.board.turn != self.player_color:
            self.status_msg = "Bot thinking…"
            self.bot_delay  = 400

    def pick_turn(self):
        # Prompt user to choose which color's turn it is
        while True:
            # Draw the turn selection screen
            self.screen.fill((20, 20, 20, 64))
            white_btn = self._draw_button("White's Turn", WIN_WIDTH//2 - 100, WIN_HEIGHT//2 - 60)
            black_btn = self._draw_button("Black's Turn", WIN_WIDTH//2 - 100, WIN_HEIGHT//2)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if white_btn.collidepoint(pos):
                        self.board.turn = chess.WHITE
                        return
                    if black_btn.collidepoint(pos):
                        self.board.turn = chess.BLACK
                        return

    def _make_player_move(self, from_sq, to_sq):
        # Handle promotion — auto-queen for simplicity
        move = chess.Move(from_sq, to_sq)
        piece = self.board.piece_at(from_sq)
        if (piece and piece.piece_type == chess.PAWN and
                chess.square_rank(to_sq) in (0, 7)):
            move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            san = self.board.san(move)
            self.board.push(move)
            self.last_move = move
            self.move_history.append(san)
            # auto-scroll
            pairs = (len(self.move_history) + 1) // 2
            self.scroll_offset = max(0, pairs - 1)

            self.selected_sq   = None
            self.legal_targets = set()

            if self.board.is_game_over():
                self._end_game()
            else:
                self.status_msg = "Bot thinking…"
                self.bot_delay  = 400   # ms

    def load_bot(self):
        # Open file picker without showing a tkinter window
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Select Bot File",
            filetypes=[("Python files", "*.py")]
        )
        root.destroy()
    
        if not path:
            return  # user cancelled

        try:
            spec   = importlib.util.spec_from_file_location("bot", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "get_move"):
                self.status_msg = "Error: no get_move() found"
                return

            self.bot        = module
            self.bot_name   = os.path.basename(path).replace(".py", "")
            self.status_msg = f"Bot loaded: {self.bot_name}"
        except Exception as e:
            self.status_msg = f"Load error: {e}"

    def bot_play(self):
        if self.game_over or self.board.turn == self.player_color:
            return
        # Ask bot (if loaded) or pick a random legal move
        if self.bot is not None:
            try:
                move = self.bot.get_move(self.board)
            except Exception as e:
                self.status_msg = f"Bot error: {e}"
                self._end_game()
                return
        else:
            moves = list(self.board.legal_moves)
            move = random.choice(moves) if moves else None

        if move is None:
            self._end_game()
            return

        # Ensure the move is legal for the current position
        if move not in self.board.legal_moves:
            self.status_msg = "Bot returned illegal move"
            self._end_game()
            return

        san = self.board.san(move)
        self.board.push(move)
        self.last_move = move
        self.move_history.append(san)
        pairs = (len(self.move_history) + 1) // 2
        self.scroll_offset = max(0, pairs - 1)

        if self.board.is_game_over():
            self._end_game()
        else:
            self.status_msg = "Your turn  (White)" if self.player_color == chess.WHITE \
                              else "Your turn  (Black)"

    def _end_game(self):
        self.game_over = True
        outcome = self.board.outcome()
        if outcome is None:
            self.status_msg = "Game over"
            return
        if outcome.winner is None:
            reason = outcome.termination.name.replace("_", " ").title()
            self.status_msg = f"Draw — {reason}"
        elif outcome.winner == self.player_color:
            self.status_msg = "You win! 🎉"
        else:
            self.status_msg = "Bot wins!"

    # -- Main loop ------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if hasattr(self, "btn_new") and self.btn_new.collidepoint(event.pos):
                            self.reset()
                        elif hasattr(self, "btn_flip") and self.btn_flip.collidepoint(event.pos):
                            self.flipped = not self.flipped
                        elif hasattr(self, "btn_load") and self.btn_load.collidepoint(event.pos):
                            self.load_bot()
                        elif hasattr(self, "btn_edit") and self.btn_edit.collidepoint(event.pos):
                            if self.edit_mode:
                                self.exit_edit_mode()
                            else:
                                self.enter_edit_mode()
                        elif self.edit_mode and event.pos[0] >= BOARD_SIZE:
                            self.handle_palette_click(event.pos)
                        else:
                            self.handle_click(event.pos)

                if event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset = max(0, self.scroll_offset - event.y)

            # Bot move after delay
            if not self.edit_mode and not self.game_over and self.bot_delay > 0:
                self.bot_delay -= dt
                if self.bot_delay <= 0:
                    self.bot_delay = 0
                    self.bot_play()

            # Draw
            self.draw_board()
            self.draw_pieces()
            self.draw_panel()
            pygame.display.flip()


if __name__ == "__main__":
    ChessApp().run()