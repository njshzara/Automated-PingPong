# Automated PingPong

A Python-based Pong game with AI players and unlimited ball speed mechanics.

## Features

- AI-controlled paddles with predictive movement
- Unlimited ball speed that increases with each paddle hit
- Real-time speed meter display
- Performance analytics panel showing:
  - Current ball speed
  - Player accuracy percentages
  - Reaction times
  - Win ratios
- Score tracking system
- Smooth paddle movement with adaptive speed

## Controls

- ESC: Quit the game
- The game is fully automated with AI players

## Technical Details

- Built with Pygame
- Uses physics-based ball movement with delta time
- Features advanced AI prediction system for paddle movement
- Includes collision detection with proper bounce mechanics
- Ball speed increases by 8% with each paddle hit (no speed limit)

## Requirements

- Python 3.x
- Pygame library

## How to Run

```bash
python pingpong_game.py
```

Enjoy watching the AI players compete as the ball gets progressively faster!