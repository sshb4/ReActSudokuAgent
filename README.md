# ReAct Sudoku Agent

A Python command-line project for CS 4300. Development begins with contracts and black-box tests before implementation.

## Current status

Puzzle operations, classical propositional logic, typed request validation, controller policies, and the agent loop are implemented. Qwen 2.5 1.5B completed the three-empty-cell example in 18 model-selected tool requests, including fact/rule updates, three entailed queries, placements, and explicit validated submission, with no rejected requests. This verifies one near-complete puzzle, not general reliability on harder puzzles. See the [live reasoning trace](docs/evidence/model-run-kb-success.json) and [independent verification](docs/evidence/requirements-verification.json).

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

The suite currently passes 170 cases. [Final test output](docs/evidence/final-tests.txt) records the complete run; [initial output](docs/evidence/initial-tests.txt) preserves the pre-implementation import failures. [Runtime verification](docs/evidence/runtime-verification.json) and the [initial successful model/tool trace](docs/evidence/model-run-fixed.json) record a genuine local-model demonstration. Supplemental tests include an independent truth-table check of the KB and explicitly labeled white-box fault injection for solution validation. Unit tests of the adapter use a substituted HTTP transport; live traces are separate integration evidence.

## Run a local tool replay

No third-party packages are needed for replay mode:

```sh
python3 -m react_sudoku --puzzle examples/board.json --replay examples/replay.json --max-actions 11 --output /tmp/sudoku-result.json
```

This example inspects a board with three empty cells, adds and queries a fact/rule, places digits, undoes a placement, and explicitly submits the board. The result contains the validated final board, action counts, terminal reason, and full tool trace. The example succeeds on its eleventh and final allowed action. Omit `--output` to print the JSON result. Exit codes: 0 for success, 1 for another terminal outcome, 2 for input/output errors.

**Replay uses scripted requests, not a language model.** It demonstrates the controller and tool integration but does not satisfy the final model-driven demonstration requirement. The [saved example](docs/evidence/scripted-replay.json) is labeled `scripted_replay`.

## Run with a local model

Install [Ollama for macOS](https://docs.ollama.com/macos), start its local runtime, and install a local model appropriate for your computer. No model is bundled with this repository; the program does not automatically install or download one. Use the name shown by `ollama list`:

```sh
python3 -m react_sudoku --puzzle examples/board.json --model YOUR_INSTALLED_MODEL --timeout 60 --max-actions 100 --output /tmp/sudoku-model-result.json
```

On the development Mac, Ollama 0.40.6 is installed in `/Applications/Ollama.app`, and `qwen2.5:1.5b` is downloaded. To start the runtime with cloud features disabled in one terminal, then run the agent in another:

```sh
OLLAMA_NO_CLOUD=1 OLLAMA_CONTEXT_LENGTH=8192 /Applications/Ollama.app/Contents/Resources/ollama serve
```

```sh
python3 -m react_sudoku --puzzle examples/board.json --model qwen2.5:1.5b --timeout 60 --max-actions 24 --output /tmp/sudoku-model-result.json
```

The adapter sends the tool JSON schema to the local runtime's `format` parameter, following [Ollama structured-output documentation](https://docs.ollama.com/capabilities/structured-outputs). It talks only to `127.0.0.1:11434`, disables HTTP proxies, and refuses redirects. Use an installed local model. There are no API credentials or paid external services configured. The runtime uses a local HTTP interface; model inference can run on the same computer.

The 60-second timeout limits blocking socket operations; total run duration can be longer across multiple tool calls. Failed transport/envelopes produce a safe `model_error` event. Invalid generated requests consume an action and return a rejection observation. Every tool observation includes the explicit terminal reason. No automatic retries or unconstrained fallback occur. Model choice affects solving reliability.

Developer prompts guide inspection, fact/rule/query reasoning, and placement goals based only on prior accepted requests and observations. The model chooses all request arguments; the prompts quote its previously chosen literals to avoid transcription mistakes. The controller does not enforce this prompting workflow or assign Sudoku meanings to propositions. An entailed KB query is only relative to the model's asserted facts/rules, and independent board validation is still required. Failed prompt experiments remain labeled in `docs/evidence/` rather than being presented as successful runs.

## Required report and student review

- [Report PDF](output/pdf/react-sudoku-report.pdf)
- [Student code-review guide](docs/student-review.md)
- [Requirements audit](docs/requirements-audit.md)
- Public repository: https://github.com/sshb4/ReActSudokuAgent

The PDF includes the repository URL, component diagram, process description, and student-selected takeaway. It contains selectable text, semantic heading tags, logical structure order, and diagram alternative text. It is a review copy until student review is confirmed; no PDF/UA certification is claimed. The PDF itself is the file to submit through Canvas.

To rebuild the report (optional dependencies; not needed for the agent):

```sh
.venv/bin/python -m pip install -r requirements-report.txt
.venv/bin/python scripts/build_report.py
```

The report builder verifies the PDF structure/text and renders page images under the ignored `tmp/pdfs/` directory for visual review. Student review confirmation is recorded only after the student actually confirms review.
