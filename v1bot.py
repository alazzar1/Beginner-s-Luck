# Imports
import chess
import random

# Constants
PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }

# Global variables
transposition_table = {}

def get_move(board: chess.Board) -> chess.Move:
    #Find the best move to take based on a simple material evaluation
    max_depth = 4  # Look <max_depth> plies ahead
    if is_endgame(board):
        max_depth = 6  # Look deeper in endgame
    best_value = float('-inf') if board.turn == chess.WHITE else float('inf')
    best_move = None
    best_moves = []
    
    # Evaluate each legal move using minimax and choose the best one
    for depth in range(1, max_depth + 1):
        best_moves = get_move_at_depth(board, depth, hint=best_move)
        best_move = random.choice(best_moves) if best_moves else None
            
    return random.choice(best_moves) if best_moves else get_move(board)

def get_move_at_depth(board: chess.Board, depth: int, hint: chess.Move = None) -> chess.Move:
    # Get the best move at a specific depth
    best_move = None
    best_value = float('-inf') if board.turn == chess.WHITE else float('inf')
    alpha = float('-inf')
    beta = float('inf')
    moves = order_moves(board)

    # Search previous best move first
    if hint is not None:
        moves = [hint] + [move for move in moves if move != hint]
    for move in board.legal_moves:
        board.push(move)
        value = minimax(board, depth, float('-inf'), float('inf'))  # Look <depth> plies ahead
        board.pop()
        
        # For white, maximize the value; for black, minimize it
        if board.turn == chess.WHITE:
            if value > best_value:
                best_value = value
                best_move = move
                best_moves = [move]
            elif value == best_value:
                best_moves.append(move)
            alpha = max(alpha, value)
        else:
            if value < best_value:
                best_value = value
                best_move = move
                best_moves = [move]
            elif value == best_value:
                best_moves.append(move)
            beta = min(beta, value)
    return best_moves

def get_difference(board: chess.Board) -> int:
    #Simple material evaluation: +1 for each white piece, -1 for each black piece
    value = 0
    for piece_type in PIECE_VALUES:
        value += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        value -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
    return value

def minimax(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    # Minimax algorithm to evaluate the position after <depth> moves
    # Check the transposition table for previously computed results
    board_key = (board.fen(), depth)
    if board_key in transposition_table:
        return transposition_table[board_key]

    # Base case: if depth is 0, return the material difference
    if depth == 0:
        return get_difference(board)
    elif not any(board.legal_moves):
        return result_eval(board)
    
    orded_moves = order_moves(board)
    
    # Perform minimax with alpha-beta pruning
    if board.turn == chess.WHITE:
        # Maximizing player (white)
        max_eval = float('-inf')
        for move in orded_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            # Alpha-beta pruning
            # If the maximizing player has found a better move than the minimizing player, stop evaluating
            if beta <= alpha:
                break
            transposition_table[board.fen()] = eval
        return max_eval
    else:
        # Minimizing player (black)
        min_eval = float('inf')
        for move in orded_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            # Alpha-beta pruning
            # If the minimizing player has found a better move than the maximizing player, stop evaluating
            if alpha >= beta:
                break
        transposition_table[board.fen()] = eval
        return min_eval
    
def order_moves(board):
    # Order moves to improve alpha-beta pruning efficiency: captures first, then others
    def priority(move):
        if board.is_capture(move):
            # MVV-LVA: most valuable victim, least valuable attacker
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim is not None and attacker is not None:
                return -(PIECE_VALUES[victim.piece_type] - PIECE_VALUES[attacker.piece_type] * 0.1)
        return 0
    return sorted(board.legal_moves, key=priority)

def result_eval(board: chess.Board) -> int:
    # Evaluate the result of the game (checkmate or stalemate)
    if board.is_checkmate():
        return float('inf') if board.turn == chess.BLACK else -float('inf')
    if board.is_stalemate() or board.is_repetition(3):
        return 0
    return get_difference(board)

def is_endgame(board: chess.Board) -> bool:
    # Check if the game is in endgame
    value = 0
    for piece_type in PIECE_VALUES:
        value += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        value += len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
    return value < 20  # Simple endgame check based on material count