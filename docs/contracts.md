# Public behavior contracts

Status: initial contracts, written before function bodies or tests. Contract IDs connect specifications to later tests.

## Python interface and result format

**I01:** import modules from the `react_sudoku` package. Component methods and `parse_request` return dictionaries with `ok` (boolean), `code` (string), and `data` (dictionary). Successful calls use code `ok`. A successful parse places the normalized request under `data.request`; failed parses return an error result instead of raising. Raw requests are Python dictionaries, not JSON strings. The model adapter is responsible for decoding runtime output.

**I02:** inspection data contains `values` and `givens`: matching nine-by-nine lists for board scope, matching flat lists for row/column/box, and scalar integer/boolean values for cell scope. Cell data additionally contains `candidates`. Placement and undo success data contains `row`, `col`, and `digit` (the placed or removed digit). Validation uses `ok` to indicate a valid solution. KB updates return `data.changed`; queries return `data.result` as `entailed`, `contradicted`, or `unresolved`.

**I03:** error codes are `invalid_request`, `unknown_tool`, `invalid_coordinates`, `invalid_digit`, `invalid_scope`, `given_cell`, `occupied_cell`, `sudoku_conflict`, `empty_undo`, `invalid_literal`, `invalid_rule`, `inconsistent_kb`, `kb_limit`, `incomplete_board`, `invalid_solution`, `session_terminal`, and `model_error`. Missing or extra request fields and incorrect field types use `invalid_request`; an integer coordinate outside 1–9 uses `invalid_coordinates`. Direct puzzle calls also reject booleans/types without mutation using `invalid_coordinates` or `invalid_digit` as appropriate.

**I04:** controller snapshots and final run results have `board`, `givens`, `status`, `terminal_reason`, `actions_used`, `actions_remaining`, `trace`, and `events`. A running session has null terminal reason. Terminal reasons are `solution_accepted`, `action_limit`, and `model_error`. Trace entries contain `action`, `request`, and `observation`. Model failure events contain `code=model_error` and a safe reason, without runtime secrets. Controller observations add action counts and status to the I01 result format. The public `fail_model()` method records a generic model failure and terminates a running session; the loop does not serialize exception text, which could contain secrets.

**I05:** messages passed to `Model.next_request(messages, tool_schemas)` are JSON-compatible dictionaries using `role` and `content`; content is a string. Instructions use role `developer`, requests use `assistant`, and observations use `tool`. Request and observation content uses JSON encoding. `TOOL_SCHEMAS` is a JSON Schema accepting exactly one T01 request, including its tool-specific argument shape. The loop passes detached messages and schemas to the model so mutation by the adapter cannot alter controller-owned state.

## Puzzle representation and operations

- **P01 — Input:** a board is nine lists of nine integers. Zero means empty; 1–9 are digits. Reject booleans, invalid shapes, other values, and duplicate nonzero digits in any row, column, or box. Construction copies its input. Unique solvability is an input assumption, not something the constructor proves.
- **P02 — Coordinates:** all public coordinates are 1-based. Rows and columns are 1–9. Boxes are numbered 1–9 from left to right, top to bottom.
- **P03 — Inspection:** `inspect` returns a board, cell, row, column, or box, including which cells are original clues. Row/column/box values appear in ascending board-coordinate order. A cell result also lists digits locally legal in that cell, in ascending order; a filled cell has no candidates. Returned data is detached from internal state.
- **P04 — Placement:** accept a digit only in an empty non-given cell when it introduces no row, column, or box duplicate. A locally legal move need not lead to a solution. Reject replacing any occupied cell, including placement of its existing value. A rejection changes neither board nor undo stack.
- **P05 — Undo:** undo the most recent accepted placement and make that cell empty. Inspection, KB operations, rejected placements, and submissions do not enter the placement stack. Reject an empty undo stack without mutation. Undo never changes clues or KB contents.
- **P06 — Submission validation:** independently compare the current board to the original clues and check that every row, column, and box contains exactly digits 1–9. A full board alone is insufficient. Do not rely on earlier placement results to establish validity.

## Knowledge-base syntax and semantics

