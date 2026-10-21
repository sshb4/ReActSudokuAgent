# Development plan and process record

## Required sequence

1. Write architecture and behavior contracts before implementation.
2. Derive public-behavior tests from contract IDs before writing the corresponding function bodies. Preserve the failing-test result where feasible.
3. Implement components against their contracts and tests.
4. Review changes, run checks, and record mismatches. Revise contracts or implementation explicitly and explain why.
5. Run the complete suite, exercise a real language-model/tool loop, and retain an inspectable run trace.
6. Complete run instructions and the accessible PDF report, with a diagram matching the implemented structure.

Use separate Git commits for specifications, tests, implementation, and consequential revisions to make ordering reviewable. Do not invent retrospective test-first or student-review claims.

## Test plan derived from contracts

| Area | Planned black-box examples | Contracts |
| --- | --- | --- |
| Puzzle input | Shapes, boolean/digit boundaries, duplicate clues, input isolation | P01–P02 |
| Inspection | Each scope, coordinate order, candidates, detached results | P02–P03 |
| Placement and undo | Legal placement, all conflict types, occupied/given protection, multiple undos, empty history | P04–P05 |
| Validation | Incomplete board, valid solved board, preserved clues | P06 |
| Logic | Facts, chained rules, contraposition, negated queries, unknown atoms, inconsistent update rollback | K01–K04 |
| KB boundaries | Duplicate statements, atom/statement limits, board/KB independence | K03–K06 |
| Requests | Missing/extra fields, booleans, invalid coordinates, unknown tools, free text, multiple requests | T01–T02, A02 |
| Controller | Count accepted/rejected actions, last-action success, last-action placement, terminal immutability | C01–C05 |
| Trace and loop | Ordered observations return to model, copied trace, immediate stop, runtime exception | C06–C07, A01–A04 |

## Milestones

1. Specifications and student design review.
2. Puzzle, KB, and schema tests; implementation follows those tests.
3. Controller and loop tests; implementation follows those tests.
4. Choose and verify the model runtime, implement its adapter, and record a demonstration.
5. Final review, instructions, complete test run, and report.

## Open decisions

- The model runtime and its finite request timeout. An external API is not required by this design.
- The repository URL to include in the submission.
- The student's final process takeaway, based on the actual development experience.

## Process record

### 2026-10-19 — Initial planning

The student supplied the assignment. The coding agent read it and inspected the empty repository. After discussion, the design leaves the model runtime undecided instead of assuming an external API. The coding agent drafted the architecture, behavior contracts, and test plan before implementation. Student design review, tests, implementation, and execution evidence are still pending.

### 2026-10-19 — Contracts clarified and tests written

Before writing tests, the coding agent identified unspecified Python return formats, exact error codes, snapshot fields, and model message structure. These details were added as I01–I05 and committed with the initial specifications in `de4e68f`. The student authorized continuing; this does not establish that a detailed student design or code review has occurred.

The coding agent then wrote 39 black-box test functions with parameterized cases across puzzle, KB, schemas, controller, and agent loop. No production function bodies existed to examine. Tests invoke only the specified public interfaces; the scripted model in the tests supplies requests without solving puzzles or inspecting internal state.

A project virtual environment was created with pytest 9.1.1 and jsonschema 4.26.0 under Python 3.14.7. All test source files parsed successfully. The first `.venv/bin/python -m pytest -q` run exited with code 2 and five collection errors because the production package does not exist. [Exact initial output](evidence/initial-tests.txt) is retained. No behavioral tests have executed or passed yet. Implementation and subsequent verification remain pending.

### 2026-10-19 — Core implementation and verification

Following the test commit `5b3962a`, the coding agent implemented the puzzle, JSON tool schema/parser, classical propositional KB with DPLL satisfiability, controller, model protocol, and agent loop. The architecture was clarified to show puzzle/KB dependencies on shared schema/result helpers before those modules were written.

The first implementation run revealed an existing test collection bug: `request` is a reserved pytest parameter name. Renaming it allowed 109 cases to run; 107 passed, and two failed because the `one_empty` fixture mutated the same `solved` object used for expected results. The fixture now copies the board first. Assertions and behavior contracts were not weakened. All 109 original cases then passed.

The coding agent reviewed the implementation against the contracts and added seven explicitly supplemental checks after implementation: public KB behavior against an independent eight-world truth-table oracle across 480 proposed updates, five white-box corrupted-board cases, and isolation from model-adapter mutation. The complete 116-case suite passes; [verification output](evidence/core-tests.txt) is retained. This is coding-agent verification, not a claim of completed student code review. A real model adapter, CLI, model demonstration, report, and student review remain outstanding.

### 2026-10-19 — CLI replay

After committing the core in `cdb749e`, the coding agent specified L01–L02 and wrote nine CLI cases before the CLI/replay bodies. The [pre-implementation run](evidence/cli-before-implementation.txt) failed at import as expected, and the contracts/tests were committed in `8d9c630`. The CLI and replay adapter were then implemented, and all 125 cases passed. The provided replay exercises inspection, KB facts/rules/query, placement, undo, and explicit submission; it succeeds on the last of 11 actions. [Current verification](evidence/current-tests.txt) and a [labeled scripted trace](evidence/scripted-replay.json) are retained. This trace demonstrates tools, not language-model solving.

Next: choose and verify an actual model runtime, implement schema-constrained selection with a finite timeout, record a model-driven run, perform student code review, and prepare the accessible PDF. No real-model completion or student review is claimed yet.

### 2026-10-19 — Local model adapter candidate

