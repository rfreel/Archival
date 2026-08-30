# Agentic Flywheel Template

A small, dependency-free starting point for evidence-backed agentic work.

It provides one executable entrypoint, `fw`, with:

- append-only, hash-linked JSONL event history;
- deterministic task replay and dependency-aware ready work;
- explicit agent claims;
- test receipts before task completion;
- machine-readable JSON output and exit codes.

The event log is canonical. Files under `.flywheel/` other than
`events.jsonl` are rebuildable projections. Beads is optional coordination
state: if a real `br` executable is available, let `br init` create `.beads/`.
Never hand-author Beads storage or treat a task description as authorization.

## Quick start

```bash
./fw init --root . --json
./fw agent register agent-one --root . --json
./fw task create --id first-slice \
  --title "Implement the first slice" \
  --acceptance "The first slice is verified" \
  --scope src/first_slice.py \
  --actor agent-one --root . --json
./fw task ready --root . --json
./fw task claim first-slice --actor agent-one --root . --json
./fw receipt test first-slice --actor agent-one \
  --command "python -m unittest discover -v" \
  --status PASS --evidence tests/ --root . --json
./fw task complete first-slice --actor agent-one \
  --reason "Implemented and verified the first slice" --root . --json
./fw cycle --root . --json
```

`--json` may appear anywhere in a command. `PASS`, `FAIL`, `UNKNOWN`, and
`NOT_DONE` map to exit codes `0`, `1`, `2`, and `3` respectively.

## Operating loop

```text
plan → create tasks → inspect ready work → claim → implement → test receipt
     → complete with evidence → inspect the next frontier
```

Keep each task bounded by acceptance criteria, dependencies, and file scope.
A task cannot be completed from a message that merely says “done”; it needs a
passing test receipt from the claiming agent.

## Optional Beads handoff

This template does not include `.beads/` because Beads owns that state. In an
approved repository root, after inspecting the installed `br` contract:

```bash
br --version
br capabilities --format json
br init
```

Use the real tool to create and inspect Beads issues. Keep Beads coordination
state separate from this event log and from any project-specific truth source.

## Development

```bash
python -m unittest discover -v
```

The implementation uses only the Python standard library.
