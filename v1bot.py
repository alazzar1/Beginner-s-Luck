# Imports
import chess
import random

# -- Constants ------------------------------------------------------------------
PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
# Constants for TT flags
EXACT = 0
LOWER_BOUND = 1  # beta cutoff (score is at least this good for the side to move)
UPPER_BOUND = 2  # failed low (score is at most this good)

# -- Global Variables ------------------------------------------------------------------
transposition_table = {}

# -- Main Functions ------------------------------------------------------------------
def get_move(board: chess.Board) -> chess.Move:
    #Find the best move to take based on a simple material evaluation
    max_depth = 5  # Look <max_depth> plies ahead
    if is_endgame(board):
        max_depth = 8  # Look deeper in endgame
    best_move = None
    
    # Evaluate each legal move using minimax and choose the best one
    for depth in range(1, max_depth + 1):
        if depth == max_depth:
            best_move = get_move_at_depth(board, depth, hint=best_move, last_search=True)
        else:
            best_move = get_move_at_depth(board, depth, hint=best_move, last_search=False)
            
    return best_move

def get_move_at_depth(board: chess.Board, depth: int, hint: chess.Move = None, last_search: bool = False) -> chess.Move:
    # Get the best move at a specific depth
    # Initialize limits and trackers
    alpha = float('-inf')
    beta = float('inf')
    best_move = None
    best_value = float('-inf') if board.turn == chess.WHITE else float('inf')
    moves = order_moves(board)

    # Search previous best move first
    if hint is not None:
        moves = [hint] + [move for move in moves if move != hint]
    for move in moves:
        board.push(move)
        value = minimax(board, depth - 1, alpha, beta, last_search)  # Look <depth> plies ahead
        board.pop()
        
        # For white, maximize the value; for black, minimize it
        if board.turn == chess.WHITE:
            if value > best_value or best_move is None:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)
        else:
            if value < best_value or best_move is None:
                best_value = value
                best_move = move
            beta = min(beta, best_value)
    return best_move

# -- Helper Functions ------------------------------------------------------------------
def get_difference(board: chess.Board) -> int:
    #Simple material evaluation: +1 for each white piece, -1 for each black piece
    value = 0
    for piece_type in PIECE_VALUES:
        value += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        value -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
    return value

def minimax(board: chess.Board, depth: int, alpha: int, beta: int, last_search: bool = False) -> int:
    # Minimax algorithm to evaluate the position after <depth> moves
    # Base case: if gameover, return the winner or draw
    if not any(board.legal_moves):
        return result_eval(board)
    elif board.is_repetition(3):
        return 0

    alpha_orig = alpha  # Save original alpha to determine flag at the end
    beta_orig = beta  # Save original beta to determine flag at the end

    # Transposition table lookup
    board_key = (board._transposition_key(), depth)
    if board_key in transposition_table:
        score, flag = transposition_table[board_key]
        if flag == EXACT:
            return score
        elif flag == LOWER_BOUND:
            alpha = max(alpha, score)
        elif flag == UPPER_BOUND:
            beta = min(beta, score)
        if alpha >= beta:
            return score
        
    # After transposition table lookup, check if the search should be terminated
    if depth == 0:
        if last_search:
            return quiescence(board, alpha, beta)
        else:
            return get_difference(board)

    ordered_moves = order_moves(board)

    if board.turn == chess.WHITE:
        # Maximizing player (white)
        max_eval = float('-inf')
        # Evaluate each move and update the maximum evaluation
        for move in ordered_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, last_search)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break

        # Determine and store flag
        if max_eval <= alpha_orig:
            flag = UPPER_BOUND
        elif max_eval >= beta:
            flag = LOWER_BOUND
        else:
            flag = EXACT
        transposition_table[board_key] = (max_eval, flag)
        return max_eval
    else:
        # Minimizing player (black)
        min_eval = float('inf')
        # Evaluate each move and update the minimum evaluation
        for move in ordered_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, last_search)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, min_eval)
            if alpha >= beta:
                break
        
        # Determine and store flag
        if min_eval >= beta_orig:
            flag = UPPER_BOUND
        elif min_eval <= alpha_orig:
            flag = LOWER_BOUND
        else:
            flag = EXACT
        transposition_table[board_key] = (min_eval, flag)
        return min_eval
    
def quiescence(board, alpha, beta):
    # Quiescence search to avoid horizon effect
    stand_pat = get_difference(board)
    
    # Search for captures to avoid horizon effect
    if board.turn == chess.WHITE:
        # If the stand-pat is already better than beta, return beta
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        # Evaluate each capture and update the alpha value
        for move in board.legal_moves:
            if board.is_capture(move):
                board.push(move)
                score = quiescence(board, alpha, beta)
                board.pop()
                if score >= beta:
                    return beta
                alpha = max(alpha, score)
        return alpha
    else:
        # If the stand-pat is already worse than alpha, return alpha
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)
        # Evaluate each capture and update the beta value
        for move in board.legal_moves:
            if board.is_capture(move):
                board.push(move)
                score = quiescence(board, alpha, beta)
                board.pop()
                if score <= alpha:
                    return alpha
                beta = min(beta, score)
        return beta

def order_moves(board, killer_moves=None):
    # Order moves to improve alpha-beta pruning efficiency: captures first, then others
    def priority(move):
        # If the move is a capture, prioritize it
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim is not None and attacker is not None:
                # MVV-LVA, scaled up so captures always beat quiet moves
                return -(1000 + PIECE_VALUES[victim.piece_type] * 10
                         - PIECE_VALUES[attacker.piece_type])
            else:
                # en passant: victim isn't on to_square
                return -(1000 + PIECE_VALUES[chess.PAWN] * 10
                         - PIECE_VALUES[attacker.piece_type])

        # Killer move heuristic: moves that caused cutoffs at this depth before
        if killer_moves and move in killer_moves:
            return -500

        # Quiet move heuristics
        score = 0
        if move.promotion:
            score -= 800  # promotions are usually strong

        # Prefer moves toward the center (cheap proxy for "active" moves)
        to_file = chess.square_file(move.to_square)
        to_rank = chess.square_rank(move.to_square)
        center_dist = abs(3.5 - to_file) + abs(3.5 - to_rank)
        score += center_dist  # smaller distance = more negative = higher priority

        return score

    return sorted(board.legal_moves, key=priority)

def result_eval(board: chess.Board) -> int:
    # Evaluate the result of the game (checkmate or stalemate)
    if board.is_checkmate():
        return float('inf') if board.turn == chess.BLACK else -float('inf')
    if board.is_stalemate():
        return 0
    return get_difference(board)

def is_endgame(board: chess.Board) -> bool:
    # Check if the game is in endgame
    value = 0
    for piece_type in PIECE_VALUES:
        value += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        value += len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
    return value < 20  # Simple endgame check based on material count