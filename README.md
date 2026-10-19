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

The suite currently passes 116 cases: the original 39 test functions with parameterized cases (109 cases), plus seven supplemental review cases. [Initial run output](docs/evidence/initial-tests.txt) preserves the pre-implementation import failures; [core verification](docs/evidence/core-tests.txt) records the passing suite. Supplemental tests include an independent truth-table check of the KB and explicitly labeled white-box fault injection for solution validation.

System run instructions will follow implementation. Never commit credentials, environment files, or authenticated service URLs.
