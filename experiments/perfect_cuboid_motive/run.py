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

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"
OUT.mkdir(parents=True,exist_ok=True)
DATA=OUT/"extension_field_character_sums.csv"
LOG=OUT/"simulator.log"


def write_csv(path:Path,rows:list[dict[str,Any]])->None:
    if not rows:
        path.write_text("",encoding="utf-8");return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def table(rows:list[list[Any]],headers:list[str])->str:
    widths=[len(str(x)) for x in headers]
    for row in rows:
        for i,x in enumerate(row):widths[i]=max(widths[i],len(str(x)))
    lines=["| "+" | ".join(str(x).ljust(widths[i]) for i,x in enumerate(headers))+" |",
           "| "+" | ".join("-"*w for w in widths)+" |"]
    lines += ["| "+" | ".join(str(x).ljust(widths[i]) for i,x in enumerate(row))+" |" for row in rows]
    return "\n".join(lines)


def main()->int:
    binary=OUT/"finite_field_motive"
    cc=["g++","-O3","-std=c++17","-Wall","-Wextra",str(ROOT/"finite_field_motive.cpp"),"-o",str(binary)]
    cp=subprocess.run(cc,text=True,capture_output=True)
    LOG.write_text("$ "+" ".join(cc)+"\n"+cp.stdout+cp.stderr,encoding="utf-8")
    if cp.returncode:
        (OUT/"STATUS.json").write_text(json.dumps({"success":False,"stage":"compile","returncode":cp.returncode},indent=2));return cp.returncode
    started=time.perf_counter()
    rp=subprocess.run([str(binary),str(DATA)],text=True,capture_output=True)
    with LOG.open("a",encoding="utf-8") as f:
        f.write("\n$ "+str(binary)+" "+str(DATA)+"\n"+rp.stdout+rp.stderr)
        f.write(f"elapsed_seconds={time.perf_counter()-started:.6f}\n")
    if not DATA.exists():
        (OUT/"STATUS.json").write_text(json.dumps({"success":False,"stage":"execute","returncode":rp.returncode},indent=2));return rp.returncode or 1

    rows=[]
    with DATA.open(newline="",encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            rows.append({k:(v if k=="polynomial" else int(v)) for k,v in raw.items()})

    byp=defaultdict(list)
    for r in rows:byp[r["p"]].append(r)
    rec=[];active=[]
    for p,g in sorted(byp.items()):
        g.sort(key=lambda r:r["n"])
        for curve in ("t4","t8"):
            t1=g[0][curve];a,b=2,t1
            rec.append({"p":p,"curve":curve,"n":1,"actual":t1,"predicted":t1,"ok":True})
            for r in g[1:]:
                pred=t1*b-p*a
                rec.append({"p":p,"curve":curve,"n":r["n"],"actual":r[curve],"predicted":pred,"ok":r[curve]==pred})
                a,b=b,r[curve]
            if t1==0:
                hits=[r for r in g[1:] if r[curve]!=0]
                if hits:active.append({"p":p,"curve":curve,"first_active_degree":hits[0]["n"],"trace":hits[0][curve]})
    write_csv(OUT/"trace_recurrence_checks.csv",rec)
    write_csv(OUT/"extension_activation.csv",active)

    motives=[]
    for r in rows:
        q,e,h=r["q"],r["e"],r["h"]
        s4=r["t4"]**2-q;s8=r["t8"]**2-q
        pred={"S7":e*s8+(2*h+e)*q+2,
              "S11":s4+(1-e)*q+2,
              "S13":s4-e*q+(1+e),
              "S14":s4-e*q+(1+e),
              "S15":3*s8+(2-2*e*h)*q+(2+e)}
        for k,v in pred.items():motives.append({"p":r["p"],"n":r["n"],"q":q,"sum":k,"actual":r[k],"predicted":v,"ok":r[k]==v})
    write_csv(OUT/"motive_fingerprint_checks.csv",motives)

    sums_ok=all(r["all_character_sums_ok"] for r in rows)
    E_ok=all(r["euler_formula_ok"] for r in rows)
    F_ok=all(r["full_formula_ok"] for r in rows)
    rec_ok=all(r["ok"] for r in rec)
    motive_ok=all(r["ok"] for r in motives)
    success=all([sums_ok,E_ok,F_ok,rec_ok,motive_ok])

    distinctions=[
        ["D74","Prime-field point-count identity","Identity over F_(p^n)","extension-tested"],
        ["D75","Elliptic trace t","Symmetric-square trace t^2-q","structural split"],
        ["D76","Formula by p mod 8","Formula by chi(-1), chi(2)","finite-field invariant"],
        ["D77","CM trace vanishes over F_p","Trace activates over an extension","observed"],
        ["D78","Numerical fit across primes","Frobenius-recurrence-compatible fingerprint","stronger"],
        ["D79","Tate/boundary terms","Transcendental CM terms","separated"],
        ["D80","j=1728 contribution","j=8000 contribution","independent"],
        ["D81","Affine character sum","Compactified trace plus boundary correction","different objects"],
        ["D82","Vary p","Vary extension degree n at fixed p","new axis"],
        ["D83","Count equality","All 16 character-sum equalities","stronger"],
        ["D84","Extension-field identity","Explicit correspondence/motivic proof","still open"],
    ]
    write_csv(OUT/"NEW_DISTINCTIONS_MOTIVE.csv",[dict(id=a,left=b,right=c,status=d) for a,b,c,d in distinctions])

    fingerprint={
        "status":"extension-field computational fingerprint; not a written motivic proof",
        "tested_fields":len(rows),"max_q":max(r["q"] for r in rows),
        "all_16_sums_ok":sums_ok,"euler_ok":E_ok,"full_ok":F_ok,
        "trace_recurrences_ok":rec_ok,"motive_fingerprints_ok":motive_ok,
        "sym2_local_polynomial":"1-(t^2-q)T+(q*t^2-q^2)T^2-q^3T^3",
        "extension_activations":active,
    }
    (OUT/"motive_fingerprints.json").write_text(json.dumps(fingerprint,indent=2),encoding="utf-8")

    fields=[[r["p"],r["n"],r["q"],r["e"],r["h"],r["t4"],r["t8"],r["euler"],r["full"]] for r in rows]
    report=f"""# Perfect Cuboid — Extension-Field Motive Iteration

## Exact scope

The simulator exhaustively evaluated all `(b,c)` over {len(rows)} finite fields `F_(p^n)`, with maximum field size {max(r['q'] for r in rows):,}. Arithmetic used explicit polynomial-basis finite fields.

## Result

- all 16 character-sum formulas: **{sums_ok}**
- Euler count formula: **{E_ok}**
- full count formula: **{F_ok}**
- Frobenius recurrences for E4 and E8: **{rec_ok}**
- symmetric-square fingerprints: **{motive_ok}**

{table(fields,['p','n','q','chi(-1)','chi(2)','t4','t8','Euler','Full'])}

## Motive-level fingerprint

For an elliptic curve over `F_q` with trace `t`,

`Tr(Sym^2 H^1)=t^2-q`,

and the local polynomial is

`1-(t^2-q)T+(q*t^2-q^2)T^2-q^3T^3`.

The hard sums reduce to:

- `S7 = chi(-1)(t8^2-q)+(2chi(2)+chi(-1))q+2`
- `S11 = (t4^2-q)+(1-chi(-1))q+2`
- `S13=S14 = (t4^2-q)-chi(-1)q+(1+chi(-1))`
- `S15 = 3(t8^2-q)+(2-2chi(-1)chi(2))q+(2+chi(-1))`

This separates Tate/boundary terms from two CM symmetric-square traces.

## Extension activation

{table([[x['p'],x['curve'],x['first_active_degree'],x['trace']] for x in active],['p','curve','first active n','trace']) if active else 'None'}

A trace that vanishes over `F_p` can reactivate over `F_(p^2)`. Prime-congruence simplifications therefore do not imply the motive is absent.

## New distinctions

{table(distinctions,['id','left','right','status'])}

## Limit

Extension-field agreement is much stronger than fitting unrelated prime counts, but it is not yet an explicit algebraic correspondence or proof of motive decomposition.
"""
    (OUT/"MOTIVE_ITERATION_REPORT.md").write_text(report,encoding="utf-8")
    (OUT/"STATUS.json").write_text(json.dumps({"success":success,**fingerprint},indent=2),encoding="utf-8")

    archive=OUT/"perfect_cuboid_motive_iteration.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            if p.is_file() and p!=archive:z.write(p,p.name)
        z.write(ROOT/"finite_field_motive.cpp","finite_field_motive.cpp")
        z.write(Path(__file__),"run.py")
    return 0 if success else 1

if __name__=="__main__":raise SystemExit(main())
