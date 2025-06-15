import chess
import chess.svg
import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional
import re

# Load environment variables from .env file
load_dotenv()

# Enhanced Rate limiting for API calls
class RateLimiter:
    def __init__(self, max_calls_per_minute=6, max_calls_per_day=800):
        self.max_calls_per_minute = max_calls_per_minute
        self.max_calls_per_day = max_calls_per_day
        self.calls_per_minute = []
        self.calls_per_day = []
        self.last_reset_time = datetime.now()
    
    def wait_if_needed(self):
        now = datetime.now()
        current_time = time.time()
        
        # Reset daily counter if a new day has started
        if now.date() > self.last_reset_time.date():
            self.calls_per_day = []
            self.last_reset_time = now
            print(f"Daily quota reset at {now.strftime('%H:%M:%S')}")
        
        # Remove calls older than 1 minute
        minute_ago = current_time - 60
        self.calls_per_minute = [call_time for call_time in self.calls_per_minute if call_time > minute_ago]
        
        # Remove calls older than 1 day
        day_ago = current_time - (24 * 60 * 60)
        self.calls_per_day = [call_time for call_time in self.calls_per_day if call_time > day_ago]
        
        # Check daily limit first
        if len(self.calls_per_day) >= self.max_calls_per_day:
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            wait_seconds = (tomorrow - now).total_seconds()
            print(f"Daily quota of {self.max_calls_per_day} calls exceeded.")
            print(f"Waiting until tomorrow ({tomorrow.strftime('%Y-%m-%d %H:%M:%S')}) - {wait_seconds/3600:.1f} hours")
            time.sleep(wait_seconds)
            self.calls_per_minute = []
            self.calls_per_day = []
            return
        
        # Check per-minute limit
        if len(self.calls_per_minute) >= self.max_calls_per_minute:
            oldest_call = min(self.calls_per_minute)
            wait_time = 60 - (current_time - oldest_call) + 5
            
            if wait_time > 0:
                print(f"Rate limit reached ({len(self.calls_per_minute)}/{self.max_calls_per_minute} calls per minute).")
                print(f"Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                
                # Refresh the list after waiting
                current_time = time.time()
                minute_ago = current_time - 60
                self.calls_per_minute = [call_time for call_time in self.calls_per_minute if call_time > minute_ago]
        
        # Record this call
        self.calls_per_minute.append(current_time)
        self.calls_per_day.append(current_time)
        
        # Show usage periodically
        if len(self.calls_per_minute) % 2 == 1:
            print(f"📊 API usage: {len(self.calls_per_minute)}/{self.max_calls_per_minute} this minute, {len(self.calls_per_day)}/{self.max_calls_per_day} today")

# Global rate limiter
rate_limiter = RateLimiter()

# Global game state
class GameState:
    def __init__(self):
        self.should_terminate = False
        self.termination_reason = ""
        self.move_count = 0
        self.consecutive_errors = 0
        
    def terminate_game(self, reason):
        self.should_terminate = True
        self.termination_reason = reason
        print(f"🛑 Game terminating: {reason}")

game_state = GameState()

class DirectGeminiChessPlayer:
    """Chess player that calls Gemini API directly"""
    
    def __init__(self, color: str, api_key: str):
        self.color = color
        self.name = f"AI_{color.title()}"
        self.api_key = api_key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        opponent_color = "black" if color == "white" else "white"
        self.system_prompt = f"""You are an expert chess player playing as {color} pieces.
Your opponent plays as {opponent_color} pieces.

CRITICAL INSTRUCTIONS:
1. You must respond with ONLY a valid UCI move notation (e.g., e2e4, g1f3, e1g1, a7a8q)
2. Do NOT include any explanations, comments, or extra text
3. Do NOT use algebraic notation (like Nf3) - use UCI format only
4. Your response must be exactly one move like: e2e4
5. Make sure your move is legal in the current position

You are a strong chess player who thinks strategically about piece development, control of center, king safety, and tactical opportunities."""

    def get_move(self, board: chess.Board) -> Optional[str]:
        """Get a chess move from Gemini API directly"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                rate_limiter.wait_if_needed()
                
                # Get current position info
                legal_moves = list(board.legal_moves)
                if not legal_moves:
                    print(f"❌ No legal moves available for {self.name}")
                    return None
                    
                legal_moves_str = ", ".join([str(move) for move in legal_moves[:15]])
                
                # Create the prompt
                prompt = f"""{self.system_prompt}

Current chess position (FEN): {board.fen()}

Visual board:
{board}

It's {self.color}'s turn. Legal moves: {legal_moves_str}

Your move (UCI format only):"""

                # Prepare API request
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 20,
                        "candidateCount": 1,
                        "stopSequences": ["\n", " "]
                    }
                }
                
                print(f"🤔 {self.name} is thinking... (attempt {retry_count + 1})")
                
                # Make API call
                response = requests.post(
                    self.api_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ API error for {self.name}: {response.status_code} - {response.text}")
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(2 ** retry_count)  # Exponential backoff
                    continue
                
                result = response.json()
                
                # Extract move from response
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    move_str = self._extract_move_from_response(content, legal_moves)
                    
                    if move_str:
                        print(f"💭 {self.name} suggests: {move_str}")
                        return move_str
                    else:
                        print(f"❌ Could not extract valid move from response: '{content.strip()}'")
                        retry_count += 1
                        if retry_count < max_retries:
                            time.sleep(1)
                        continue
                
                print(f"❌ No valid response from {self.name}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)
                
            except requests.exceptions.Timeout:
                print(f"⏱️ API timeout for {self.name} (attempt {retry_count + 1})")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)
            except requests.exceptions.RequestException as e:
                print(f"❌ API request error for {self.name}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)
            except Exception as e:
                print(f"❌ Error getting move from {self.name}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)
        
        print(f"❌ {self.name} failed after {max_retries} attempts")
        return None

    def _extract_move_from_response(self, content: str, legal_moves) -> Optional[str]:
        """Extract a valid UCI move from the API response"""
        # Clean the content
        content = content.strip().lower()
        
        # Try to find a UCI move pattern in the response
        uci_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
        matches = re.findall(uci_pattern, content)
        
        # Check each match against legal moves
        for match in matches:
            try:
                move = chess.Move.from_uci(match)
                if move in legal_moves:
                    return match
            except ValueError:
                continue
        
        # If no pattern match, try the first word
        first_word = content.split()[0] if content.split() else ""
        if first_word:
            try:
                move = chess.Move.from_uci(first_word)
                if move in legal_moves:
                    return first_word
            except ValueError:
                pass
        
        return None


class HumanChessPlayer:
    """Human chess player that gets moves from user input"""
    
    def __init__(self, color: str):
        self.color = color
        self.name = f"Human_{color.title()}"
    
    def get_move(self, board: chess.Board) -> Optional[str]:
        """Get a chess move from human input"""
        legal_moves = list(board.legal_moves)
        legal_moves_str = ", ".join([str(move) for move in legal_moves[:12]])
        
        print(f"\n🎯 {self.name}, it's your turn!")
        print(f"Legal moves: {legal_moves_str}")
        if len(legal_moves) > 12:
            print(f"... and {len(legal_moves) - 12} more moves")
        
        while True:
            try:
                print(f"\nEnter your move in UCI format (e.g., e2e4, g1f3):")
                print("Or type 'help' for move format help, 'legal' to see all legal moves, 'quit' to exit")
                
                user_input = input("Your move: ").strip().lower()
                
                if user_input == 'quit':
                    game_state.terminate_game("Human player quit")
                    return None
                elif user_input == 'help':
                    self._show_help()
                    continue
                elif user_input == 'legal':
                    self._show_all_legal_moves(legal_moves)
                    continue
                elif user_input == '':
                    print("❌ Please enter a move!")
                    continue
                
                # Try to parse the move
                try:
                    move = chess.Move.from_uci(user_input)
                    if move in legal_moves:
                        print(f"✅ {self.name} plays: {user_input}")
                        return user_input
                    else:
                        print(f"❌ Illegal move: {user_input}")
                        print("💡 Tip: Make sure the move is legal in the current position")
                except ValueError:
                    print(f"❌ Invalid move format: {user_input}")
                    print("💡 Tip: Use UCI format like 'e2e4' or 'g1f3'")
                
            except KeyboardInterrupt:
                print("\n🛑 Game interrupted by user")
                game_state.terminate_game("User interrupted")
                return None
            except EOFError:
                print("\n🛑 Input ended")
                game_state.terminate_game("Input ended")
                return None
    
    def _show_help(self):
        """Show help for move input format"""
        print("\n📚 UCI Move Format Help:")
        print("   • Normal move: e2e4 (from e2 to e4)")
        print("   • Knight move: g1f3 (knight from g1 to f3)")
        print("   • Castling: e1g1 (kingside) or e1c1 (queenside)")
        print("   • Pawn promotion: a7a8q (promote to queen)")
        print("     - q=queen, r=rook, b=bishop, n=knight")
        print("   • En passant: e5d6 (just like normal capture)")
    
    def _show_all_legal_moves(self, legal_moves):
        """Show all legal moves in a readable format"""
        print(f"\n📋 All {len(legal_moves)} legal moves:")
        for i, move in enumerate(legal_moves):
            if i % 8 == 0:
                print()
            print(f"{str(move):6}", end=" ")
        print("\n")

class ChessGame:
    """Chess game controller using direct API calls"""
    
    def __init__(self, api_key: str, game_mode: str = "ai_vs_ai", human_color: str = "white"):
        self.board = chess.Board()
        self.move_history = []
        self.game_mode = game_mode
        self.max_consecutive_errors = 3  # Reduced from 5
        
        # Validate inputs
        if game_mode not in ["ai_vs_ai", "human_vs_ai", "human_vs_human"]:
            raise ValueError(f"Invalid game mode: {game_mode}")
        if human_color not in ["white", "black"]:
            raise ValueError(f"Invalid human color: {human_color}")
        
        # Create players based on game mode
        if game_mode == "ai_vs_ai":
            self.white_player = DirectGeminiChessPlayer("white", api_key)
            self.black_player = DirectGeminiChessPlayer("black", api_key)
        elif game_mode == "human_vs_ai":  
            if human_color == "white":
                self.white_player = HumanChessPlayer("white")
                self.black_player = DirectGeminiChessPlayer("black", api_key)
            else:
                self.white_player = DirectGeminiChessPlayer("white", api_key)
                self.black_player = HumanChessPlayer("black")
        elif game_mode == "human_vs_human":
            self.white_player = HumanChessPlayer("white")
            self.black_player = HumanChessPlayer("black")
        
    def _validate_and_make_move(self, uci_move_str: str) -> bool:
        """Validate and execute a move on the board"""
        try:
            # Clean the move string
            uci_move_str = uci_move_str.strip().lower()
            
            # Parse UCI move
            move = chess.Move.from_uci(uci_move_str)
            
            # Check if move is legal
            if move not in self.board.legal_moves:
                legal_moves = [str(m) for m in list(self.board.legal_moves)[:8]]
                print(f"❌ Illegal move: {uci_move_str}")
                print(f"   Legal moves: {', '.join(legal_moves)}...")
                return False
            
            # Execute the move
            self.board.push(move)
            game_state.move_count += 1
            self.move_history.append(uci_move_str)
            
            print(f"✅ Move {game_state.move_count}: {uci_move_str}")
            
            # Save board visualization
            self._save_board_svg()
            
            # Reset consecutive errors on successful move
            game_state.consecutive_errors = 0
            
            return True
            
        except ValueError as e:
            print(f"❌ Invalid UCI move format: {uci_move_str} - {e}")
            return False
        except Exception as e:
            print(f"❌ Error making move: {e}")
            return False
    
    def _save_board_svg(self):
        """Save current board position as SVG"""
        try:
            moves_dir = 'moves'
            os.makedirs(moves_dir, exist_ok=True)
            svg_filename = os.path.join(moves_dir, f'move_{game_state.move_count:03d}.svg')
            
            # Create SVG with move highlights
            last_move = None
            if self.board.move_stack:
                last_move = self.board.move_stack[-1]
            
            svg_output = chess.svg.board(self.board, lastmove=last_move, size=400)
            with open(svg_filename, 'w', encoding='utf-8') as file:
                file.write(svg_output)
            print(f"💾 Board saved: {svg_filename}")
        except Exception as e:
            print(f"⚠️ Could not save SVG: {e}")
    
    def _check_game_over(self) -> bool:
        """Check if game has ended"""
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn else "White"
            game_state.terminate_game(f"CHECKMATE! {winner} wins!")
            return True
        elif self.board.is_stalemate():
            game_state.terminate_game("STALEMATE! Draw.")
            return True
        elif self.board.is_insufficient_material():
            game_state.terminate_game("DRAW! Insufficient material.")
            return True
        elif self.board.is_fivefold_repetition():
            game_state.terminate_game("DRAW! Fivefold repetition.")
            return True
        elif self.board.is_seventyfive_moves():
            game_state.terminate_game("DRAW! Seventy-five move rule.")
            return True
        elif self.board.can_claim_draw():
            game_state.terminate_game("DRAW! Draw can be claimed.")
            return True
        
        return False
    
    def _display_board(self):
        """Display current board state"""
        print(f"\n📋 Position after move {game_state.move_count}:")
        print(f"{'White' if self.board.turn else 'Black'} to move")
        
        # Check for check
        if self.board.is_check():
            print("⚠️  CHECK!")
        
        print(self.board)
        print("-" * 60)
    
    def play_game(self, max_moves: int = 150):
        """Main game loop"""
        print(f"🚀 Starting {self.game_mode.upper().replace('_', ' ')} Chess Game!")
        print(f"🎮 Game mode: {self.game_mode}")
        print("📋 Initial position:")
        print(self.board)
        print("-" * 60)
        
        start_time = datetime.now()
        
        try:
            while not game_state.should_terminate and game_state.move_count < max_moves:
                # Check if game is already over
                if self._check_game_over():
                    break
                
                # Determine current player
                current_player = self.white_player if self.board.turn else self.black_player
                
                # Get move from current player
                move_str = current_player.get_move(self.board)
                
                if move_str is None:
                    game_state.consecutive_errors += 1
                    print(f"❌ {current_player.name} failed to provide a move (errors: {game_state.consecutive_errors})")
                    
                    if game_state.consecutive_errors >= self.max_consecutive_errors:
                        game_state.terminate_game(f"Too many consecutive errors from {current_player.name}")
                        break
                    
                    # For AI players, wait and try again. For humans, they might have quit
                    if isinstance(current_player, DirectGeminiChessPlayer):
                        print("⏳ Waiting before retry...")
                        time.sleep(5)
                        continue
                    else:
                        # Human player quit or had input error
                        break
                
                # Validate and make the move
                if not self._validate_and_make_move(move_str):
                    game_state.consecutive_errors += 1
                    print(f"❌ Invalid move from {current_player.name}: {move_str} (errors: {game_state.consecutive_errors})")
                    
                    if game_state.consecutive_errors >= self.max_consecutive_errors:
                        game_state.terminate_game("Too many invalid moves")
                        break
                    
                    # For AI players, wait before trying again
                    if isinstance(current_player, DirectGeminiChessPlayer):
                        print("⏳ Waiting before retry...")
                        time.sleep(3)
                    continue
                
                # Display board
                self._display_board()
                
                # Brief pause between moves
                if self.game_mode == "ai_vs_ai":
                    time.sleep(2)
                elif isinstance(current_player, DirectGeminiChessPlayer):
                    time.sleep(1)
                
            # Check if we hit move limit
            if game_state.move_count >= max_moves:
                game_state.terminate_game(f"Maximum moves ({max_moves}) reached")
                
        except KeyboardInterrupt:
            print("\n🛑 Game stopped by user")
            game_state.terminate_game("User interrupted")
        except Exception as e:
            print(f"❌ Game error: {e}")
            game_state.terminate_game(f"Error: {e}")
        
        # Print final statistics
        self._print_final_stats(start_time)
    
    def _print_final_stats(self, start_time):
        """Print game statistics"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🏁 GAME OVER")
        print(f"📊 Final Statistics:")
        print(f"   • Total moves: {game_state.move_count}")
        print(f"   • Duration: {duration}")
        print(f"   • Reason: {game_state.termination_reason}")
        print(f"   • Move history: {' '.join(self.move_history)}")
        
        if self.board.is_game_over():
            result = self.board.result()
            if result == "1-0":
                print(f"🏆 Winner: White")
            elif result == "0-1":
                print(f"🏆 Winner: Black")
            else:
                print(f"🤝 Result: Draw ({result})")
        
        print(f"\n📋 Final position:")
        print(self.board)
        
        # Save final position
        try:
            with open('final_position.fen', 'w') as f:
                f.write(self.board.fen())
            print("💾 Final position saved to final_position.fen")
        except Exception as e:
            print(f"⚠️ Could not save final position: {e}")

