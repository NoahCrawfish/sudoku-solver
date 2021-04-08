import tkinter as tk
from tkinter import font as tk_font
import random

import numpy as np


def can_place(y, x, value, board):
    """
    Tests by standard sudoku rules whether a given value can be placed on the board.

    An auxiliary function to the Solver.

    :param y: (type - int) Y coordinate 0-8 to be tested.
    :param x: (type - int) X coordinate 0-8 to be tested.
    :param value: (type - int) The value 1-9 to be tested.
    :param board: (type - numpy.array) A 9x9 grid. The sudoku board.
    :return: True or False.
    """

    for i in range(9):
        if board[y][i] == value:
            return False
        if board[i][x] == value:
            return False

    # dividing, flooring, and then multiplying by the same number, snaps the result to multiples of that number
    # i.e. these lines get the top right corner of the square that the coordinate falls in
    square_x = x // 3 * 3
    square_y = y // 3 * 3

    for i in range(3):
        for j in range(3):
            if board[square_y + j][square_x + i] == value:
                return False
    return True


class Solver:
    def __init__(self, master):
        self.master = master

        # the solution is accessed through the class hierarchy rather than being returned
        # this is because it acts as a "global" variable within the namespace
        # once a solution is found, all recursions can be immediately broken to save computation time
        self.solution = None

    def init_solve(self, board, drawing):
        """
        The setup function for the solving algorithm.

        :param board: (type - numpy.array) A 9x9 grid.
        :param drawing: (type - bool) Whether the solution will be drawn on the board or handled internally.
        :return: None.
        """

        self.solution = None
        self.solve(board)
        if drawing:
            self.master.main_canvas.draw_puzzle(self.solution, self.master.puzzle)

    def solve(self, board):
        """
        Solves the given sudoku board by recursive backtracking.

        The solution is called by other classes rather than returned. If the solver was to be used in any wider of a
        context, it would be best to return the solution.

        :param board: (type - numpy.array) 9x9 grid.
        :return: None.
        """

        # the board is copied within the function's namespace so that it is not shared by all recursions
        sudoku = board.copy()

        # works from top-left to bottom-right of the board
        for (y, x), n in np.ndenumerate(sudoku):
            if n == 0:
                numbers = list(range(1, 10))
                while numbers:
                    # number candidates for the cell are chosen in a random order
                    # which is critical to the logic of the generator algorithm
                    # this becomes apparent when looking at .unique()
                    num = numbers.pop(random.randrange(len(numbers)))

                    if self.solution is None:
                        # if placing the number doesn't violate sudoku rules, place it and call the next recursion
                        if can_place(y, x, num, sudoku):
                            sudoku[y][x] = num
                            self.solve(sudoku)
                    else:
                        # the exit if a solution is found in a deeper recursion
                        return

                # if no values are valid in the cell, backtrack to an earlier recursion
                # each recursion is "in charge" of one cell
                # the alternative is looping through cells in each recursion
                # which is tricky because if no values can be placed in a cell, that cell may be left unsolved
                return

        # the only path here is if every cell on the board is non-zero (solved)
        self.solution = sudoku

    def unique(self, board, depth):
        """
        Checks whether a given sudoku board has a unique (only one) solution.

        Because in .solve(), when looking at a cell, numbers are tested in a random order, multiple solutions can
        be found with the same board. This function leverages that fact, by solving the board a pre-determined
        number of times and comparing the solutions.

        :param board: (type - numpy.array) 9x9 grid.
        :param depth: (type - int) The number of solutions to be compared.
        :return: True or False.
        """

        # the solution to be compared against
        self.init_solve(board, False)
        first_solution = self.solution

        # The depth variable is how many boards are compared before the solution is determined to be unique.
        # Two boards are most likely to match if there are two solutions that only vary by a pair of numbers flipping.
        # In this case, the probability of a false positive is 1 out of 2^n, where n is the depth.

        # But a false positive is essentially irrelevant to the outcome of the generator unless it is on the last
        # recursion. This is because, in the next recursion, taking out any number will result in multiple solutions,
        # so the probability of a false positive reduces to 1 out of s^(n*x), where s is the number of solutions and
        # x>17. (A sudoku needs at minimum 17 clues to have a unique solution, hence the restriction on x.)
        # Best case scenario, s=2, n=2, x=17, evaluating to a 5.28 * 10^(-9) percent chance of a false positive.

        # Therefore, the effect of any false positives before the generator's final recursion on the result are trivial.
        # The only purpose of avoiding false positives before the final recursion is to avoid the extra computing time
        # of testing every cell in the next recursion (because they are all guaranteed to have multiple solutions).

        # The probability that the final recursion will give a false positive is  1 out of s^n, where s is the number of
        # solutions and n is the generator depth. In practice, removing a number from a unique solution usually results
        # in a few different solutions by the end of a generation. For the final recursion, a generator depth of 12 was
        # chosen. So, the odds of generating a non-unique sudoku are anywhere from 1/4096 - essentially 0, depending on
        # the number of solutions.

        # An interesting follow up project would be to measure the frequency of generations with 2, 3, 4, 5+ solutions
        # on the final recursion, in order to optimise the depth variable. The current value of 12 for the final
        # recursion is an educated guess, but could easily be overkill.

        for i in range(depth):
            self.init_solve(board, False)
            if np.any(self.solution-first_solution):
                return False
        return True


