#!/usr/bin/env python3
"""A tiny, replayable coding flywheel template.

The event log is canonical. Everything else under .flywheel/ is a derived
projection that can be rebuilt by running any command that reads the log.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


KNOWN_EVENTS = {
    "PROJECT_INITIALIZED",
    "AGENT_REGISTERED",
    "TASK_CREATED",
    "TASK_DEP_ADDED",
    "TASK_CLAIMED",
    "TEST_RECEIPT",
    "TASK_COMPLETED",
}
STATUSES = {"PASS", "FAIL", "UNKNOWN", "NOT_DONE"}


class FlywheelError(ValueError):
    """A fail-closed user-facing error."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    text = "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for row in rows)
    atomic_write(path, text)


def _event_hash(event: dict[str, Any]) -> str:
    without_hash = {key: value for key, value in event.items() if key != "hash"}
    return hashlib.sha256(canonical_json(without_hash)).hexdigest()


def _validate_event_sequence(events: list[dict[str, Any]]) -> None:
    previous_hash = "GENESIS"
    for expected_seq, event in enumerate(events, start=1):
        required = {"seq", "id", "ts", "kind", "actor", "subject_id", "payload", "refs", "prev_hash", "hash"}
        missing = sorted(required - set(event))
        if missing:
            raise FlywheelError(f"event {expected_seq} missing fields: {', '.join(missing)}")
        if event["seq"] != expected_seq:
            raise FlywheelError(f"event sequence is not contiguous at {expected_seq}")
        if event["kind"] not in KNOWN_EVENTS:
            raise FlywheelError(f"unknown event kind: {event['kind']}")
        if event["prev_hash"] != previous_hash:
            raise FlywheelError(f"event {event['seq']} has an invalid prev_hash")
        if event["hash"] != _event_hash(event):
            raise FlywheelError(f"event {event['seq']} has an invalid hash")
        previous_hash = event["hash"]


def _copy_task(task: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(task, sort_keys=True))


