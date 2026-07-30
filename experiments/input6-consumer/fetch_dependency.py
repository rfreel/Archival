from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
LOCK_PATH = ROOT / "dependency.lock.json"
VENDOR_ROOT = ROOT / "vendor"


def load_lock(path: Path = LOCK_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_admissible(lock: dict) -> None:
    commit = lock["producer_commit"]
    if lock["status"] != "active":
        raise RuntimeError("dependency contract is not active")
    if commit in set(lock.get("revoked_commits", [])):
        raise RuntimeError(f"producer commit is revoked: {commit}")


def fetch_bytes(repository: str, commit: str, path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{repository}/{commit}/{path}"
    with urlopen(url, timeout=30) as response:
        return response.read()


def verify_sha256(data: bytes, expected: str, label: str) -> None:
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(
            f"{label} hash mismatch: expected {expected}, received {actual}"
        )


def materialize(lock: dict) -> None:
    assert_admissible(lock)
    repository = lock["producer_repository"]
    commit = lock["producer_commit"]

    module_spec = lock["files"]["module"]
    contract_spec = lock["files"]["contract"]

    module = fetch_bytes(repository, commit, module_spec["path"])
    contract = fetch_bytes(repository, commit, contract_spec["path"])

    verify_sha256(module, module_spec["sha256"], "module")
    verify_sha256(contract, contract_spec["sha256"], "contract")

    package = VENDOR_ROOT / "identifiers"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(
        "from .normalize import UnsafeIdentifier, normalize_identifier\n",
        encoding="utf-8",
    )
    (package / "normalize.py").write_bytes(module)
    (VENDOR_ROOT / "contract-v1.0.0.json").write_bytes(contract)


if __name__ == "__main__":
    current = load_lock()
    materialize(current)
    print(
        "materialized",
        current["contract_id"],
        current["contract_version"],
        current["producer_commit"],
    )
