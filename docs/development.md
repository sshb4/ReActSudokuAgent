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

## Submission checklist

- Complete repository, specifications, tests, code, and reproducible run instructions.
- Evidence of specification/test/implementation order and honest review/revision notes.
- Complete passing test suite and a language-model demonstration trace.
- PDF with repository URL, accurate architecture diagram, process description, and one specific student takeaway.
- PDF accessibility: selectable text, semantic headings, logical reading order, and accessible diagram labeling or alternative text. Verify these properties in the final artifact.
- No credentials, `.env` files, or authenticated service URLs.
- Due October 22, 2026, at 9:30 a.m. MDT.