def fold(events: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_event_sequence(events)
    state: dict[str, Any] = {
        "agents": {},
        "tasks": {},
        "test_receipts": [],
        "events": len(events),
    }
    for event in events:
        kind = event["kind"]
        payload = event["payload"]
        if kind == "AGENT_REGISTERED":
            state["agents"][payload["name"]] = {"name": payload["name"], "metadata": payload.get("metadata", {})}
        elif kind == "TASK_CREATED":
            task = _copy_task(payload["task"])
            task.setdefault("status", "open")
            task.setdefault("dependencies", [])
            state["tasks"][task["id"]] = task
        elif kind == "TASK_DEP_ADDED":
            task = state["tasks"].get(payload["child_id"])
            if task is None:
                raise FlywheelError(f"dependency references missing task: {payload['child_id']}")
            if payload["parent_id"] not in task["dependencies"]:
                task["dependencies"].append(payload["parent_id"])
                task["dependencies"].sort()
        elif kind == "TASK_CLAIMED":
            task = state["tasks"].get(event["subject_id"])
            if task is None:
                raise FlywheelError(f"claim references missing task: {event['subject_id']}")
            task["status"] = "in_progress"
            task["claimed_by"] = event["actor"]
        elif kind == "TEST_RECEIPT":
            state["test_receipts"].append({**payload, "actor": event["actor"], "event_id": event["id"]})
        elif kind == "TASK_COMPLETED":
            task = state["tasks"].get(event["subject_id"])
            if task is None:
                raise FlywheelError(f"completion references missing task: {event['subject_id']}")
            task["status"] = "closed"
            task["completed_by"] = event["actor"]
            task["completion"] = {"reason": payload["reason"], "evidence": payload["evidence"], "event_id": event["id"]}
    return state


class EventStore:
    def __init__(self, root: Path):
        self.root = root
        self.flywheel = root / ".flywheel"
        self.log_path = self.flywheel / "events.jsonl"

    def ensure_layout(self) -> None:
        for relative in (
            "plan/revisions",
            "tasks",
            "sessions",
            "memory",
            "reviews",
            "receipts",
        ):
            (self.flywheel / relative).mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("", encoding="utf-8")
        for relative in ("tasks/tasks.jsonl", "memory/playbook.jsonl"):
            projection = self.flywheel / relative
            if not projection.exists():
                projection.write_text("", encoding="utf-8")

    def read_events(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(self.log_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FlywheelError(f"invalid event JSON on line {line_number}: {exc.msg}") from exc
            if not isinstance(value, dict):
                raise FlywheelError(f"event on line {line_number} must be an object")
            events.append(value)
        _validate_event_sequence(events)
        return events

    def state(self) -> dict[str, Any]:
        self.ensure_layout()
        return fold(self.read_events())

    def append(self, kind: str, actor: str, subject_id: str | None, payload: dict[str, Any], refs: list[str] | None = None) -> dict[str, Any]:
        if kind not in KNOWN_EVENTS:
            raise FlywheelError(f"unknown event kind: {kind}")
        if not actor.strip():
            raise FlywheelError("actor must be non-empty")
        if not isinstance(payload, dict):
            raise FlywheelError("payload must be an object")
        self.ensure_layout()
        events = self.read_events()
        state_before = fold(events)
        event = {
            "seq": len(events) + 1,
            "id": f"ev-{len(events) + 1:06d}",
            "ts": utc_now(),
            "kind": kind,
            "actor": actor,
            "subject_id": subject_id,
            "payload": payload,
            "refs": sorted(set(refs or [])),
            "prev_hash": events[-1]["hash"] if events else "GENESIS",
        }
        event["hash"] = _event_hash(event)
        # Fold before writing so known payload failures cannot corrupt the log.
        fold(events + [event])
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.rebuild_projections(state_before=state_before)
        return event

    def rebuild_projections(self, state_before: dict[str, Any] | None = None) -> dict[str, Any]:
        state = fold(self.read_events())
        tasks = [state["tasks"][task_id] for task_id in sorted(state["tasks"])]
        atomic_jsonl(self.flywheel / "tasks/tasks.jsonl", tasks)
        atomic_jsonl(self.flywheel / "memory/playbook.jsonl", [])
        return state


def detect_cycles(tasks: dict[str, dict[str, Any]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            start = visiting.index(task_id)
            cycle = visiting[start:] + [task_id]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if task_id in visited:
            return
        visiting.append(task_id)
        for dependency in tasks[task_id].get("dependencies", []):
            if dependency in tasks:
                visit(dependency)
        visiting.pop()
        visited.add(task_id)

    for task_id in sorted(tasks):
        visit(task_id)
    return cycles


def ready_tasks(state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    tasks = state["tasks"]
    cycles = detect_cycles(tasks)
    cycle_members = {member for cycle in cycles for member in cycle}
    ready: list[dict[str, Any]] = []
    for task_id in sorted(tasks):
        task = tasks[task_id]
        if task.get("status") != "open" or task_id in cycle_members:
            continue
        dependencies = task.get("dependencies", [])
        if all(dependency in tasks and tasks[dependency].get("status") == "closed" for dependency in dependencies):
            ready.append(_copy_task(task))
    return ready, cycles


def require_agent(state: dict[str, Any], actor: str) -> None:
    if actor not in state["agents"]:
        raise FlywheelError(f"agent is not registered: {actor}")


def require_task(state: dict[str, Any], task_id: str) -> dict[str, Any]:
    task = state["tasks"].get(task_id)
    if task is None:
        raise FlywheelError(f"task not found: {task_id}")
    return task


def parse_payload(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise FlywheelError(f"payload is not valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise FlywheelError("payload must be a JSON object")
    return parsed


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--actor", default="system")

    agent = commands.add_parser("agent")
    agent_commands = agent.add_subparsers(dest="agent_command", required=True)
    register = agent_commands.add_parser("register")
    register.add_argument("name")
    register.add_argument("--actor")

    task = commands.add_parser("task")
    task_commands = task.add_subparsers(dest="task_command", required=True)
    create = task_commands.add_parser("create")
    create.add_argument("--id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--description", default="")
    create.add_argument("--priority", type=int, default=2)
    create.add_argument("--acceptance", action="append", required=True)
    create.add_argument("--scope", action="append", required=True)
    create.add_argument("--depends-on", action="append", default=[])
    create.add_argument("--actor", default="system")

    dep = task_commands.add_parser("dep")
    dep_commands = dep.add_subparsers(dest="dep_command", required=True)
    dep_add = dep_commands.add_parser("add")
    dep_add.add_argument("child_id")
    dep_add.add_argument("parent_id")
    dep_add.add_argument("--actor", default="system")

    task_commands.add_parser("ready")
    claim = task_commands.add_parser("claim")
    claim.add_argument("task_id")
    claim.add_argument("--actor", required=True)
    complete = task_commands.add_parser("complete")
    complete.add_argument("task_id")
    complete.add_argument("--actor", required=True)
    complete.add_argument("--reason", required=True)

    receipt = commands.add_parser("receipt")
    receipt_commands = receipt.add_subparsers(dest="receipt_command", required=True)
    test = receipt_commands.add_parser("test")
    test.add_argument("task_id")
    test.add_argument("--actor", required=True)
    test.add_argument("--command", dest="test_command", required=True)
    test.add_argument("--status", choices=sorted(STATUSES), required=True)
    test.add_argument("--evidence", action="append", default=[])

    event = commands.add_parser("event")
    event_commands = event.add_subparsers(dest="event_command", required=True)
    append = event_commands.add_parser("append")
    append.add_argument("--kind", required=True)
    append.add_argument("--actor", required=True)
    append.add_argument("--subject-id")
    append.add_argument("--payload", default="{}")
    append.add_argument("--refs", action="append", default=[])

    commands.add_parser("cycle")
    return parser


def extract_global_args(argv: list[str]) -> tuple[list[str], Path, bool]:
    args = list(argv)
    json_mode = False
    while "--json" in args:
        args.remove("--json")
        json_mode = True
    root = Path(".")
    if "--root" in args:
        index = args.index("--root")
        if index + 1 >= len(args):
            raise FlywheelError("--root requires a path")
        root = Path(args[index + 1])
        del args[index : index + 2]
    return args, root.resolve(), json_mode


def result(status: str, **fields: Any) -> dict[str, Any]:
    return {"status": status, **fields}


def dispatch(args: argparse.Namespace, store: EventStore) -> dict[str, Any]:
    if args.command == "init":
        store.ensure_layout()
        events = store.read_events()
        if not events:
            event = store.append("PROJECT_INITIALIZED", args.actor, None, {"root": str(store.root)})
            return result("PASS", event_id=event["id"], root=str(store.root))
        store.rebuild_projections()
        return result("PASS", root=str(store.root), events=len(events), idempotent=True)

    state = store.state()
    if not state["events"]:
        raise FlywheelError("project is not initialized; run fw init first")

    if args.command == "agent" and args.agent_command == "register":
        actor = args.actor or args.name
        if args.name in state["agents"]:
            return result("PASS", agent=state["agents"][args.name], idempotent=True)
        event = store.append("AGENT_REGISTERED", actor, args.name, {"name": args.name, "metadata": {}})
        return result("PASS", agent=args.name, event_id=event["id"])

    if args.command == "task" and args.task_command == "create":
        if args.id in state["tasks"]:
            raise FlywheelError(f"task already exists: {args.id}")
        if args.priority < 0 or args.priority > 4:
            raise FlywheelError("priority must be between 0 and 4")
        for dependency in args.depends_on:
            if dependency not in state["tasks"]:
                raise FlywheelError(f"dependency task not found: {dependency}")
        task = {
            "id": args.id,
            "title": args.title,
            "description": args.description or args.title,
            "acceptance": args.acceptance,
            "scope": args.scope,
            "priority": args.priority,
            "dependencies": sorted(set(args.depends_on)),
            "status": "open",
        }
        event = store.append("TASK_CREATED", args.actor, args.id, {"task": task})
        return result("PASS", task=task, event_id=event["id"])

    if args.command == "task" and args.task_command == "dep":
        require_task(state, args.child_id)
        require_task(state, args.parent_id)
        if args.child_id == args.parent_id:
            raise FlywheelError("task cannot depend on itself")
        if args.parent_id in state["tasks"][args.child_id].get("dependencies", []):
            return result("PASS", child_id=args.child_id, parent_id=args.parent_id, idempotent=True)
        event = store.append("TASK_DEP_ADDED", args.actor, args.child_id, {"child_id": args.child_id, "parent_id": args.parent_id})
        return result("PASS", child_id=args.child_id, parent_id=args.parent_id, event_id=event["id"])

    if args.command == "task" and args.task_command == "ready":
        ready, cycles = ready_tasks(state)
        return result("PASS", tasks=ready, cycles=cycles, next=ready[0] if ready else None)

    if args.command == "task" and args.task_command == "claim":
        require_agent(state, args.actor)
        task = require_task(state, args.task_id)
        ready, _ = ready_tasks(state)
        if args.task_id not in {item["id"] for item in ready}:
            if task.get("status") == "in_progress" and task.get("claimed_by") == args.actor:
                return result("PASS", task=task, idempotent=True)
            raise FlywheelError(f"task is not ready: {args.task_id}")
        event = store.append("TASK_CLAIMED", args.actor, args.task_id, {})
        return result("PASS", task_id=args.task_id, actor=args.actor, event_id=event["id"])

    if args.command == "receipt" and args.receipt_command == "test":
        require_agent(state, args.actor)
        task = require_task(state, args.task_id)
        if not args.test_command.strip():
            raise FlywheelError("test command must be non-empty")
        payload = {
            "task_id": args.task_id,
            "command": args.test_command,
            "status": args.status,
            "evidence": args.evidence,
        }
        event = store.append("TEST_RECEIPT", args.actor, args.task_id, payload)
        return result("PASS" if args.status == "PASS" else args.status, receipt={**payload, "event_id": event["id"]})

    if args.command == "task" and args.task_command == "complete":
        require_agent(state, args.actor)
        task = require_task(state, args.task_id)
        if task.get("status") != "in_progress" or task.get("claimed_by") != args.actor:
            raise FlywheelError("task must be claimed by the completing agent")
        passing = [receipt for receipt in state["test_receipts"] if receipt.get("task_id") == args.task_id and receipt.get("status") == "PASS"]
        if not passing:
            raise FlywheelError("task requires a passing test receipt before completion")
        evidence = sorted({item for receipt in passing for item in receipt.get("evidence", [])})
        event = store.append("TASK_COMPLETED", args.actor, args.task_id, {"reason": args.reason, "evidence": evidence})
        return result("PASS", task_id=args.task_id, evidence=evidence, event_id=event["id"])

    if args.command == "event" and args.event_command == "append":
        payload = parse_payload(args.payload)
        event = store.append(args.kind, args.actor, args.subject_id, payload, args.refs)
        return result("PASS", event=event)

    if args.command == "cycle":
        ready, cycles = ready_tasks(state)
        status = "PASS" if ready else "NOT_DONE"
        return result(
            status,
            current_object=str(store.root),
            graph={"task_count": len(state["tasks"]), "cycles": cycles},
            ready=ready,
            next_action=(f"fw task claim {ready[0]['id']} --actor <agent> --root {store.root} --json" if ready else None),
        )

    raise FlywheelError("unsupported command")


def main(argv: list[str] | None = None) -> int:
    try:
        raw, root, _json_mode = extract_global_args(argv if argv is not None else sys.argv[1:])
        args = make_parser().parse_args(raw)
        payload = dispatch(args, EventStore(root))
    except SystemExit as exc:
        return int(exc.code)
    except (FlywheelError, OSError) as exc:
        payload = result("FAIL", reason=str(exc))
    print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "UNKNOWN": 2, "NOT_DONE": 3}.get(payload["status"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
