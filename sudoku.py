import tkinter as tk
from tkinter import font as tk_font
import random

import numpy as np


# Tests by standard sudoku rules whether a given value can be placed on the board.
def can_place(y: int, x: int, value: int, board: "np.ndarray") -> bool:
    # check row an column
    for i in range(9):
        if board[y][i] == value:
            return False
        if board[i][x] == value:
            return False

    # check 3x3 square
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
        self.solution = None

    def init_solve(self, board: "np.ndarray", drawing: bool):
        self.solution = None
        self.solve(board)
        if drawing:
            self.master.main_canvas.draw_puzzle(self.solution, self.master.puzzle)

    # solve via recursive backtracking
    def solve(self, board: "np.ndarray"):
        sudoku = board.copy()

        for (y, x), n in np.ndenumerate(sudoku):
            if n == 0:
                numbers = list(range(1, 10))
                while numbers:
                    # use random to allow different solutions if multiple solutions exist
                    num = numbers.pop(random.randrange(len(numbers)))

                    if self.solution is None:
                        if can_place(y, x, num, sudoku):
                            sudoku[y][x] = num
                            self.solve(sudoku)
                    else:
                        # return to top level once a solution is found
                        return

                # backtracking
                return

        # only reachable once every cell on the board is non-zero (solved)
        self.solution = sudoku

    # checks whether a given sudoku board has a unique solution.
    # can generate false positives, but is very unlikely at the proper depth
    def unique(self, board: "np.ndarray", depth: int) -> bool:
        # the solution to be compared against
        self.init_solve(board, False)
        first_solution = self.solution

        # generate depth # of solutions and assume the sudoku is unique if all solutions match
        for i in range(depth):
            self.init_solve(board, False)
            if np.any(self.solution-first_solution):
                return False

        return True


class Generator:
    def __init__(self, master):
        self.master = master
        self.clues = 0

    def generate(self, difficulty: str):
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
        board = self.remove_numbers(board)

        self.master.puzzle = board
        self.master.main_canvas.draw_puzzle(board, board)

    def remove_numbers(self, board: "np.ndarray", excluded: list = None):
        """
        Removes numbers from the board until the desired amount of clues are left.

        A recursive backtracking algorithm. Values that have found to lead to multiple solutions are blacklisted by
        the excluded param. and are passed down to later recursions. Once the sudoku has the desired amount of clues,
        it is returned and passed back up.
        """

        sudoku = board.copy()
        if excluded is None:
            excluded_nums = []
        else:
            excluded_nums = excluded.copy()

        if np.count_nonzero(sudoku) > self.clues:
            # if only one more number needs to be removed, use a higher depth value so the .unique() verification
            # function is less likely to return a false positive
            if np.count_nonzero(sudoku) == self.clues+1:
                depth = generator_depth[1]
            else:
                depth = generator_depth[0]

            # gets a list of coordinates where empty spots are
            indices = np.array([np.nonzero(sudoku)[0], np.nonzero(sudoku)[1]])
            indices = indices.T.tolist()

            while indices:
                # picks a random coordinate that was not blacklisted by earlier recursions
                y, x = indices.pop(random.randrange(len(indices)))
                while (y, x) in excluded_nums and indices:
                    y, x = indices.pop(random.randrange(len(indices)))

                if indices:
                    n = sudoku[y][x]
                    sudoku[y][x] = 0

                    if self.master.solver.unique(sudoku, depth):
                        next_layer = self.remove_numbers(sudoku, excluded_nums)
                        # pass the solution back up
                        if next_layer is not None:
                            return next_layer

                    excluded_nums.append((y, x))
                    if len(excluded_nums) > self.clues:
                        return

                    # fill the empty cell that was tested back in
                    sudoku[y][x] = n
        else:
            return sudoku


class DifficultyButton:
    def __init__(self, master, difficulty: str):
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

    # draw the grid lines on the sudoku board
    def draw_board(self):
        for line in self.board_lines:
            self.canvas.delete(line)
        for i in range(1, 9):
            self.board_lines.append(self.canvas.create_line(self.width/9*i, 0, self.width/9*i, self.height, width=1.5))
            self.board_lines.append(self.canvas.create_line(0, self.height/9*i, self.width, self.height/9*i, width=1.5))
        for i in range(1, 3):
            self.board_lines.append(self.canvas.create_line(self.width/3*i, 0, self.width/3*i, self.height, width=5))
            self.board_lines.append(self.canvas.create_line(0, self.height/3*i, self.width, self.height/3*i, width=5))
        self.board_lines.append(self.canvas.create_rectangle(0, 0, self.width, self.height, width=14))

    # toggles/updates the highlighted cell's position on the sudoku grid
    def on_click(self, event):
        # deselect if already selected
        if self.selected_position == [int(event.x//self.section_width), int(event.y//self.section_height)]:
            self.canvas.delete(self.selection)
            self.selected_position = []
        elif self.master.popup is None:
            self.selected_position = [int(event.x//self.section_width), int(event.y//self.section_height)]
            self.draw_selected()
            self.canvas.focus_set()

    def draw_selected(self):
        if self.selection:
            self.canvas.delete(self.selection)
        self.selection = self.canvas.create_rectangle(
            self.selected_position[0] * self.section_width,
            self.selected_position[1] * self.section_height,
            (self.selected_position[0] + 1) * self.section_width,
            (self.selected_position[1] + 1) * self.section_height,
            fill="#cfcfcf"
        )

        # redraw board elements (lines and numbers) over selection square
        self.draw_board()
        self.draw_puzzle(self.master.puzzle, self.master.puzzle)

    def enter_value(self, event):
        if self.selected_position:
            if event.keysym == "BackSpace":
                self.master.puzzle[self.selected_position[1], self.selected_position[0]] = 0
            else:
                self.master.puzzle[self.selected_position[1], self.selected_position[0]] = int(event.char)
            # redraw numbers on the board
            self.draw_puzzle(self.master.puzzle, self.master.puzzle)

    # keyboard navigation of the sudoku board
    def key_press(self, event):
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

    # refreshes the numbers on the canvas
    def draw_puzzle(self, current_board, previous_board):
        if current_board is None:
            current_board = previous_board
        board_colors = current_board-previous_board

        for text in self.board_text:
            self.canvas.delete(text)

        # different values between current and previous board are drawn in red, same values are drawn in black
        for (y, x), n in np.ndenumerate(current_board):
            if n > 0:
                fill = "red" if board_colors[y][x] != 0 else "black"
                text = self.canvas.create_text(
                    self.section_width*(x+0.5),
                    self.section_height*(y+0.5),
                    text=n,
                    font=board_font_solved,
                    fill=fill
                )
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


generator_depth = (5, 12)

main_root = tk.Tk()
main_root.title("Sudoku Solver")

button_font = tk_font.Font(size=20)
board_font = tk_font.Font(size=25)
board_font_solved = tk_font.Font(size=25, slant="italic")

main_app = Application(main_root)
main_app.mainloop()
