import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
CLI = TEMPLATE_ROOT / "fw.py"


class TemplateCliTests(unittest.TestCase):
    def run_cli(self, *args, expect=0, root=None):
        project_root = Path(root or tempfile.mkdtemp())
        result = subprocess.run(
            [sys.executable, str(CLI), *args, "--root", str(project_root), "--json"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expect, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(result.stderr, "")
        return project_root, payload

    def create_task(self, root, task_id, title, *dependencies):
        args = [
            "task",
            "create",
            "--id",
            task_id,
            "--title",
            title,
            "--acceptance",
            f"{title} is verified",
            "--scope",
            f"src/{task_id}.py",
            "--actor",
            "template-test",
        ]
        for dependency in dependencies:
            args.extend(["--depends-on", dependency])
        return self.run_cli(*args, root=root)

    def test_init_creates_replayable_layout_and_json_output(self):
        root, payload = self.run_cli("init", "--actor", "template-test")
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue((root / ".flywheel/events.jsonl").exists())
        self.assertTrue((root / ".flywheel/tasks/tasks.jsonl").exists())
        self.assertTrue((root / ".flywheel/memory/playbook.jsonl").exists())

        _, second = self.run_cli("init", "--actor", "template-test", root=root)
        self.assertEqual(second["status"], "PASS")
        events = (root / ".flywheel/events.jsonl").read_text().splitlines()
        self.assertEqual(len(events), 1)

    def test_ready_claim_receipt_and_completion_unlock_dependency(self):
        root, _ = self.run_cli("init", root=tempfile.mkdtemp())
        self.run_cli("agent", "register", "agent-one", root=root)
        self.create_task(root, "root", "Build the root slice")
        self.create_task(root, "child", "Verify the child slice", "root")

        _, ready = self.run_cli("task", "ready", root=root)
        self.assertEqual([task["id"] for task in ready["tasks"]], ["root"])

        self.run_cli("task", "claim", "root", "--actor", "agent-one", root=root)
        self.run_cli(
            "receipt",
            "test",
            "root",
            "--actor",
            "agent-one",
            "--command",
            "python -m unittest",
            "--status",
            "PASS",
            "--evidence",
            "tests/test_fw.py",
            root=root,
        )
        _, complete = self.run_cli(
            "task",
            "complete",
            "root",
            "--actor",
            "agent-one",
            "--reason",
            "Root slice verified by test receipt",
            root=root,
        )
        self.assertEqual(complete["status"], "PASS")

        _, ready_after = self.run_cli("task", "ready", root=root)
        self.assertEqual([task["id"] for task in ready_after["tasks"]], ["child"])

    def test_completion_requires_a_passing_test_receipt(self):
        root, _ = self.run_cli("init", root=tempfile.mkdtemp())
        self.run_cli("agent", "register", "agent-one", root=root)
        self.create_task(root, "task-a", "Make a bounded change")
        self.run_cli("task", "claim", "task-a", "--actor", "agent-one", root=root)
        _, rejected = self.run_cli(
            "task",
            "complete",
            "task-a",
            "--actor",
            "agent-one",
            "--reason",
            "done",
            expect=1,
            root=root,
        )
        self.assertEqual(rejected["status"], "FAIL")
        self.assertIn("passing test receipt", rejected["reason"])

    def test_cycle_is_reported_without_making_work_ready(self):
        root, _ = self.run_cli("init", root=tempfile.mkdtemp())
        self.create_task(root, "task-a", "A")
        self.create_task(root, "task-b", "B")
        self.run_cli("task", "dep", "add", "task-a", "task-b", "--actor", "template-test", root=root)
        self.run_cli("task", "dep", "add", "task-b", "task-a", "--actor", "template-test", root=root)
        _, ready = self.run_cli("task", "ready", root=root)
        self.assertEqual(ready["tasks"], [])
        self.assertTrue(ready["cycles"])

    def test_unknown_event_kind_is_rejected_without_log_mutation(self):
        root, _ = self.run_cli("init", root=tempfile.mkdtemp())
        event_log = root / ".flywheel/events.jsonl"
        before = event_log.read_bytes()
        _, rejected = self.run_cli(
            "event",
            "append",
            "--kind",
            "NOT_A_REAL_EVENT",
            "--actor",
            "agent-one",
            expect=1,
            root=root,
        )
        self.assertEqual(rejected["status"], "FAIL")
        self.assertIn("unknown event kind", rejected["reason"])
        self.assertEqual(event_log.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
