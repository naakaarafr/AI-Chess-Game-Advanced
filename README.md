# AI Chess Game Advanced

A sophisticated chess game implementation featuring AI opponents powered by Google's Gemini API, with support for multiple game modes including AI vs AI, Human vs AI, and Human vs Human gameplay.

## 🎯 Features

### Game Modes
- **AI vs AI**: Watch two AI players compete against each other
- **Human vs AI**: Play against a Gemini-powered AI opponent (choose your color)
- **Human vs Human**: Classic two-player chess on the same computer

### AI Capabilities
- **Powered by Google Gemini 1.5 Flash**: Strategic AI that considers piece development, center control, king safety, and tactical opportunities
- **UCI Move Format**: Uses standard Universal Chess Interface notation for precise move communication
- **Smart Error Handling**: Robust retry mechanisms and move validation
- **Rate Limiting**: Conservative API usage (6 calls/minute, 800/day) to stay within limits

### Technical Features
- **Real-time Board Visualization**: ASCII board display with move highlighting
- **Move History Tracking**: Complete game record in UCI format
- **SVG Board Export**: Saves each position as a visual SVG file
- **Game State Management**: Comprehensive tracking of game progress and termination conditions
- **FEN Position Saving**: Export final positions in standard chess notation

### Chess Rules Implementation
- Full chess rule validation including:
  - Checkmate and stalemate detection
  - Draw conditions (insufficient material, repetition, 50-move rule)
  - Castling, en passant, and pawn promotion
  - All standard chess piece movements

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Google API key for Gemini (for AI gameplay)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/naakaarafr/AI-Chess-Game-Advanced.git
   cd AI-Chess-Game-Advanced
   ```

2. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Google API key:**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to get your API key
   - Create a `.env` file in the project directory:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

4. **Run the game:**
   ```bash
   python chess_advanced.py
   ```

### Required Dependencies
```
python-chess
requests
python-dotenv
```

Create a `requirements.txt` file with:
```
python-chess>=1.999
requests>=2.25.1
python-dotenv>=0.19.0
```

## 🎮 How to Play

### Starting the Game
1. Run the script and select your preferred game mode
2. For Human vs AI, choose whether you want to play as White or Black
3. The game begins with an ASCII representation of the chess board

### Making Moves (Human Players)
- **Move Format**: Use UCI notation (e.g., `e2e4`, `g1f3`)
- **Special Moves**:
  - Castling: `e1g1` (kingside) or `e1c1` (queenside)
  - Pawn Promotion: `a7a8q` (promote to queen), `a7a8r` (rook), etc.
  - En Passant: Standard capture notation
- **Commands**:
  - `help`: Show move format help
  - `legal`: Display all legal moves
  - `quit`: Exit the game

### Game Controls
- **Ctrl+C**: Stop the game at any time
- **Move Validation**: Invalid moves are rejected with helpful error messages
- **Auto-save**: Board positions and game history are automatically saved

## 📁 Project Structure

```
AI-Chess-Game-Advanced/
├── chess_advanced.py      # Main game script
├── requirements.txt       # Python dependencies
├── .env                  # API key configuration (create this)
├── moves/                # Auto-generated SVG board images
│   ├── move_001.svg
│   ├── move_002.svg
│   └── ...
└── final_position.fen    # Final game position
```

## 🔧 Configuration

### Rate Limiting
The game implements conservative rate limiting to respect API quotas:
- **6 calls per minute**: Prevents overwhelming the API
- **800 calls per day**: Daily usage limit
- **Automatic waiting**: Pauses when limits are reached

### Game Limits
- **Maximum moves**: 150 (configurable)
- **Error tolerance**: 3 consecutive errors before game termination
- **Timeout handling**: 30-second API timeout with retry logic

## 🎨 Output Files

### SVG Board Images
- Generated for each move in the `moves/` directory
- Includes move highlighting for easy game review
- 400x400 pixel resolution

### Game Data
- **Move History**: Complete UCI move sequence
- **Final Position**: Saved as FEN notation in `final_position.fen`
- **Game Statistics**: Duration, move count, termination reason

## 🤖 AI Behavior

### Strategy
The AI considers multiple chess principles:
- **Opening**: Piece development and center control
- **Middlegame**: Tactical opportunities and positioning
- **Endgame**: King activity and pawn promotion

### Technical Implementation
- **Temperature**: 0.3 (balanced creativity vs. consistency)
- **Max Tokens**: 20 (focused on move generation)
- **Response Validation**: Ensures moves are legal and properly formatted
- **Fallback Logic**: Multiple retry attempts with exponential backoff

## 🔍 Troubleshooting

### Common Issues

**API Key Errors:**
- Ensure your `.env` file is in the project root
- Verify your API key is valid and has quota remaining
- Check that the key has permissions for Gemini API

**Move Format Issues:**
- Use lowercase letters for squares (e.g., `e2e4`, not `E2E4`)
- Double-check piece positions on the board
- Use the `legal` command to see all valid moves

**Installation Problems:**
- Ensure Python 3.7+ is installed
- Try installing packages individually if `requirements.txt` fails
- Use virtual environments to avoid conflicts

### Performance Tips
- AI vs AI games run fastest with minimal console output
- Human vs AI games pause briefly for better user experience
- Large move histories may slow down board rendering

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional AI providers (OpenAI, Anthropic)
- Enhanced move visualization
- Opening book integration
- Chess engine evaluation
- Web interface
- Tournament mode

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 naakaarafr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **python-chess**: Excellent chess library for move validation and board representation
- **Google Gemini**: Powerful AI for strategic chess gameplay
- **Chess.com**: Inspiration for move notation and game flow

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on [GitHub](https://github.com/naakaarafr/AI-Chess-Game-Advanced/issues)
- Check existing issues for solutions
- Provide detailed error messages and reproduction steps

---

**Happy Chess Playing! ♟️**
