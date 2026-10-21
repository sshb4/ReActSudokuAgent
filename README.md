# ReAct Sudoku Agent

A Python command-line project for CS 4300. Development begins with contracts and black-box tests before implementation.

## Current status

Puzzle operations, classical propositional logic, typed request validation, controller policies, and the agent loop are implemented. Qwen 2.5 1.5B completed the three-empty-cell example in 18 model-selected tool requests, including fact/rule updates, three entailed queries, placements, and explicit validated submission, with no rejected requests. This verifies one near-complete puzzle, not general reliability on harder puzzles. See the [live reasoning trace](docs/evidence/model-run-kb-success.json) and [independent verification](docs/evidence/requirements-verification.json).

- [Architecture](docs/architecture.md)
- [Behavior contracts](docs/contracts.md)
- [Development plan and evidence](docs/development.md)


## Report files

- [report.md](report/report.md): the editable report, including a Mermaid component diagram.


