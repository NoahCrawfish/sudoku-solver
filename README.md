# Sudoku Solver / Generator

A **Python** application built with **tkinter** that can solve user-entered Sudoku puzzles and generate new puzzles guaranteed to have a unique solution.

## Implementation Details

- **Solving Algorithm**
  - Fills the grid via recursive backtracking
  - Ensures each row, column, and 3×3 box satisfies Sudoku constraints

- **Puzzle Generation**
  - Initialized by running the solver on an empty grid
  - Incrementally removes numbers while:
    - Re-running the solver to verify uniqueness
    - Rejecting removals that introduce multiple solutions

## Controls

- Navigate: *Arrow Keys*
- Delete Cell: *Backspace*
- Clear Board: *Delete*
- Solve: *Enter*

## Demo

https://user-images.githubusercontent.com/82133480/156081822-d87b9139-5f9e-4a6a-b478-4d1ba3d856df.mov

## Setup

> pip install numpy