- **K01 — Literals:** a literal is an ASCII atom matching `[A-Za-z][A-Za-z0-9_]{0,63}`, optionally prefixed with `~` for negation. Names are case-sensitive. No whitespace, arbitrary expressions, executable code, or implicit Sudoku meaning is allowed.
- **K02 — Statements:** facts are literals. Rules have a nonempty list of at most nine premise literals and one conclusion literal. A rule means the classical propositional implication `(premise_1 AND ... AND premise_n) -> conclusion`. Negation is classical negation. Example: `['A', '~B'] -> C`.
- **K03 — Updates:** accept a fact or rule only if the resulting KB is satisfiable. Stage the update, check consistency, and commit atomically. Reject inconsistent or malformed updates without mutation. Repeating an identical statement succeeds with `changed=false`. Premise order and repeated premises do not distinguish rules.
- **K04 — Queries:** for query literal L, return `entailed` when KB AND NOT L is unsatisfiable; `contradicted` when KB AND L is unsatisfiable; otherwise return `unresolved`. A consistent KB cannot return both entailed and contradicted. Querying an unknown atom is unresolved. Implication uses classical semantics, including reasoning by contraposition; forward chaining alone is insufficient.
- **K05 — Resource bounds:** store at most 64 distinct atoms and 256 distinct statements. Reject updates exceeding these limits without mutation. Queries do not add atoms or statements. The limits constrain KB size; they do not promise constant-time satisfiability checks.
- **K06 — Board relationship:** the KB stores model-supplied propositions independently of the board. Logical consistency does not certify a Sudoku placement. No board change automatically creates or retracts a fact. Prompts must advise using versioned proposition names for claims about mutable board states. Submission always validates the board itself.

## Typed tool request schemas

**T01:** requests are objects with exactly `tool` and `arguments`. Arguments are objects with exactly the fields specified below; reject unknown fields. Integers exclude booleans. There are no implicit coercions or defaults except those explicitly stated. The implementation will expose corresponding JSON Schemas to the model.

| Tool | Arguments |
| --- | --- |
| `inspect` | `scope`: one of `board`, `cell`, `row`, `column`, `box`; `cell` additionally requires `row` and `col`; `row` requires `row`; `column` requires `col`; `box` requires `box`; `board` accepts no additional fields. Coordinates are integers 1–9. |
| `place` | `row`, `col`, `digit`: integers 1–9 |
| `undo` | Empty object |
| `add_fact` | `literal`: literal string under K01 |
| `add_rule` | `premises`: array of 1–9 literal strings; `conclusion`: literal string |
| `query` | `literal`: literal string under K01 |
| `submit` | Empty object; validates the application-owned board |

**T02:** every observation contains `ok`, `code`, `data`, `actions_used`, `actions_remaining`, and `status`. Status is `running`, `success`, `action_limit`, or `model_error`. Data contains the operation-specific result or a human-readable rejection reason. Error codes distinguish malformed requests, unknown tools, invalid coordinates, clue/occupied-cell protection, Sudoku conflicts, empty undo, inconsistent KB, KB limits, incomplete/invalid submission, terminal sessions, and model failures.

## Controller policies and ordered terminal checks

- **C01 — Initial state:** require a valid puzzle and positive integer action limit, excluding booleans. Start with an empty KB and trace, zero actions used, and `running` status. A solved input still requires explicit submission.
- **C02 — Action accounting:** every request received during a running session consumes one action, including inspections, queries, malformed requests, and rejected submissions. A model invocation failure consumes no tool action. Budgets never become negative.
- **C03 — Atomic rejection:** an invalid request cannot modify board, clues, undo stack, or KB. The action counter and trace still record the attempt. Schema validation precedes operation dispatch.
- **C04 — Check order:** (1) if already terminal, return `session_terminal` without executing, counting, or adding a trace entry; (2) consume one action for a running request; (3) validate and execute or reject the request; (4) if an explicit submission passes P06, set `success`; (5) otherwise, if no actions remain, set `action_limit`; (6) otherwise remain `running`; (7) produce and record the final observation. A successful submission on the last action succeeds. Filling the last cell on the last action terminates at the action limit because no submission occurred.
- **C05 — Failed submission:** report incomplete or invalid board, then continue if budget remains. Submission does not change the board or undo stack.
- **C06 — Trace:** record each counted request and resulting observation in order with a 1-based action number. Record malformed model text as an attempted request without executing it. Never record credentials or runtime authentication configuration. Public trace reads are copies.
- **C07 — Other termination:** a model exception or runtime failure stops the loop with `model_error` and an explicit reason, preserving prior board/KB state and tool trace. Record the failure separately as a run event. A structurally invalid model response is a rejected, counted request, not a transport failure. There are no automatic retries or additional tools outside the action budget. Configure a finite model-call timeout when selecting the runtime.

