# ReAct Sudoku Agent

A Python command-line project for CS 4300. Development begins with contracts and black-box tests before implementation.

## Current status

Puzzle operations, classical propositional logic, typed request validation, controller policies, and the agent loop are implemented. A local Ollama adapter and CLI mode are implemented and unit-tested. An installed runtime and local model are still needed to verify actual schema-constrained generation and record a model-driven run.

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

The suite currently passes 154 cases, including local adapter and model-mode CLI tests. [Initial run output](docs/evidence/initial-tests.txt) preserves the pre-implementation import failures; [current verification](docs/evidence/local-adapter-tests.txt) records the passing suite. Supplemental tests include an independent truth-table check of the KB and explicitly labeled white-box fault injection for solution validation. Adapter tests replace the HTTP transport; they do not prove a real runtime supports the full tool schema.

## Run a local tool replay

No third-party packages are needed for replay mode:

```sh
python3 -m react_sudoku --puzzle examples/board.json --replay examples/replay.json --max-actions 11 --output /tmp/sudoku-result.json
```

This example inspects a board with three empty cells, adds and queries a fact/rule, places digits, undoes a placement, and explicitly submits the board. The result contains the validated final board, action counts, terminal reason, and full tool trace. The example succeeds on its eleventh and final allowed action. Omit `--output` to print the JSON result. Exit codes: 0 for success, 1 for another terminal outcome, 2 for input/output errors.

**Replay uses scripted requests, not a language model.** It demonstrates the controller and tool integration but does not satisfy the final model-driven demonstration requirement. The [saved example](docs/evidence/scripted-replay.json) is labeled `scripted_replay`.

## Run with a local model (runtime verification pending)

Install [Ollama for macOS](https://docs.ollama.com/macos), start its local runtime, and install a local model appropriate for your computer. No model is bundled with this repository; the program does not automatically install or download one. Use the name shown by `ollama list`:

```sh
python3 -m react_sudoku --puzzle examples/board.json --model YOUR_INSTALLED_MODEL --timeout 60 --max-actions 100 --output /tmp/sudoku-model-result.json
```

The adapter sends the tool JSON schema to the local runtime's `format` parameter, following [Ollama structured-output documentation](https://docs.ollama.com/capabilities/structured-outputs). It talks only to `127.0.0.1:11434`, disables HTTP proxies, and refuses redirects. Use an installed local model. There are no API credentials or paid external services configured. The runtime uses a local HTTP interface; model inference can run on the same computer.

The 60-second timeout limits blocking socket operations; total run duration can be longer across multiple tool calls. Failed transport/envelopes produce a safe `model_error` event. Invalid generated requests consume an action and return a rejection observation. No automatic retries or unconstrained fallback occur. Model choice affects solving reliability. Neither successful integration nor a genuine model solution is claimed until a real run verifies it.

Outstanding work: install/select a local runtime and model, verify the full schema, record a model-driven run, complete student review, and create the accessible report with the repository URL and student takeaway.

Never commit credentials, environment files, or authenticated service URLs.
