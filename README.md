# Chess Bot

A chess GUI application that allows you to play against different bot implementations, from simple random movers to more sophisticated minimax-based AI opponents.

## Features

- **Interactive Chess GUI** - Beautiful pygame-based interface with piece highlighting and move visualization
- **Multiple Bot Implementations**:
  - **v0bot** - Simple random move bot (great for learning)
  - **v1bot** - Advanced bot using minimax algorithm with alpha-beta pruning for stronger play
- **Customizable Gameplay**:
  - Choose to play as White, Black, or Random
  - Load custom bot implementations at runtime
  - Create custom board positions
- **Move History & Tracking** - View all moves played in the current game
- **Game State Visualization**:
  - Legal move indicators on selected pieces
  - Last move highlighting
  - Check detection and highlighting

## Requirements

- Python 3.7+
- pygame
- python-chess

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install pygame python-chess
   ```

## Usage

Run the main application:
```bash
python chess_gui.py
```

### Game Flow

1. **Start Screen** - Choose to start a new game or create a custom position
2. **Color Selection** - Select whether you play as White, Black, or a random color
3. **Bot Selection** - Load a bot implementation (v0bot or v1bot)
4. **Play** - Use mouse clicks to select and move your pieces; the bot will automatically respond

### Bot Selection

When prompted, you can load different bot implementations:
- Select the bot file from your filesystem
- The bot's move generation function will be called to determine moves

## Bot Implementations

### v0bot (Random Bot)
A simple bot that selects a random legal move from the current position. Perfect for beginners or casual play.

### v1bot (Minimax Bot)
A more sophisticated bot that:
- Uses minimax algorithm with alpha-beta pruning
- Evaluates positions based on material count
- Looks up to 4 plies (half-moves) ahead
- Assigns standard piece values:
  - Pawn: 1
  - Knight/Bishop: 3
  - Rook: 5
  - Queen: 9
  - King: 0 (not captured)

## Game Controls

- **Left Click** - Select a piece or move to a highlighted square
- **Close Window** - Quit the game

## Project Structure

```
Chess Bot/
├── chess_gui.py      # Main GUI application
├── v0bot.py          # Random move bot
├── v1bot.py          # Minimax bot with alpha-beta pruning
└── README.md         # This file
```

## Creating Custom Bots

To create your own bot implementation:

1. Create a new Python file (e.g., `mybot.py`)
2. Implement a `get_move(board: chess.Board) -> chess.Move` function that:
   - Takes a chess.Board object
   - Returns a legal chess.Move
3. Load it in the game using the bot selection dialog

Example bot template:
```python
import chess

def get_move(board: chess.Board) -> chess.Move:
    # Your move generation logic here
    legal_moves = list(board.legal_moves)
    return legal_moves[0] if legal_moves else None
```

## Future Enhancements

- Opening book integration
- Endgame tablebase support
- Adjustable search depth
- PGN import/export
- Time controls
- ELO rating display
- Multi-bot tournament mode

## License

This project is provided as-is for educational and personal use.
