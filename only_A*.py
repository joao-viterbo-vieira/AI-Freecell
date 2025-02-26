import pygame
import random
import sys
import time
from collections import deque
import heapq

# Initialize pygame
pygame.init()

# Constants
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_MARGIN = 10
ANIMATION_SPEED = 10

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
RED = (220, 0, 0)
BLUE = (0, 0, 220)
GRAY = (200, 200, 200)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCel Solver")

# Font
font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 16)


# Card class
class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.color = RED if suit in ["H", "D"] else BLACK

    def __str__(self):
        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks.get(self.rank, str(self.rank))
        return f"{rank_str}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is None:
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))

    def draw(self, x, y):
        # Draw card background
        pygame.draw.rect(screen, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
        pygame.draw.rect(screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)

        # Draw card value
        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks.get(self.rank, str(self.rank))
        suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}

        # Draw rank and suit at top-left
        rank_text = small_font.render(rank_str, True, self.color)
        suit_text = small_font.render(suit_symbols[self.suit], True, self.color)
        screen.blit(rank_text, (x + 5, y + 5))
        screen.blit(suit_text, (x + 5, y + 25))

        # Draw large suit in the middle
        big_suit = font.render(suit_symbols[self.suit], True, self.color)
        screen.blit(big_suit, (x + CARD_WIDTH // 2 - 10, y + CARD_HEIGHT // 2 - 15))

        # Draw rank and suit at bottom-right (inverted)
        screen.blit(rank_text, (x + CARD_WIDTH - 20, y + CARD_HEIGHT - 30))
        screen.blit(suit_text, (x + CARD_WIDTH - 20, y + CARD_HEIGHT - 50))


# Game state class
class FreeCellGame:
    def __init__(self, initial_state=None):
        # Cascades (8 columns)
        self.cascades = [[] for _ in range(8)]
        # Free cells (4 individual cells)
        self.free_cells = [None] * 4
        # Foundations (4 piles, one for each suit)
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        self.moves = []

        # If no initial state is provided, create a new game
        if initial_state is None:
            self.new_game()
        else:
            # Copy the provided state
            for i in range(8):
                self.cascades[i] = initial_state.cascades[i].copy()
            self.free_cells = initial_state.free_cells.copy()
            for suit in self.foundations:
                self.foundations[suit] = initial_state.foundations[suit].copy()

    def new_game(self):
        # Create a deck of cards
        suits = ["H", "D", "C", "S"]
        ranks = list(range(1, 14))  # 1 (Ace) to 13 (King)

        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)

        # Deal cards to the cascades
        for i, card in enumerate(deck):
            cascade_idx = i % 8
            self.cascades[cascade_idx].append(card)

    def is_solved(self):
        # Check if all foundations have 13 cards each
        for suit in self.foundations:
            if len(self.foundations[suit]) != 13:
                return False
        return True

    def can_move_to_foundation(self, card):
        if card is None:
            return False

        foundation = self.foundations[card.suit]

        # If foundation is empty, we can only place an Ace
        if not foundation:
            return card.rank == 1

        # Otherwise, the card must be one rank higher than the top card
        return card.rank == foundation[-1].rank + 1

    def can_move_to_cascade(self, card, cascade_idx):
        if card is None:
            return False

        cascade = self.cascades[cascade_idx]

        # If cascade is empty, any card can be placed
        if not cascade:
            return True

        # Otherwise, the card must be one rank lower and different color
        top_card = cascade[-1]
        return card.rank == top_card.rank - 1 and (
            (card.color == RED and top_card.color == BLACK)
            or (card.color == BLACK and top_card.color == RED)
        )

    def get_valid_moves(self):
        valid_moves = []

        # Check all possible source cards (from cascades and free cells)
        for source_type in ["cascade", "free_cell"]:
            if source_type == "cascade":
                sources = [
                    (i, card)
                    for i, cascade in enumerate(self.cascades)
                    for j, card in enumerate(cascade)
                    if j == len(cascade) - 1
                ]
            else:  # free_cell
                sources = [
                    (i, card)
                    for i, card in enumerate(self.free_cells)
                    if card is not None
                ]

            for source_idx, card in sources:
                # Check if card can be moved to a foundation
                if self.can_move_to_foundation(card):
                    valid_moves.append(
                        ("foundation", source_type, source_idx, card.suit)
                    )

                # Check if card can be moved to a free cell
                if source_type == "cascade":  # Can only move from cascade to free cell
                    for i, cell in enumerate(self.free_cells):
                        if cell is None:
                            valid_moves.append(
                                ("free_cell", source_type, source_idx, i)
                            )
                            break  # Only need one free cell

                # Check if card can be moved to another cascade
                for i, cascade in enumerate(self.cascades):
                    if (
                        source_type != "cascade" or i != source_idx
                    ) and self.can_move_to_cascade(card, i):
                        valid_moves.append(("cascade", source_type, source_idx, i))

        return valid_moves

    def make_move(self, move):
        move_type, source_type, source_idx, dest = move

        # Get the card from the source
        if source_type == "cascade":
            card = self.cascades[source_idx].pop()
        else:  # free_cell
            card = self.free_cells[source_idx]
            self.free_cells[source_idx] = None

        # Place the card in the destination
        if move_type == "foundation":
            self.foundations[dest].append(card)
        elif move_type == "free_cell":
            self.free_cells[dest] = card
        else:  # cascade
            self.cascades[dest].append(card)

        # Record the move
        self.moves.append(move)

    def heuristic(self):
        """
        A heuristic function to estimate how close the game is to being solved.
        Lower scores are better.
        """
        score = 0

        # Score for cards in foundations (prefer more cards in foundations)
        for suit in self.foundations:
            score -= len(self.foundations[suit]) * 10

        # Score for cards in free cells (prefer fewer cards in free cells)
        for cell in self.free_cells:
            if cell is not None:
                score += 5

        # Score for cards in cascades (prefer ordered cards)
        for cascade in self.cascades:
            for i in range(len(cascade) - 1):
                card = cascade[i]
                next_card = cascade[i + 1]

                # Penalty for unordered cards
                if not (
                    card.rank == next_card.rank + 1
                    and (
                        (card.color == RED and next_card.color == BLACK)
                        or (card.color == BLACK and next_card.color == RED)
                    )
                ):
                    score += 1

        return score

    def __lt__(self, other):
        # Required for heapq
        return self.heuristic() < other.heuristic()

    def __eq__(self, other):
        # Compare all components of the game state
        if not isinstance(other, FreeCellGame):
            return False

        return (
            self.cascades == other.cascades
            and self.free_cells == other.free_cells
            and self.foundations == other.foundations
        )

    def __hash__(self):
        # Hash for state comparison (needed for visited set)
        cascades_tuple = tuple(tuple(col) for col in self.cascades)
        free_cells_tuple = tuple(self.free_cells)
        foundations_tuple = tuple(
            (suit, tuple(self.foundations[suit]))
            for suit in sorted(self.foundations.keys())
        )

        return hash((cascades_tuple, free_cells_tuple, foundations_tuple))

    def draw(self, highlight_move=None):
        screen.fill(GREEN)

        # Draw title
        title = font.render("FreeCel Solver", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - 80, 10))

        # Draw free cells
        for i, card in enumerate(self.free_cells):
            x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            y = 50
            pygame.draw.rect(screen, GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT))
            pygame.draw.rect(screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)
            if card:
                card.draw(x, y)

        # Draw foundations
        for i, suit in enumerate(["H", "D", "C", "S"]):
            x = SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
            y = 50
            pygame.draw.rect(screen, GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT))
            pygame.draw.rect(screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)

            if self.foundations[suit]:
                self.foundations[suit][-1].draw(x, y)
            else:
                # Draw suit symbol
                suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
                suit_color = RED if suit in ["H", "D"] else BLACK
                suit_text = font.render(suit_symbols[suit], True, suit_color)
                screen.blit(
                    suit_text, (x + CARD_WIDTH // 2 - 10, y + CARD_HEIGHT // 2 - 15)
                )

        # Draw cascades
        for i, cascade in enumerate(self.cascades):
            x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            y = 200

            # Draw cascade outline
            pygame.draw.rect(screen, GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)

            # Draw cards in cascade
            for j, card in enumerate(cascade):
                card_y = y + j * 30  # Overlap cards
                card.draw(x, card_y)

        # Highlight move if provided
        if highlight_move:
            move_type, source_type, source_idx, dest = highlight_move

            # Highlight source
            if source_type == "cascade":
                source_x = 50 + source_idx * (CARD_WIDTH + CARD_MARGIN)
                source_y = 200 + (len(self.cascades[source_idx]) - 1) * 30
            else:  # free_cell
                source_x = 50 + source_idx * (CARD_WIDTH + CARD_MARGIN)
                source_y = 50

            # Highlight destination
            if move_type == "foundation":
                suit_to_idx = {"H": 0, "D": 1, "C": 2, "S": 3}
                dest_x = (
                    SCREEN_WIDTH
                    - 50
                    - CARD_WIDTH
                    - suit_to_idx[dest] * (CARD_WIDTH + CARD_MARGIN)
                )
                dest_y = 50
            elif move_type == "free_cell":
                dest_x = 50 + dest * (CARD_WIDTH + CARD_MARGIN)
                dest_y = 50
            else:  # cascade
                dest_x = 50 + dest * (CARD_WIDTH + CARD_MARGIN)
                dest_y = 200 + len(self.cascades[dest]) * 30

            # Draw highlight rectangles
            pygame.draw.rect(
                screen, BLUE, (source_x, source_y, CARD_WIDTH, CARD_HEIGHT), 3
            )
            pygame.draw.rect(screen, BLUE, (dest_x, dest_y, CARD_WIDTH, CARD_HEIGHT), 3)

            # Draw arrow between source and destination
            pygame.draw.line(
                screen,
                BLUE,
                (source_x + CARD_WIDTH // 2, source_y + CARD_HEIGHT // 2),
                (dest_x + CARD_WIDTH // 2, dest_y + CARD_HEIGHT // 2),
                3,
            )

        # Draw solve button
        pygame.draw.rect(
            screen, BLUE, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 60, 200, 40)
        )
        solve_text = font.render("Solve Game", True, WHITE)
        screen.blit(solve_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 50))

        # Draw new game button
        pygame.draw.rect(
            screen, RED, (SCREEN_WIDTH // 2 - 320, SCREEN_HEIGHT - 60, 200, 40)
        )
        new_game_text = font.render("New Game", True, WHITE)
        screen.blit(new_game_text, (SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT - 50))

        # Draw step forward button
        pygame.draw.rect(
            screen, BLUE, (SCREEN_WIDTH // 2 + 120, SCREEN_HEIGHT - 60, 200, 40)
        )
        step_text = font.render("Step Forward", True, WHITE)
        screen.blit(step_text, (SCREEN_WIDTH // 2 + 140, SCREEN_HEIGHT - 50))

        pygame.display.flip()


# Solver using A* search
def solve_freecell(game):
    # Priority queue for A* search
    queue = [(game.heuristic(), id(game), game, [])]
    heapq.heapify(queue)

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 10000
    states_explored = 0

    while queue and states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        states_explored += 1

        # Check if the game is solved
        if current_game.is_solved():
            return moves

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        for move in valid_moves:
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the queue
            new_moves = moves + [move]
            heapq.heappush(
                queue,
                (
                    new_game.heuristic() + len(new_moves),
                    id(new_game),
                    new_game,
                    new_moves,
                ),
            )
            visited.add(new_hash)

    return None  # No solution found within constraints


# Main game loop
def main():
    game = FreeCellGame()
    solution = None
    solution_index = 0
    solving = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = pygame.mouse.get_pos()

                # Check if solve button was clicked
                if (
                    SCREEN_WIDTH // 2 - 100 <= x <= SCREEN_WIDTH // 2 + 100
                    and SCREEN_HEIGHT - 60 <= y <= SCREEN_HEIGHT - 20
                ):
                    print("Solving...")
                    solving = True
                    solution = solve_freecell(game)
                    solution_index = 0
                    if solution:
                        print(f"Solution found with {len(solution)} moves!")
                    else:
                        print("No solution found within the constraints.")
                        solving = False

                # Check if new game button was clicked
                if (
                    SCREEN_WIDTH // 2 - 320 <= x <= SCREEN_WIDTH // 2 - 120
                    and SCREEN_HEIGHT - 60 <= y <= SCREEN_HEIGHT - 20
                ):
                    game = FreeCellGame()
                    solution = None
                    solution_index = 0
                    solving = False

                # Check if step forward button was clicked
                if (
                    SCREEN_WIDTH // 2 + 120 <= x <= SCREEN_WIDTH // 2 + 320
                    and SCREEN_HEIGHT - 60 <= y <= SCREEN_HEIGHT - 20
                ):
                    if solution and solution_index < len(solution):
                        move = solution[solution_index]
                        game.make_move(move)
                        solution_index += 1

        # Draw the game
        if solving and solution and solution_index < len(solution):
            game.draw(highlight_move=solution[solution_index])
            pygame.display.flip()
            time.sleep(0.5)  # Pause to show the move
            game.make_move(solution[solution_index])
            solution_index += 1
            if solution_index >= len(solution):
                solving = False
        else:
            game.draw()

        pygame.time.Clock().tick(30)


if __name__ == "__main__":
    main()
