# Assignment requirements audit

Checked October 20, 2026 against the supplied assignment, current source, tests, Git history, and saved traces. This is a coding-agent audit, not a student-review record or an instructor grade.

## Overall result

Update after gap fixes: all 170 tests pass; observations now include explicit terminal reasons; a genuine model run uses facts/rules/queries and completes in 18 actions. A tagged, visually checked report PDF is prepared at `output/pdf/react-sudoku-report.pdf` and includes the student's selected takeaway. The repository is confirmed public. Student code-review confirmation and publication of the final changes are still pending. The mapping below preserves the original audit findings for process evidence.

## Rubric mapping

| Criterion | Evidence | Assessment |
| --- | --- | --- |
| Architecture and specifications | `docs/architecture.md`, `docs/contracts.md`; initial spec commit `de4e68f` precedes test and implementation commits | Substantially satisfied. Initial module/interface/state/interaction contracts exist. Latest observation revision remains uncommitted. The report diagram must agree with the final implementation. |
| ReAct agent and tool integration | `agent.py`, `ollama_model.py`, `controller.py`; real-model trace `docs/evidence/model-run-fixed.json` | Implemented. Model selects schema-constrained requests, receives observations, and cannot directly establish success. Real run solved the example in eight actions. |
| Sudoku, logic, controller policies | Public puzzle/KB/controller interfaces and tests; scripted replay exercises every required tool | Implemented, with one observation-level gap: terminal reasons exist in final results, but tool observations omit the explicit `terminal_reason` field requested by the Sensors description. Add that field and a contract-derived test. |
| Specification-derived testing | Original tests committed in `5b3962a` before core implementation `cdb749e`; later CLI/adapter tests similarly precede their implementations; supplemental checks are labeled | Complete suite: **162 passed in 0.21 seconds** during this audit. Latest runtime regression tests and fixes remain uncommitted. Preserve the honest revision record; do not retroactively claim separate commits for those edits. |
| Coding-agent development process | Significant agent-written implementation, specifications, tests, process log, initial failures, revisions | Agent contribution and verification are documented. The student's own review/responsibility must still be completed and accurately recorded. Chat approvals alone are not evidence of detailed code review. |
| Repository and report | Code/docs/tests/run instructions exist; configured remote is `https://github.com/sshb4/ReActSudokuAgent` | Incomplete. No PDF exists. Commit/push final changes and verify instructor access; this audit did not check remote availability or permissions. |

## Model demonstration limits

The genuine successful model run starts with three empty cells and uses inspection, placement, and submission. It does not use the KB or undo. Tests and scripted replay demonstrate those tools, but a model-driven example that uses a propositional query to support a placement would better support the stated Reliable reasoning measure. Do not present scripted tool choices as model choices.

The assignment does not specify a minimum number of empty cells, puzzle difficulty, success rate, or graphical interface. A harder puzzle would provide additional evidence, but the explicit missing deliverables and the observation gap take priority.

## Required PDF

Prepared in the report review copy (final student review still pending):

- Repository URL, with instructor access confirmed.
- Final project-structure/component-interaction diagram.
- Brief, accurate development-process description, including actual revisions.
- One student-selected takeaway identifying a process change to keep.
- Selectable text, semantic headings, logical reading order, and accessible diagram labeling or alternative text.

The assignment requires submitting **one PDF through Canvas**, not just uploading code. Due October 22, 2026 at 9:30 a.m. MDT.

## Secret check

No tracked `.env`, `.pem`, or `.key` files were found. A targeted scan of project source, tests, docs, and examples found no obvious private-key blocks or long OpenAI-style secret-key strings. This is a limited pattern check, not a guarantee that every possible secret format is absent. The runtime's account/config/model files are stored outside the project and must stay outside the submission.

## Recommended completion order

1. Specify/test/add explicit terminal reasons to tool observations.
2. Strengthen model-driven KB/query evidence where feasible without replacing model-selected actions with a script.
3. Walk through the code with the student and record actual review and the student's chosen takeaway.
4. Commit/push the final project and verify instructor access.
5. Produce and accessibility-check the required PDF, then submit it through Canvas.
