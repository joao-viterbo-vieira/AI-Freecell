import pygame
import sys
import random
from enum import Enum
from typing import List, Tuple, Optional, Dict, Set, Callable

# Initialize pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (169, 169, 169)

# Card dimensions
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_MARGIN = 10
FREECELL_MARGIN = 20
CASCADE_MARGIN = 20

# Game dimensions
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
HEADER_HEIGHT = 50

# Fonts
FONT = pygame.font.SysFont("Arial", 16)
HEADER_FONT = pygame.font.SysFont("Arial", 24)


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

    def color(self):
        if self in (Suit.HEARTS, Suit.DIAMONDS):
            return RED
        return BLACK


class Card:
    def __init__(self, rank: int, suit: Suit):
        self.rank = rank
        self.suit = suit
        self.rect = pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT)
        self.selected = False

    def __str__(self):
        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks.get(self.rank, str(self.rank))
        return f"{rank_str}{self.suit.value}"

    def draw(self, surface, x, y):
        # Draw card background
        self.rect.x, self.rect.y = x, y
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK if self.selected else DARK_GRAY, self.rect, 2)

        # Draw rank and suit
        rank_map = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = rank_map.get(self.rank, str(self.rank))

        rank_text = FONT.render(rank_str, True, self.suit.color())
        suit_text = FONT.render(self.suit.value, True, self.suit.color())

        # Draw at top-left
        surface.blit(rank_text, (x + 5, y + 5))
        surface.blit(suit_text, (x + 5 + rank_text.get_width(), y + 5))

        # Draw in center (bigger)
        big_suit = pygame.font.SysFont("Arial", 40).render(
            self.suit.value, True, self.suit.color()
        )
        surface.blit(
            big_suit,
            (
                x + CARD_WIDTH // 2 - big_suit.get_width() // 2,
                y + CARD_HEIGHT // 2 - big_suit.get_height() // 2,
            ),
        )

        # Draw at bottom-right (inverted)
        bottom_rank = FONT.render(rank_str, True, self.suit.color())
        bottom_suit = FONT.render(self.suit.value, True, self.suit.color())
        surface.blit(
            bottom_suit,
            (
                x + CARD_WIDTH - 5 - bottom_suit.get_width() - bottom_rank.get_width(),
                y + CARD_HEIGHT - 25,
            ),
        )
        surface.blit(
            bottom_rank,
            (x + CARD_WIDTH - 5 - bottom_rank.get_width(), y + CARD_HEIGHT - 25),
        )


class Location(Enum):
    FREECELL = "freecell"
    FOUNDATION = "foundation"
    CASCADE = "cascade"


class Move:
    def __init__(
        self,
        card: Card,
        from_location: Location,
        from_index: int,
        to_location: Location,
        to_index: int,
    ):
        self.card = card
        self.from_location = from_location
        self.from_index = from_index
        self.to_location = to_location
        self.to_index = to_index

    def __str__(self):
        return f"Move {self.card} from {self.from_location.value}[{self.from_index}] to {self.to_location.value}[{self.to_index}]"


class FreeCellGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FreeCellAI - An AI-Ready FreeCellGame")

        self.freecells = [None] * 4
        self.foundations = {suit: [] for suit in Suit}
        self.cascades = [[] for _ in range(8)]

        self.selected_card = None
        self.selected_location = None
        self.selected_index = None

        self.moves_history = []
        self.current_algorithm = None
        self.algorithm_running = False
        self.algorithm_thinking = False
        self.algorithm_name = "None"

        # Initialize timer
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.moves_count = 0

        # Areas for clicking buttons
        self.new_game_button = pygame.Rect(SCREEN_WIDTH - 130, 10, 120, 30)
        self.hint_button = pygame.Rect(SCREEN_WIDTH - 260, 10, 120, 30)
        self.algo_button = pygame.Rect(SCREEN_WIDTH - 390, 10, 120, 30)

        self.deal_cards()

    def deal_cards(self):
        # Clear all areas
        self.freecells = [None] * 4
        self.foundations = {suit: [] for suit in Suit}
        self.cascades = [[] for _ in range(8)]
        self.moves_history = []
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.moves_count = 0

        # Create deck
        deck = []
        for suit in Suit:
            for rank in range(1, 14):  # 1 = Ace, 13 = King
                deck.append(Card(rank, suit))

        # Shuffle
        random.shuffle(deck)

        # Deal to cascades
        for i, card in enumerate(deck):
            cascade_index = i % 8
            self.cascades[cascade_index].append(card)

    def is_valid_move(self, card: Card, to_location: Location, to_index: int) -> bool:
        # Moving to freecell
        if to_location == Location.FREECELL:
            return self.freecells[to_index] is None

        # Moving to foundation
        elif to_location == Location.FOUNDATION:
            foundation = self.foundations[Suit(to_index)]
            if not foundation:  # Empty foundation
                return card.rank == 1  # Only Ace can start a foundation
            top_card = foundation[-1]
            return card.suit == top_card.suit and card.rank == top_card.rank + 1

        # Moving to cascade
        elif to_location == Location.CASCADE:
            cascade = self.cascades[to_index]
            if not cascade:  # Empty cascade
                return True  # Any card can be placed on an empty cascade
            top_card = cascade[-1]

            # Check if card is one rank lower and opposite color
            return (
                card.rank == top_card.rank - 1
                and card.suit.color() != top_card.suit.color()
            )

        return False

    def get_valid_moves(
        self, card: Card = None, from_location: Location = None, from_index: int = None
    ) -> List[Move]:
        valid_moves = []

        # If no specific card is provided, get all possible moves
        if card is None:
            # Try all cards at the end of cascades
            for i, cascade in enumerate(self.cascades):
                if cascade:
                    card = cascade[-1]
                    valid_moves.extend(self.get_valid_moves(card, Location.CASCADE, i))

            # Try all freecell cards
            for i, card in enumerate(self.freecells):
                if card:
                    valid_moves.extend(self.get_valid_moves(card, Location.FREECELL, i))

            return valid_moves

        # Check moves to freecells
        for i in range(4):
            if self.is_valid_move(card, Location.FREECELL, i):
                valid_moves.append(
                    Move(card, from_location, from_index, Location.FREECELL, i)
                )

        # Check moves to foundations
        for suit in Suit:
            if self.is_valid_move(card, Location.FOUNDATION, suit.value):
                valid_moves.append(
                    Move(
                        card, from_location, from_index, Location.FOUNDATION, suit.value
                    )
                )

        # Check moves to cascades
        for i in range(8):
            if self.is_valid_move(card, Location.CASCADE, i):
                valid_moves.append(
                    Move(card, from_location, from_index, Location.CASCADE, i)
                )

        return valid_moves

    def make_move(self, move: Move) -> bool:
        # Check if move is valid
        if not self.is_valid_move(move.card, move.to_location, move.to_index):
            return False

        # Remove card from source
        if move.from_location == Location.FREECELL:
            self.freecells[move.from_index] = None
        elif move.from_location == Location.CASCADE:
            self.cascades[move.from_index].pop()

        # Add card to destination
        if move.to_location == Location.FREECELL:
            self.freecells[move.to_index] = move.card
        elif move.to_location == Location.FOUNDATION:
            self.foundations[Suit(move.to_index)].append(move.card)
        elif move.to_location == Location.CASCADE:
            self.cascades[move.to_index].append(move.card)

        # Record move in history
        self.moves_history.append(move)
        self.moves_count += 1
        return True

    def get_card_at_pos(self, pos) -> Tuple[Optional[Card], Location, int]:
        x, y = pos

        # Check freecells
        for i in range(4):
            freecell_x = FREECELL_MARGIN + i * (CARD_WIDTH + CARD_MARGIN)
            freecell_y = HEADER_HEIGHT + CARD_MARGIN
            freecell_rect = pygame.Rect(freecell_x, freecell_y, CARD_WIDTH, CARD_HEIGHT)

            if freecell_rect.collidepoint(x, y) and self.freecells[i]:
                return self.freecells[i], Location.FREECELL, i

        # Check foundations
        for i, suit in enumerate(Suit):
            foundation_x = (
                SCREEN_WIDTH - FREECELL_MARGIN - (4 - i) * (CARD_WIDTH + CARD_MARGIN)
            )
            foundation_y = HEADER_HEIGHT + CARD_MARGIN
            foundation_rect = pygame.Rect(
                foundation_x, foundation_y, CARD_WIDTH, CARD_HEIGHT
            )

            if foundation_rect.collidepoint(x, y) and self.foundations[suit]:
                return self.foundations[suit][-1], Location.FOUNDATION, suit.value

        # Check cascades
        for i in range(8):
            cascade = self.cascades[i]
            if not cascade:
                continue

            cascade_x = CASCADE_MARGIN + i * (CARD_WIDTH + CARD_MARGIN)

            # Only the last card in a cascade can be selected
            card = cascade[-1]
            cascade_y = (
                HEADER_HEIGHT
                + CARD_HEIGHT
                + 3 * CARD_MARGIN
                + (len(cascade) - 1) * (CARD_HEIGHT // 3)
            )
            card_rect = pygame.Rect(cascade_x, cascade_y, CARD_WIDTH, CARD_HEIGHT)

            if card_rect.collidepoint(x, y):
                return card, Location.CASCADE, i

        return None, None, None

    def get_target_location(self, pos) -> Tuple[Location, int]:
        x, y = pos

        # Check freecells
        for i in range(4):
            freecell_x = FREECELL_MARGIN + i * (CARD_WIDTH + CARD_MARGIN)
            freecell_y = HEADER_HEIGHT + CARD_MARGIN
            freecell_rect = pygame.Rect(freecell_x, freecell_y, CARD_WIDTH, CARD_HEIGHT)

            if freecell_rect.collidepoint(x, y):
                return Location.FREECELL, i

        # Check foundations
        for i, suit in enumerate(Suit):
            foundation_x = (
                SCREEN_WIDTH - FREECELL_MARGIN - (4 - i) * (CARD_WIDTH + CARD_MARGIN)
            )
            foundation_y = HEADER_HEIGHT + CARD_MARGIN
            foundation_rect = pygame.Rect(
                foundation_x, foundation_y, CARD_WIDTH, CARD_HEIGHT
            )

            if foundation_rect.collidepoint(x, y):
                return Location.FOUNDATION, suit.value

        # Check cascades
        for i in range(8):
            cascade_x = CASCADE_MARGIN + i * (CARD_WIDTH + CARD_MARGIN)
            cascade_rect = pygame.Rect(
                cascade_x,
                HEADER_HEIGHT + CARD_HEIGHT + 3 * CARD_MARGIN,
                CARD_WIDTH,
                SCREEN_HEIGHT - HEADER_HEIGHT - CARD_HEIGHT - 3 * CARD_MARGIN,
            )

            if cascade_rect.collidepoint(x, y):
                return Location.CASCADE, i

        return None, None

    def is_game_won(self) -> bool:
        # Check if all foundations are complete
        for suit in Suit:
            if len(self.foundations[suit]) != 13:
                return False
        return True

    def is_game_over(self) -> bool:
        # Game is won
        if self.is_game_won():
            return True

        # Check if there are any valid moves left
        return len(self.get_valid_moves()) == 0

    def get_hint(self) -> Optional[Move]:
        # If an algorithm is set, use it to get a hint
        if self.current_algorithm:
            self.algorithm_thinking = True
            hint = self.current_algorithm.get_next_move(self)
            self.algorithm_thinking = False
            return hint

        # Basic hint strategy: try to move to foundations first
        for i, cascade in enumerate(self.cascades):
            if not cascade:
                continue
            card = cascade[-1]
            # Try moving to foundation
            for suit in Suit:
                if self.is_valid_move(card, Location.FOUNDATION, suit.value):
                    return Move(
                        card, Location.CASCADE, i, Location.FOUNDATION, suit.value
                    )

        # Try freecells to foundations
        for i, card in enumerate(self.freecells):
            if not card:
                continue
            for suit in Suit:
                if self.is_valid_move(card, Location.FOUNDATION, suit.value):
                    return Move(
                        card, Location.FREECELL, i, Location.FOUNDATION, suit.value
                    )

        # Simple strategy: find any valid move
        valid_moves = self.get_valid_moves()
        if valid_moves:
            return valid_moves[0]

        return None

    def run_algorithm(self):
        if not self.current_algorithm or self.algorithm_running:
            return

        self.algorithm_running = True

        while self.algorithm_running and not self.is_game_over():
            # Get next move from algorithm
            move = self.current_algorithm.get_next_move(self)
            if not move:
                break

            # Make the move
            self.make_move(move)

            # Update display and add a delay to see moves
            self.draw()
            pygame.display.flip()
            pygame.time.delay(500)  # 500ms delay between moves

            # Check for quit event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.algorithm_running = False

        self.algorithm_running = False

    def set_algorithm(self, algorithm, name):
        self.current_algorithm = algorithm
        self.algorithm_name = name

    def cycle_algorithm(self):
        # Add your algorithms here
        algorithms = [
            (None, "None"),
            (RandomAlgorithm(), "Random"),
            (GreedyAlgorithm(), "Greedy"),
        ]

        # Find current algorithm index and cycle to next
        current_index = 0
        for i, (algo, name) in enumerate(algorithms):
            if name == self.algorithm_name:
                current_index = i
                break

        # Move to next algorithm
        next_index = (current_index + 1) % len(algorithms)
        self.current_algorithm, self.algorithm_name = algorithms[next_index]

    def draw(self):
        self.screen.fill(GREEN)

        # Update elapsed time
        if not self.is_game_over():
            self.elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000

        # Draw header
        pygame.draw.rect(self.screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))

        # Draw time and moves
        time_text = HEADER_FONT.render(
            f"Time: {self.elapsed_time // 60:02d}:{self.elapsed_time % 60:02d}",
            True,
            WHITE,
        )
        self.screen.blit(time_text, (10, 10))

        moves_text = HEADER_FONT.render(f"Moves: {self.moves_count}", True, WHITE)
        self.screen.blit(moves_text, (150, 10))

        # Draw algorithm name
        algo_text = HEADER_FONT.render(f"Algorithm: {self.algorithm_name}", True, WHITE)
        self.screen.blit(algo_text, (280, 10))

        # Draw buttons
        pygame.draw.rect(self.screen, BLUE, self.new_game_button)
        new_game_text = FONT.render("New Game", True, WHITE)
        self.screen.blit(
            new_game_text, (self.new_game_button.x + 20, self.new_game_button.y + 8)
        )

        pygame.draw.rect(self.screen, BLUE, self.hint_button)
        hint_text = FONT.render("Hint", True, WHITE)
        self.screen.blit(hint_text, (self.hint_button.x + 40, self.hint_button.y + 8))

        pygame.draw.rect(self.screen, BLUE, self.algo_button)
        algo_btn_text = FONT.render("Cycle Algo", True, WHITE)
        self.screen.blit(
            algo_btn_text, (self.algo_button.x + 20, self.algo_button.y + 8)
        )

        # Draw thinking indicator if algorithm is thinking
        if self.algorithm_thinking:
            thinking_text = HEADER_FONT.render("Thinking...", True, RED)
            self.screen.blit(thinking_text, (500, 10))

        # Draw freecells
        for i in range(4):
            freecell_x = FREECELL_MARGIN + i * (CARD_WIDTH + CARD_MARGIN)
            freecell_y = HEADER_HEIGHT + CARD_MARGIN

            # Draw freecell placeholder
            pygame.draw.rect(
                self.screen,
                LIGHT_GRAY,
                (freecell_x, freecell_y, CARD_WIDTH, CARD_HEIGHT),
                2,
            )

            # Draw card if exists
            if self.freecells[i]:
                self.freecells[i].draw(self.screen, freecell_x, freecell_y)

        # Draw foundations
        for i, suit in enumerate(Suit):
            foundation_x = (
                SCREEN_WIDTH - FREECELL_MARGIN - (4 - i) * (CARD_WIDTH + CARD_MARGIN)
            )
            foundation_y = HEADER_HEIGHT + CARD_MARGIN

            # Draw foundation placeholder with suit
            pygame.draw.rect(
                self.screen,
                LIGHT_GRAY,
                (foundation_x, foundation_y, CARD_WIDTH, CARD_HEIGHT),
                2,
            )
            suit_text = pygame.font.SysFont("Arial", 40).render(
                suit.value, True, suit.color()
            )
            self.screen.blit(
                suit_text,
                (
                    foundation_x + CARD_WIDTH // 2 - suit_text.get_width() // 2,
                    foundation_y + CARD_HEIGHT // 2 - suit_text.get_height() // 2,
                ),
            )

            # Draw top card if exists
            if self.foundations[suit]:
                self.foundations[suit][-1].draw(self.screen, foundation_x, foundation_y)

        # Draw cascades
        for i, cascade in enumerate(self.cascades):
            cascade_x = CASCADE_MARGIN + i * (CARD_WIDTH + CARD_MARGIN)
            base_y = HEADER_HEIGHT + CARD_HEIGHT + 3 * CARD_MARGIN

            # Draw cascade placeholder
            pygame.draw.rect(
                self.screen, LIGHT_GRAY, (cascade_x, base_y, CARD_WIDTH, CARD_HEIGHT), 2
            )

            # Draw cards in cascade
            for j, card in enumerate(cascade):
                card_y = base_y + j * (CARD_HEIGHT // 3)
                card.draw(self.screen, cascade_x, card_y)

        # Draw game over message
        if self.is_game_won():
            # Draw semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))

            # Draw win message
            win_text = pygame.font.SysFont("Arial", 60).render("YOU WIN!", True, WHITE)
            self.screen.blit(
                win_text,
                (
                    SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - win_text.get_height() // 2,
                ),
            )

            stats_text = pygame.font.SysFont("Arial", 30).render(
                f"Time: {self.elapsed_time // 60:02d}:{self.elapsed_time % 60:02d} - Moves: {self.moves_count}",
                True,
                WHITE,
            )
            self.screen.blit(
                stats_text,
                (
                    SCREEN_WIDTH // 2 - stats_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 + win_text.get_height(),
                ),
            )

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    # ESC key stops algorithm
                    if event.key == pygame.K_ESCAPE:
                        self.algorithm_running = False
                    # Space key starts algorithm
                    elif event.key == pygame.K_SPACE and self.current_algorithm:
                        self.run_algorithm()
                    # H key gives a hint
                    elif event.key == pygame.K_h:
                        hint = self.get_hint()
                        if hint:
                            # Highlight the card to move
                            if hint.from_location == Location.FREECELL:
                                if self.freecells[hint.from_index]:
                                    self.freecells[hint.from_index].selected = True
                            elif hint.from_location == Location.CASCADE:
                                if self.cascades[hint.from_index]:
                                    self.cascades[hint.from_index][-1].selected = True

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if any button was clicked
                    if self.new_game_button.collidepoint(event.pos):
                        self.deal_cards()
                    elif self.hint_button.collidepoint(event.pos):
                        hint = self.get_hint()
                        if hint:
                            # Make the hint move
                            self.make_move(hint)
                    elif self.algo_button.collidepoint(event.pos):
                        self.cycle_algorithm()
                    else:
                        # Clear any selected card highlight
                        if self.selected_card:
                            self.selected_card.selected = False

                        # If already selected, try to move
                        if self.selected_card:
                            target_location, target_index = self.get_target_location(
                                event.pos
                            )
                            if target_location:
                                move = Move(
                                    self.selected_card,
                                    self.selected_location,
                                    self.selected_index,
                                    target_location,
                                    target_index,
                                )
                                if self.is_valid_move(
                                    move.card, move.to_location, move.to_index
                                ):
                                    self.make_move(move)

                            # Clear selection
                            self.selected_card = None
                            self.selected_location = None
                            self.selected_index = None
                        else:
                            # Try to select a card
                            card, location, index = self.get_card_at_pos(event.pos)
                            if card:
                                self.selected_card = card
                                self.selected_location = location
                                self.selected_index = index
                                card.selected = True

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


# AI Algorithm Interface
class FreeCellAlgorithm:
    def get_next_move(self, game: FreeCellGame) -> Optional[Move]:
        """
        Get the next move for the FreeCellGame
        """
        pass


# Sample Algorithms


class RandomAlgorithm(FreeCellAlgorithm):
    def get_next_move(self, game: FreeCellGame) -> Optional[Move]:
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        return random.choice(valid_moves)


class GreedyAlgorithm(FreeCellAlgorithm):
    def get_next_move(self, game: FreeCellGame) -> Optional[Move]:
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None

        # Prioritize moves by type:
        # 1. Move to foundation
        # 2. Make a build (move cards between cascades to build sequences)
        # 3. Move to freecell

        # Foundation moves
        for move in valid_moves:
            if move.to_location == Location.FOUNDATION:
                return move

        # Building moves (prefer moving to cascades)
        cascade_moves = [
            move for move in valid_moves if move.to_location == Location.CASCADE
        ]
        if cascade_moves:
            return random.choice(cascade_moves)

        # Last resort: move to freecell
        freecell_moves = [
            move for move in valid_moves if move.to_location == Location.FREECELL
        ]
        if freecell_moves:
            return random.choice(freecell_moves)

        # If all else fails, choose a random move
        return random.choice(valid_moves)


# Add your own algorithm classes here!

# Entry point
if __name__ == "__main__":
    game = FreeCellGame()
    game.run()