The coding agent found no `ollama`, `llama-server`, `lmstudio`, or `lms` executable in PATH, and no Ollama or LM Studio application in `/Applications`. This does not rule out a runtime installed elsewhere. No model or runtime was downloaded. The agent consulted official Ollama structured-output and chat-endpoint documentation, then specified M01–M04 and wrote adapter tests before implementation (commit `8cead18`). The pre-implementation adapter run failed at import as retained in [the initial result](evidence/adapter-before-implementation.txt). Model-mode CLI tests were also written and committed before changing the CLI (`0838e12`); their initial run had five expected failures and one pass because that CLI mode was absent.

The adapter was then implemented using standard-library HTTP/JSON, schema-constrained output, a configurable finite socket timeout, strict JSON parsing, safe error handling, and no automatic retry. It connects to a fixed loopback endpoint and does not configure credentials. All 154 cases pass; [verification](evidence/local-adapter-tests.txt) is retained. Adapter tests substitute the HTTP boundary. A real Ollama instance has not yet verified schema support or selected a move; the candidate integration must not be described as a demonstrated model solution.

Outstanding: install/select a local runtime/model, run real schema-constrained inference, record a validated model-driven session, obtain student review, and finish the accessible report. The model download requires a separate setup decision because none was present and model size depends on the computer.

## Submission checklist

### 2026-10-20 — Fixes from real-model testing

The user approved installing a local runtime/model on October 19. Ollama 0.40.6 and `qwen2.5:1.5b` were installed. The small model was chosen given 16 GB of memory and approximately 4.3 GiB free disk before installation. Cloud features were disabled when starting the runtime.

The first real run ([trace](evidence/model-run-initial.json)) reached its 20-action limit with repeated attempts to modify clues. The controller rejected those attempts without changing the puzzle. Runtime logs also identified an unsupported lookahead in the literal schema. Before editing the implementation, the coding agent specified explicit empty-cell labels and wrote eight regression cases; three initially failed because labels and compatible regex anchors had not been implemented.

On October 20, after the user's request to finish these fixes, board inspection was updated to label empty-cell coordinates and report the existing locally legal candidates. The prompt now explains those observations and clarifies that rejected placements must not be undone. The schema uses a runtime-supported anchored pattern with a separate final-newline exclusion; the controller's stricter literal validator was preserved. All 162 cases passed (`.venv/bin/python -m pytest -q --tb=short`, 0.20 seconds).

The installed runtime was restarted and the CLI rerun against the actual model. Qwen inspected the board, placed three forced digits, and explicitly submitted in eight actions, with no rejected requests. [Actual trace](evidence/model-run-fixed.json) and [independent verification](evidence/runtime-verification.json) are retained. A separate check compared all original clues and every row/column/box to digits 1–9. No schema warning was observed. This is a successful model-driven demonstration on a near-complete board; it does not establish hard-puzzle reliability or model use of KB/undo tools.

Changes remain uncommitted at the user's preference to run tests without a prior commit. The test-first edits and initial failing results occurred before implementation, but they are not represented by separate Git commits. Student code review and the accessible PDF remain outstanding.

## Remaining submission items

### 2026-10-20 — Requirements-gap fixes and report preparation

An audit against the supplied rubric found explicit terminal reasons missing from tool observations (although final results already had them), incomplete student review, no report PDF, and no published main branch. The terminal observation contract was updated and four black-box cases failed before the implementation fix. After adding the field, running, success, budget-limit, and model-error/terminal-session observations all passed.

The original successful local-model run did not use the KB. Subsequent real prompt experiments were retained honestly: a long prompt led to unnecessary undos; a shorter prompt repeated facts; goal reminders alone still repeated steps; consolidated runtime instructions progressed through facts/rules/queries but exposed dropped negations. Prompts now quote exact model-selected literals/conclusions and distinguish a new conclusion atom from the accepted premise. Goal reminders use only accepted tool observations, never choose coordinates or digits, and execute no tools. Tests were written for goal progression, rejection/unresolved-query handling, preservation of chosen literals, and message consolidation before the respective changes. The complete suite passes 170 cases; `docs/evidence/final-tests.txt` retains the result. A 16-action reasoning run filled every cell but correctly ended at the budget limit without submission; it is not labeled successful.

The repository was checked through GitHub and is public at `https://github.com/sshb4/ReActSudokuAgent`; its remote main branch was empty before publication. No existing branch is being overwritten. A concrete student review guide was prepared and the student said they would review it. Review completion is not inferred from that message. The student explicitly selected the takeaway "Decide what each function should do before coding it."

A two-page report was generated with selectable text, tagged H1/H2/P structure, page reading-order mappings, language metadata, and a Figure tag containing alternative text. Both pages were rendered and visually inspected. The generator retains a visible review-copy label until the student confirms code review. Artifact-only dependencies are isolated in `requirements-report.txt`; the agent itself remains standard-library-only. No PDF/UA certification is claimed.

The final 24-action-budget run (`docs/evidence/model-run-kb-success.json`) succeeded in 18 actions with zero rejections. All requests were selected by the local model; the trace includes three model-chosen fact/rule/query sequences and their entailed results before placements. A separate verification preserved every original clue and checked each row, column, and box. KB names remain uninterpreted assertions; entailment is not a certificate that the model's chosen names accurately describe board truth. The run verifies the tool workflow and independent board correctness, not general or difficult-puzzle reliability. The report records this limitation.

- Complete repository, specifications, tests, code, and reproducible run instructions.
- Evidence of specification/test/implementation order and honest review/revision notes.
- Complete passing test suite and a language-model demonstration trace.
- PDF with repository URL, accurate architecture diagram, process description, and one specific student takeaway.
- PDF accessibility: selectable text, semantic headings, logical reading order, and accessible diagram labeling or alternative text. Verify these properties in the final artifact.
- No credentials, `.env` files, or authenticated service URLs.
- Due October 22, 2026, at 9:30 a.m. MDT.