def select_game_mode():
    """Interactive game mode selection"""
    print("\n🎮 Select Game Mode:")
    print("1. AI vs AI")
    print("2. Human vs AI")
    print("3. Human vs Human")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice == "1":
                return "ai_vs_ai", "white"
            elif choice == "2":
                print("\nChoose your color:")
                print("1. White (you go first)")
                print("2. Black (AI goes first)")
                color_choice = input("Enter your choice (1-2): ").strip()
                if color_choice == "1":
                    return "human_vs_ai", "white"
                elif color_choice == "2":
                    return "human_vs_ai", "black"
                else:
                    print("❌ Invalid choice. Please enter 1 or 2.")
            elif choice == "3":
                return "human_vs_human", "white"
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n🛑 Exiting...")
            sys.exit(0)

def main():
    # Check if Google API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    
    print("🚀 Enhanced Chess Game with Direct Gemini API")
    print("🔧 Improved error handling and move validation")
    print("📊 Conservative rate limiting: 6 calls/minute, 800/day")
    print("🎮 Press Ctrl+C anytime to stop")
    print("-" * 60)
    
    # Select game mode
    game_mode, human_color = select_game_mode()
    
    # Check API key only if needed
    if game_mode in ["ai_vs_ai", "human_vs_ai"] and not api_key:
        print("\n❌ Error: Google API key required for AI players")
        print("Create a .env file in your project directory with:")
        print("GOOGLE_API_KEY=your_api_key_here")
        print("You can get your API key from: https://makersuite.google.com/app/apikey")
        return

    # Create and start the game
    try:
        game = ChessGame(api_key, game_mode, human_color)
        game.play_game(max_moves=150)
    except Exception as e:
        print(f"❌ Failed to start game: {e}")

if __name__ == "__main__":
    main()