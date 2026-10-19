# ReAct Sudoku Agent

A Python command-line project for CS 4300. Development begins with contracts and black-box tests before implementation.

## Current status

Puzzle operations, classical propositional logic, typed request validation, controller policies, and the runtime-independent agent loop are implemented. The model interface is defined; a real language-model runtime is still to be selected and integrated.

- [Architecture](docs/architecture.md)
- [Behavior contracts](docs/contracts.md)
- [Development plan and evidence](docs/development.md)

The assignment requires a language model to select tool calls. It does not require an external API. The model adapter will allow the eventual model runtime to be chosen separately. Scripted model responses will support repeatable tests, but do not demonstrate the required language-model behavior.

## Run the tests

Requires Python 3.11 or newer.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'pytest>=8,<10' 'jsonschema>=4,<5'
.venv/bin/python -m pytest -q
```

The suite currently passes 125 cases: 109 original specification-derived cases, seven supplemental review cases, and nine CLI cases. [Initial run output](docs/evidence/initial-tests.txt) preserves the pre-implementation import failures; [final verification](docs/evidence/current-tests.txt) records the passing suite. Supplemental tests include an independent truth-table check of the KB and explicitly labeled white-box fault injection for solution validation.

## Run a local tool replay

No third-party packages are needed for replay mode:

```sh
python3 -m react_sudoku --puzzle examples/board.json --replay examples/replay.json --max-actions 11 --output /tmp/sudoku-result.json
```

This example inspects a board with three empty cells, adds and queries a fact/rule, places digits, undoes a placement, and explicitly submits the board. The result contains the validated final board, action counts, terminal reason, and full tool trace. The example succeeds on its eleventh and final allowed action. Omit `--output` to print the JSON result. Exit codes: 0 for success, 1 for another terminal outcome, 2 for input/output errors.

**Replay uses scripted requests, not a language model.** It demonstrates the controller and tool integration but does not satisfy the final model-driven demonstration requirement. The [saved example](docs/evidence/scripted-replay.json) is labeled `scripted_replay`. The model protocol in `react_sudoku/model.py` is the boundary for the eventual runtime adapter; the CLI currently exposes only replay mode.

Outstanding work: integrate and verify an actual model runtime with constrained output and a finite timeout, record a model-driven run, complete student review, and create the accessible report with the repository URL and student takeaway.

Never commit credentials, environment files, or authenticated service URLs.
