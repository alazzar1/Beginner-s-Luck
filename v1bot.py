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

def get_move(board: chess.Board) -> chess.Move:
    #Find the best move to take based on a simple material evaluation
    depth = 2  # Look <depth> plies ahead
    best_move = None
    best_value = float('-inf') if board.turn == chess.WHITE else float('inf')
    
    for move in board.legal_moves:
        board.push(move)
        value = minimax(board, depth, board.turn == chess.BLACK)  # Look <depth> plies ahead
        board.pop()
        
        if (board.turn == chess.WHITE and value > best_value) or (board.turn == chess.BLACK and value < best_value):
            best_value = value
            best_move = move
            
    return best_move if best_move else get_move(board)

def get_difference(board: chess.Board) -> int:
    #Simple material evaluation: +1 for each white piece, -1 for each black piece
    value = 0
    for piece_type in PIECE_VALUES:
        value += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        value -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
    return value

def minimax(board: chess.Board, depth: int, maximizing: bool) -> int:
    # Minimax algorithm to evaluate the position after <depth> moves
    if depth == 0 or board.is_game_over():
        return get_difference(board)
    
    if maximizing:
        # Maximizing player (white)
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, False)
            board.pop()
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        # Minimizing player (black)
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, True)
            board.pop()
            min_eval = min(min_eval, eval)
        return min_eval