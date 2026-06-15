import chess
import random

def get_move(board: chess.Board) -> chess.Move:
    #Return a random legal move from the current position
    legal_moves = list(board.legal_moves)
    return random.choice(legal_moves) if legal_moves else None