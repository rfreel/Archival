# Template plan

## Current object

A minimal, local-first coding flywheel that a fresh worker can run without
private context or third-party services.

## Goal

Make the smallest useful loop executable:

```text
task graph → ready work → claim → implement → test receipt → evidence-gated completion
```

## Boundaries

- Python standard library only.
- `.flywheel/events.jsonl` is the durable source of task lineage.
- Projections may be rebuilt from the event log.
- No `.beads` files are checked in or hand-authored.
- Beads, GitHub publication, and multi-agent coordination are optional future integrations.

## Baseline acceptance

- [x] `fw init --json` creates the bounded runtime layout.
- [x] Tasks carry acceptance criteria, file scope, priority, and dependencies.
- [x] Ready work excludes open tasks blocked by dependencies or cycles.
- [x] Claims are explicit and attributable to registered agents.
- [x] Completion requires a passing test receipt.
- [x] Unknown event kinds fail without mutating the event log.
- [x] `python -m unittest discover -v` verifies the baseline.

## Extension order

1. Add leases before allowing concurrent file edits.
2. Add session history and scoped procedural memory before adding embeddings.
3. Add review receipts before broadening completion policy.
4. Add destructive-effect guards before automating external writes.
5. Add real Beads only through the installed `br` contract.

Every extension should add a failing behavior test first and preserve the
canonical/derived and evidence/uncertainty boundaries.
