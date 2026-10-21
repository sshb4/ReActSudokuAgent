# Student code review guide

Status: prepared for student review; completion is not yet claimed.

## What the program does

The model chooses one JSON tool request at a time. Python checks that request, executes an allowed operation, and sends the result back. The model does not receive Python objects it can edit. A model saying "solved" cannot establish success: only `submit` followed by independent Sudoku validation can do that.

## Files to review

1. [puzzle.py](../react_sudoku/puzzle.py): input is a nine-by-nine list; zero is empty. Original clues are saved separately. A placement must target an empty non-clue cell and avoid row, column, and box duplicates. Undo removes the latest accepted placement. Rejected operations do not enter the undo stack.
2. [knowledge.py](../react_sudoku/knowledge.py): facts and implication rules are stored as propositional clauses. Updates are checked for consistency before being saved. A query checks whether the literal must be true, must be false, or is unresolved across possible truth assignments. Logical consistency alone does not prove that a claim about the board is true.
3. [schemas.py](../react_sudoku/schemas.py): exactly seven tool names and their required argument fields are accepted. Extra fields, malformed literals, and invalid types/coordinates are rejected. The same advertised tool schema constrains model generation.
4. [controller.py](../react_sudoku/controller.py): owns the puzzle, KB, action count, trace, and terminal status. Every attempted tool request consumes one action. A correct submission on the final action succeeds; filling the board without submitting on that action ends at the limit. Every observation now includes an explicit terminal reason.
5. [agent.py](../react_sudoku/agent.py) and [ollama_model.py](../react_sudoku/ollama_model.py): ask the local model for one schema-constrained request, record the controller's observation, and repeat while running. Transport errors produce a safe model-failure result. Observation-based developer reminders guide initial fact, rule, and query goals; they choose no coordinates, digits, names, or tool arguments and execute no requests themselves.
6. [tests](../tests/) and [development log](development.md): public-behavior tests were written from contracts before main implementation. Supplemental truth-table and fault-injection checks are labeled honestly. Read the actual model traces separately from scripted replay.

## Changes to review from testing

- Board observations label empty-cell coordinates and legal candidates, because the first small-model run repeatedly targeted a clue.
- The literal regex was rewritten for the runtime's schema converter while preserving strict controller validation.
- Terminal reasons were added directly to observations, closing the assignment audit's sensor gap.
- Real-model KB use is evaluated through an actual model trace, not claimed from the scripted test model.

## What an honest review should confirm

Read the files above, compare the important behavior with `docs/contracts.md`, and inspect the passing test result and actual run trace. Note any part you do not understand or any change you want. Student review is complete only after the student actually does this and confirms it; the coding agent cannot perform that responsibility on the student's behalf.

## Student-selected takeaway

The student selected: "Decide what each function should do before coding it."

Report wording: "I plan to decide and write down what each function should do before coding it, so I have a clear contract to implement and test."