class Generator:
    """
    Generates a sudoku puzzle with a unique solution.

    The number of clues given is determined by the difficulty. A subtractive method is used to generate the puzzle.
    More info on the algorithm in .remove_numbers()
    """

    def __init__(self, master):
        self.master = master
        self.clues = 0

    def generate(self, difficulty):
        """
        Initializes the sudoku generation algorithm.

        Rather than returning a value, the result is drawn directly on MainCanvas.canvas through the class hierarchy.

        :param difficulty: (type - str.) Determines the possible range of clues.
        :return: None.
        """

        if difficulty == "easy":
            self.clues = random.randint(40, 50)
        if difficulty == "medium":
            self.clues = random.randint(32, 40)
        if difficulty == "hard":
            self.clues = random.randint(25, 32)

        # generate a random solved sudoku
        board = np.zeros((9, 9), int)
        self.master.solver.init_solve(board, False)
        board = self.master.solver.solution

        # remove the desired amount of numbers, such that the remaining board has a unique solution
        # more info in .remove_numbers()
        board = self.remove_numbers(board, [])

        self.master.puzzle = board
        self.master.main_canvas.draw_puzzle(board, board)

    def remove_numbers(self, board, excluded):
        """
        Removes numbers from the board until the desired amount of clues are left.

        A recursive backtracking algorithm. Values that have found to lead to multiple solutions are blacklisted by
        the excluded param. and are passed down to later recursions. Once the sudoku has the desired amount of clues,
        it is returned and passed back up.

        :param board: (type - numpy.array) A 9x9 grid.
        :param excluded: (type - list) Holds tuples of board coordinates.
        :return: (type - numpy.array) A 9x9 grid.
        """

        # parameters are copied within the function's namespace so that they are not shared by all recursions
        sudoku = board.copy()
        excluded_nums = excluded.copy()

        if np.count_nonzero(sudoku) > self.clues:
            # if this could be the final recursion before a board is generated, use a different (higher) depth value to
            # test whether the board has a unique solution
            # see the bottom of the code for the specific depth values
            # see Solver.unique() for an explanation of the role of the depth parameter
            depth = generator_depth[0]
            if np.count_nonzero(sudoku) == self.clues+1:
                depth = generator_depth[1]

            # gets a list of coordinates where empty spots are
            indices = np.array([np.nonzero(sudoku)[0], np.nonzero(sudoku)[1]])
            indices = indices.T
            indices = indices.tolist()

            while indices:
                # picks a random coordinate that was not blacklisted by earlier recursions
                y, x = indices.pop(random.randrange(len(indices)))
                while (y, x) in excluded_nums and indices:
                    y, x = indices.pop(random.randrange(len(indices)))

                # if there are no coordinates left, the function will break (backtracking to the earlier recursion)
                if indices:
                    n = sudoku[y][x]
                    sudoku[y][x] = 0
                    # if removing the value leads to a unique solution, call the next recursion
                    # and pass along the updated board/blacklist
                    if self.master.solver.unique(sudoku, depth):
                        next_layer = self.remove_numbers(sudoku, excluded_nums)
                        # pass the solution back up
                        if next_layer is not None:
                            return next_layer

                    # appends the coordinate the the blacklist, to be passed down to later recursions
                    excluded_nums.append((y, x))
                    if len(excluded_nums) > self.clues:
                        return
                    # fill the empty cell that was tested back in
                    sudoku[y][x] = n
        else:
            return sudoku


