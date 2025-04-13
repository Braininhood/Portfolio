import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):
        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = [[False for _ in range(width)] for _ in range(height)]

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """Prints a text-based representation of where mines are located."""
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                print("|X" if self.board[i][j] else "| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        return self.board[cell[0]][cell[1]]

    def nearby_mines(self, cell):
        """Returns the number of mines that are within one row and column of a given cell."""
        count = 0
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                if (i, j) != cell and 0 <= i < self.height and 0 <= j < self.width and self.board[i][j]:
                    count += 1
        return count

    def won(self):
        """Checks if all mines have been flagged."""
        return self.mines_found == self.mines


class Sentence():
    """Logical statement about a Minesweeper game"""

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """Returns the set of all cells known to be mines."""
        if len(self.cells) == self.count:
            return set(self.cells)
        return set()

    def known_safes(self):
        """Returns the set of all cells known to be safe."""
        if self.count == 0:
            return set(self.cells)
        return set()

    def mark_mine(self, cell):
        """Removes a cell known to be a mine and decrements count."""
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """Removes a cell known to be safe."""
        if cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI():
    """Minesweeper game player"""

    def __init__(self, height=8, width=8):
        self.height = height
        self.width = width
        self.moves_made = set()
        self.mines = set()
        self.safes = set()
        self.knowledge = []

    def mark_mine(self, cell):
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """Updates knowledge base with new information."""
        self.moves_made.add(cell)
        self.mark_safe(cell)

        # Determine surrounding cells
        neighbors = set()
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                if (i, j) != cell and 0 <= i < self.height and 0 <= j < self.width:
                    if (i, j) in self.mines:
                        count -= 1
                    elif (i, j) not in self.safes:
                        neighbors.add((i, j))

        if neighbors:
            self.knowledge.append(Sentence(neighbors, count))

        self.update_knowledge()

    def update_knowledge(self):
        """Infers new information from the knowledge base."""
        updated = True
        while updated:
            updated = False
            new_mines, new_safes = set(), set()

            for sentence in self.knowledge:
                new_mines.update(sentence.known_mines())
                new_safes.update(sentence.known_safes())

            if new_mines or new_safes:
                updated = True
                for cell in new_mines:
                    self.mark_mine(cell)
                for cell in new_safes:
                    self.mark_safe(cell)

            inferred_sentences = []
            for s1 in self.knowledge:
                for s2 in self.knowledge:
                    if s1 != s2 and s1.cells.issubset(s2.cells):
                        inferred = Sentence(s2.cells - s1.cells, s2.count - s1.count)
                        if inferred not in self.knowledge and inferred not in inferred_sentences:
                            inferred_sentences.append(inferred)
                            updated = True
            self.knowledge.extend(inferred_sentences)
            self.knowledge = [s for s in self.knowledge if s.cells]

    def make_safe_move(self):
        """Returns a known safe move not already made."""
        for move in self.safes:
            if move not in self.moves_made:
                return move
        return None

    def make_random_move(self):
        """Returns a random move that has not been made and is not known to be a mine."""
        choices = [(i, j) for i in range(self.height) for j in range(self.width)
                   if (i, j) not in self.moves_made and (i, j) not in self.mines]
        return random.choice(choices) if choices else None
