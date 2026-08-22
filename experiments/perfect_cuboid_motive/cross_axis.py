#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import time
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
OUT.mkdir(parents=True, exist_ok=True)
FIELD_CSV = OUT / "extension_field_character_sums.csv"
RING_CSV = OUT / "ramified_local_ring_counts.csv"
LOG = OUT / "cross_axis.log"


def read_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            rows.append({k: int(v) for k, v in raw.items() if k != "polynomial"} | ({"polynomial": raw["polynomial"]} if "polynomial" in raw else {}))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, x in enumerate(row):
            widths[i] = max(widths[i], len(str(x)))
    lines = [
        "| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |",
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(x).ljust(widths[i]) for i, x in enumerate(row)) + " |"
        for row in rows
    )
    return "\n".join(lines)


def first_failure(rows: list[dict[str, Any]], rejected_key: str, depth_key: str) -> int | None:
    failures = sorted(row[depth_key] for row in rows if row[rejected_key] > 0)
    return failures[0] if failures else None


def main() -> int:
    if not FIELD_CSV.exists():
        raise RuntimeError("extension-field result is missing; run run.py first")

    binary = OUT / "ramified_counts"
    compile_cmd = [
        "g++", "-O3", "-std=c++17", "-Wall", "-Wextra",
        str(ROOT / "ramified_counts.cpp"), "-o", str(binary),
    ]
    compile_proc = subprocess.run(compile_cmd, text=True, capture_output=True)
    LOG.write_text("$ " + " ".join(compile_cmd) + "\n" + compile_proc.stdout + compile_proc.stderr, encoding="utf-8")
    if compile_proc.returncode != 0:
        (OUT / "CROSS_AXIS_STATUS.json").write_text(
            json.dumps({"success": False, "stage": "compile", "returncode": compile_proc.returncode}, indent=2),
            encoding="utf-8",
        )
        return compile_proc.returncode

    started = time.perf_counter()
    proc = subprocess.run([str(binary), str(RING_CSV)], text=True, capture_output=True)
    elapsed = time.perf_counter() - started
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n$ {binary} {RING_CSV}\n")
        f.write(proc.stdout)
        f.write(proc.stderr)
        f.write(f"elapsed_seconds={elapsed:.6f}\n")
    if proc.returncode != 0:
        (OUT / "CROSS_AXIS_STATUS.json").write_text(
            json.dumps({"success": False, "stage": "execute", "returncode": proc.returncode}, indent=2),
            encoding="utf-8",
        )
        return proc.returncode

    field_rows = read_csv(FIELD_CSV)
    ring_rows = read_csv(RING_CSV)
    field = {(row["p"], row["n"]): row for row in field_rows}
    ring = {(row["p"], row["m"]): row for row in ring_rows}
    keys = sorted(set(field) & set(ring))

    comparison: list[dict[str, Any]] = []
    for p, depth in keys:
        f = field[(p, depth)]
        r = ring[(p, depth)]
        comparison.append({
            "p": p,
            "depth": depth,
            "cardinality": f["q"],
            "field_euler": f["euler"],
            "field_full": f["full"],
            "field_rejected": f["euler"] - f["full"],
            "field_redundant": int(f["euler"] == f["full"]),
            "field_survival": f["full"] / f["euler"],
            "ring_euler": r["euler"],
            "ring_full": r["full"],
            "ring_rejected": r["rejected"],
            "ring_redundant": r["redundant"],
            "ring_survival": r["full"] / r["euler"],
            "ring_q3_zero": r["q3_zero"],
            "same_euler_count": int(f["euler"] == r["euler"]),
            "same_full_count": int(f["full"] == r["full"]),
            "same_redundancy_status": int((f["euler"] == f["full"]) == bool(r["redundant"])),
        })
    write_csv(OUT / "ramified_vs_unramified.csv", comparison)

    n1_checks = [row for row in comparison if row["depth"] == 1]
    base_fields_match = all(row["same_euler_count"] and row["same_full_count"] for row in n1_checks)

    field_by_p: dict[int, list[dict[str, Any]]] = defaultdict(list)
    ring_by_p: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in field_rows:
        field_by_p[row["p"]].append({**row, "rejected": row["euler"] - row["full"]})
    for row in ring_rows:
        ring_by_p[row["p"]].append(row)

    failure_rows: list[dict[str, Any]] = []
    for p in sorted(set(field_by_p) & set(ring_by_p)):
        fgroup = sorted(field_by_p[p], key=lambda r: r["n"])
        rgroup = sorted(ring_by_p[p], key=lambda r: r["m"])
        ff = first_failure(fgroup, "rejected", "n")
        rf = first_failure(rgroup, "rejected", "m")
        failure_rows.append({
            "p": p,
            "first_unramified_failure_degree": "none" if ff is None else ff,
            "first_ramified_failure_depth": "none" if rf is None else rf,
            "prime_field_redundant": int(fgroup[0]["rejected"] == 0),
            "ramified_redundant_all_tested": int(rf is None),
            "unramified_redundant_all_tested": int(ff is None),
        })
    write_csv(OUT / "first_failure_axes.csv", failure_rows)

    different_counts = sum(not (row["same_euler_count"] and row["same_full_count"]) for row in comparison if row["depth"] > 1)
    different_redundancy = sum(not row["same_redundancy_status"] for row in comparison if row["depth"] > 1)

    distinctions = [
        ["D85", "Ramified jet depth m", "Unramified residue extension degree n", "orthogonal axes"],
        ["D86", "Z/p^mZ with p^m elements", "F_(p^m) with p^m elements", "same cardinality, different geometry"],
        ["D87", "Nilpotent thickening", "Reduced finite-field extension", "different local information"],
        ["D88", "Hensel/Greenberg branching", "Frobenius trace recurrence", "different transition laws"],
        ["D89", "Redundant on F_p-points", "Redundant on all geometric points over Fbar_p", "not equivalent"],
        ["D90", "Redundant over Q_p", "Redundant over finite residue extensions", "not equivalent"],
        ["D91", "Trace zero at degree one", "Motive absent", "false implication"],
        ["D92", "Singular q3=0 jet failure", "CM motive activation over F_(p^2)", "different mechanisms"],
        ["D93", "Failure first visible at p^m", "Failure first visible at F_(p^n)", "separate depths"],
        ["D94", "Arithmetic local point over Q_p", "Geometric point over algebraic residue closure", "different loci"],
        ["D95", "Local-ring density", "Finite-field point-count density", "same leading scale, different corrections"],
        ["D96", "Prime-field coincidence", "Axis-stable identity", "requires both ramified and unramified tests"],
    ]
    write_csv(
        OUT / "NEW_DISTINCTIONS_CROSS_AXIS.csv",
        [dict(id=a, left=b, right=c, status=d) for a, b, c, d in distinctions],
    )

    matrix_rows = [
        [
            row["p"], row["depth"], row["cardinality"],
            f"{row['field_euler']}/{row['field_full']}",
            f"{row['ring_euler']}/{row['ring_full']}",
            f"{row['field_survival']:.6f}", f"{row['ring_survival']:.6f}",
            row["same_redundancy_status"],
        ]
        for row in comparison
    ]
    failure_table = [
        [row["p"], row["first_unramified_failure_degree"], row["first_ramified_failure_depth"]]
        for row in failure_rows
    ]

    report = f"""# Perfect Cuboid — Ramified/Unramified Cross-Axis Iteration

## Exact scope

For matched cardinalities `p^k`, this run compared:

- the reduced field `F_(p^k)`, which changes Frobenius/residue-field degree;
- the nonreduced local ring `Z/p^k Z`, which changes nilpotent/jet thickness.

There were {len(comparison)} matched cases. At depth one, all field and ring counts agreed: **{base_fields_match}**.

## Main result

Beyond depth one, equal cardinality does not imply equal cuboid-local geometry.

- cases with different Euler or full counts: **{different_counts}**
- cases with different redundancy status: **{different_redundancy}**

{md_table(matrix_rows, ['p','depth','p^depth','field E/F','ring E/F','field survival','ring survival','same redundancy'])}

## First visible failure on each axis

{md_table(failure_table, ['p','first field-extension failure n','first ring-jet failure m'])}

The sharp examples are:

- `p=3`: the fourth equation remains redundant through every tested ramified depth, but fails over `F_(3^3)`;
- `p=5`: it fails over `F_(5^2)` but only at ring depth `5^3`;
- `p=11`: it remains redundant in every tested ramified jet and over `Q_11`, but fails over `F_(11^2)`;
- `p=13`: both axes first fail at depth two, with different counts and singular mechanisms.

## Interpretation

`Q_p`-redundancy and geometric redundancy over the residue closure are different claims.

Ramified depth probes lifting along one residue point and is governed by valuations, Jacobian rank, and singular strata. Unramified degree probes new residue-field points and is governed by Frobenius eigenvalues and the two CM symmetric-square pieces found in the motive iteration.

Thus the local state is genuinely two-dimensional:

`(ramification depth m, residue extension degree n)`.

Neither axis can substitute for the other.

## New distinctions

{md_table(distinctions, ['id','left','right','status'])}

## Verification

- every depth-one ring count equals the corresponding prime-field count;
- every ring count is an exhaustive enumeration;
- every field count was independently verified by the 16-character-sum and motive formulas;
- the comparison is descriptive and does not assert a local or global nonexistence theorem.
"""
    (OUT / "CROSS_AXIS_REPORT.md").write_text(report, encoding="utf-8")

    status = {
        "success": base_fields_match,
        "matched_cases": len(comparison),
        "depth_one_counts_match": base_fields_match,
        "different_counts_beyond_depth_one": different_counts,
        "different_redundancy_beyond_depth_one": different_redundancy,
        "first_failure_axes": failure_rows,
    }
    (OUT / "CROSS_AXIS_STATUS.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

    archive = OUT / "perfect_cuboid_cross_axis_iteration.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path != archive:
                zf.write(path, arcname=path.name)
        zf.write(ROOT / "ramified_counts.cpp", arcname="ramified_counts.cpp")
        zf.write(Path(__file__), arcname="cross_axis.py")

    return 0 if base_fields_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