class DifficultyButton:
    def __init__(self, master, difficulty):
        self.master = master
        self.difficulty = difficulty
        self.button = tk.Button(master, text=difficulty.title(), font=button_font, width="12")
        self.button["command"] = self.pressed

    def pressed(self):
        self.master.on_delete()
        # The hierarchy goes up: DifficultyButton -> PopUpWindow -> Application
        # And then back down: Application -> Generator -> .generate()
        self.master.master.generator.generate(self.difficulty)


class PopUpWindow(tk.Toplevel):
    """
    A popup window to select the difficulty of generated sudoku.

    Inherits from tkinter.Toplevel.
    """

    def __init__(self, master):
        super().__init__()
        self.master = master
        self.wm_protocol("WM_DELETE_WINDOW", self.on_delete)

        self.easy_button = DifficultyButton(self, "easy")
        self.medium_button = DifficultyButton(self, "medium")
        self.hard_button = DifficultyButton(self, "hard")

        self.easy_button.button.pack(fill=tk.BOTH, expand=True)
        self.medium_button.button.pack(fill=tk.BOTH, expand=True)
        self.hard_button.button.pack(fill=tk.BOTH, expand=True)

    def on_delete(self):
        self.master.popup = None
        self.destroy()


class MainCanvas:
    """Updates the sudoku board on the tkinter canvas."""

    def __init__(self, master):
        # master is the parent Class
        self.master = master
        self.canvas = tk.Canvas(master, width=644, height=644, bg="white")

        self.canvas.update()
        self.width = self.canvas.winfo_reqwidth()
        self.height = self.canvas.winfo_reqheight()
        self.section_width = self.width/9
        self.section_height = self.height/9

        self.canvas.bind("<Button-1>", self.on_click)
        for i in range(1, 10):
            self.canvas.bind(str(i), self.enter_value)
        self.canvas.bind("<BackSpace>", self.enter_value)
        self.canvas.bind("<Key>", self.key_press)

        # board values (tkinter objects) are stored so that they may be deleted when refreshing
        self.board_text = []
        self.board_lines = []
        self.selected_position = []
        self.selection = None

        self.draw_board()

    def draw_board(self):
        """
        Draws the grid lines on the sudoku board.

        :return: None.
        """

        for line in self.board_lines:
            self.canvas.delete(line)
        for i in range(1, 9):
            self.board_lines.append(self.canvas.create_line(self.width/9*i, 0, self.width/9*i, self.height, width=1.5))
            self.board_lines.append(self.canvas.create_line(0, self.height/9*i, self.width, self.height/9*i, width=1.5))
        for i in range(1, 3):
            self.board_lines.append(self.canvas.create_line(self.width/3*i, 0, self.width/3*i, self.height, width=5))
            self.board_lines.append(self.canvas.create_line(0, self.height/3*i, self.width, self.height/3*i, width=5))
        self.board_lines.append(self.canvas.create_rectangle(0, 0, self.width, self.height, width=14))

    def on_click(self, event):
        """
        Toggles/updates the highlighted cell's position on the sudoku grid.

        Because of the layering, when the highlight is updated, the grid lines are redrawn on top of it.

        :param event: (type - tkinter.Event) Passes information about the mouse click.
        :return: None.
        """

        if self.selected_position == [int(event.x//self.section_width), int(event.y//self.section_height)]:
            self.canvas.delete(self.selection)
            self.selected_position = []
        elif self.master.popup is None:
            self.selected_position = [int(event.x//self.section_width), int(event.y//self.section_height)]
            self.draw_selected()
            self.draw_board()
            self.draw_puzzle(self.master.puzzle, self.master.puzzle)
            self.canvas.focus_set()

    def draw_selected(self):
        """
        Highlight the selected cell of the sudoku grid.

        :return: None.
        """

        if self.selection:
            self.canvas.delete(self.selection)
        self.selection = self.canvas.create_rectangle(self.selected_position[0] * self.section_width,
                                                      self.selected_position[1] * self.section_height,
                                                      (self.selected_position[0] + 1) * self.section_width,
                                                      (self.selected_position[1] + 1) * self.section_height,
                                                      fill="#cfcfcf")

    def enter_value(self, event):
        """
        Updates the internal puzzle array when a digit is inputted and calls for the numbers to be redrawn.

        :param event: (type - tkinter.Event) Passes information about the key pressed.
        :return: None.
        """

        if self.selected_position:
            if event.keysym == "BackSpace":
                self.master.puzzle[self.selected_position[1], self.selected_position[0]] = 0
            else:
                self.master.puzzle[self.selected_position[1], self.selected_position[0]] = int(event.char)
            self.draw_puzzle(self.master.puzzle, self.master.puzzle)

    def key_press(self, event):
        """
        Keyboard navigation of the sudoku board.

        :param event: (type - tkinter.Event) Passes information about the key pressed.
        :return: None.
        """

        if event.keysym == "Return":
            self.master.solve_button.pressed()
        if event.keysym == "Delete":
            self.master.clear_button.pressed()
        elif self.selected_position:
            if event.keysym == "Left" and self.selected_position[0] > 0:
                self.selected_position[0] -= 1
            if event.keysym == "Right" and self.selected_position[0] < 8:
                self.selected_position[0] += 1
            if event.keysym == "Up" and self.selected_position[1] > 0:
                self.selected_position[1] -= 1
            if event.keysym == "Down" and self.selected_position[1] < 8:
                self.selected_position[1] += 1
            self.draw_selected()
            self.draw_board()
            self.draw_puzzle(self.master.puzzle, self.master.puzzle)

    def draw_puzzle(self, current_board, previous_board):
        """
        Refreshes the numbers on the canvas.

        The difference between the current board and the old board is drawn in red. Values that they have in common
        are drawn in black.

        :param current_board: (type - numpy.array) A 9x9 grid.
        :param previous_board: (type - numpy.array) A 9x9 grid.
        :return: None.
        """

        if current_board is None:
            current_board = previous_board
        board_colors = current_board-previous_board
        for text in self.board_text:
            self.canvas.delete(text)
        for (y, x), n in np.ndenumerate(current_board):
            if n > 0:
                if board_colors[y][x] != 0:
                    text = self.canvas.create_text(self.section_width*(x+0.5), self.section_height*(y+0.5), text=n,
                                                   font=board_font_solved, fill="red")
                else:
                    text = self.canvas.create_text(self.section_width*(x+0.5), self.section_height*(y+0.5), text=n,
                                                   font=board_font, fill="black")
                self.board_text.append(text)


class SolveButton:
    def __init__(self, master):
        self.master = master
        self.button = tk.Button(master.taskbar, text="Solve", height=2, font=button_font)
        self.button["command"] = self.pressed

    def pressed(self):
        if self.master.popup is None:
            self.master.main_canvas.canvas.delete(self.master.main_canvas.selection)
            self.master.main_canvas.selected_position = []
            self.master.solver.init_solve(self.master.puzzle, True)


class ClearButton:
    def __init__(self, master):
        self.master = master
        self.button = tk.Button(master.taskbar, text="Clear", height=2, font=button_font)
        self.button["command"] = self.pressed

    def pressed(self):
        if self.master.popup is None:
            self.master.puzzle = np.zeros((9, 9), int)
            self.master.main_canvas.canvas.delete(self.master.main_canvas.selection)
            self.master.main_canvas.selected_position = []
            self.master.main_canvas.draw_puzzle(self.master.puzzle, self.master.puzzle)


class GenerateButton:
    def __init__(self, master):
        self.master = master
        self.button = tk.Button(master.taskbar, text="Generate", font=button_font)
        self.button["command"] = self.pressed

    def pressed(self):
        self.master.create_popup()


class Application(tk.Frame):
    """
    The parent of the GUI hierarchy.

    Initializes classes, packs their tkinter objects, and handles the popup window.
    Inherits from tkinter.Frame.
    """

    def __init__(self, master):
        super().__init__(master)
        self.root = master
        self.puzzle = np.zeros((9, 9), int)
        self.solver = Solver(self)
        self.generator = Generator(self)
        self.taskbar = tk.Frame(master)
        self.solve_button = SolveButton(self)
        self.clear_button = ClearButton(self)
        self.generate_button = GenerateButton(self)
        self.main_canvas = MainCanvas(self)
        self.popup = None

        self.pack()
        self.main_canvas.canvas.pack()
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.solve_button.button.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.clear_button.button.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.generate_button.button.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def create_popup(self):
        if self.popup is None:
            self.popup = PopUpWindow(self)
            self.main_canvas.canvas.delete(self.main_canvas.selection)
            self.main_canvas.selected_position = []


# see the wall of text in Solver.unique() for an explanation
generator_depth = (5, 12)

main_root = tk.Tk()
main_root.title("Sudoku Solver")

button_font = tk_font.Font(size=20)
board_font = tk_font.Font(size=25)
board_font_solved = tk_font.Font(size=25, slant="italic")

main_app = Application(main_root)
main_app.mainloop()