## Agent loop

- **A01 — Sequence:** provide developer-constructed instructions, tool schemas, initial budget, and history. The model obtains board state through inspection observations. Ask for one tool request, pass it to `Controller.step`, append the request and observation to model history, and repeat only while running.
- **A02 — Response constraints:** the model adapter requests schema-constrained output. Accept exactly one tool request per response. Reject free text, zero requests, multiple requests, and schema violations as one malformed attempt, with no tool execution. Model prose cannot mutate state or establish success.
- **A03 — Test model:** a scripted implementation of the model interface supplies predetermined requests for deterministic integration tests. It tests orchestration but does not replace the language model in the final demonstration.
- **A04 — Final result:** return application status, explicit terminal reason, final board, action counts, trace, and run events. Stop asking the model for actions immediately after termination.

## CLI replay interface

**L01:** `python -m react_sudoku --puzzle BOARD.json --replay REQUESTS.json --max-actions N [--output RESULT.json]` loads a board and a JSON array of scripted requests. The default budget is 200. The replay adapter implements `Model.next_request` by returning the next scripted item, without modifying it. Exhaustion raises a model failure handled by C07. Replay is a diagnostic demonstration, not a language model or evidence of model solving ability.

**L02:** `cli.main(argv)` returns 0 on validated success, 1 on any other terminal outcome, and 2 on invalid arguments, unreadable inputs, invalid JSON/board, or unwritable output. Successful invocation writes the final JSON result to standard output, or to `--output` when supplied. Results include `mode=scripted_replay`. Input/output failures print a concise message to standard error without stack traces or input contents. Arguments are parsed with standard CLI help behavior. Input reads complete before the optional output file is written. A result is never submitted to an external service by replay mode.

## Local model adapter

**M01:** `OllamaModel(model, timeout=60)` in `ollama_model.py` implements the model protocol. A model name must be a nonempty string without whitespace. Timeout must be a positive finite int or float, excluding booleans. Invalid configuration raises `ValueError`. The endpoint is fixed to `http://127.0.0.1:11434/api/chat`. No account, token, proxy, remote endpoint, or download is configured by this adapter. Redirects are refused. The separately installed Ollama runtime must use an installed local model.

**M02:** each `next_request` sends exactly one non-streaming POST with `model`, translated `messages`, `format` containing the supplied JSON schema, `stream=false`, and `options.temperature=0`. Developer messages become system messages; observations with role `tool` become user messages prefixed `Tool observation: `, since these are schema-constrained request objects rather than Ollama native function calls. Assistant messages remain assistant messages. Include the schema as text in an additional system instruction. Do not mutate the caller's messages/schema. Pass the configured timeout to the HTTP transport; this bounds blocking socket operations, not total process execution time.

**M03:** read at most 1 MiB of response bytes. A valid transport response is a JSON object with `done=true` and a `message.content` string. Parse that content as exactly one JSON value, rejecting duplicate object keys and non-finite numeric constants. Return the decoded value unchanged for controller validation. A malformed content string is returned as a malformed raw response so it consumes one rejected action. A malformed/incomplete transport envelope, oversized response, HTTP error, or timeout raises a generic `RuntimeError` without response text or exception details; C07 handles it. Never automatically retry or fall back to unconstrained generation.

**M04:** the CLI accepts exactly one of `--replay FILE` or `--model NAME`. Model mode uses `OllamaModel`, accepts `--timeout SECONDS` (default 60), and labels results `mode=local_model` with the configured `model` name. Invalid model configuration returns 2. Missing/stopped runtime becomes `model_error` and returns 1 with a safe run event. This implementation is a candidate integration until a real runtime verifies that the full schema is supported and a genuine model run is retained.

Protocol sources consulted before implementation: [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs) and [chat endpoint](https://docs.ollama.com/api/chat).
