# ReAct Sudoku Agent

A Python command-line project for CS 4300. Development begins with contracts and black-box tests before implementation.

## Current status

Specifications and initial black-box tests are written. No production components or model integration have been implemented.

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

At this test-first stage, pytest stops with five import errors because `react_sudoku` does not exist yet. These are expected collection errors, not passing tests or executed behavioral failures. The [initial run output](docs/evidence/initial-tests.txt) preserves that result. The test files contain 39 test functions, with parameterized cases, derived from the specification IDs in their names and docstrings.

System run instructions will follow implementation. Never commit credentials, environment files, or authenticated service URLs.
