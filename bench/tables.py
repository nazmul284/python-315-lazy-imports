"""Render the article/README tables from the result JSON.

Generated, not hand-typed: it is the only thing that stops the article and the
repository disagreeing. Every block is kept under 76 characters so it does not
wrap on a phone.
"""
from __future__ import annotations
import json, pathlib

R = pathlib.Path(__file__).resolve().parent.parent / "results"
load = lambda n: json.loads((R / n).read_text())


def rule(w):    return "-" * sum(w) 
def row(cells, w): return "".join(str(c).ljust(x) for c, x in zip(cells, w)).rstrip()


def startup_table() -> str:
    d = load("startup.json")
    helps = {r["strategy"]: r for r in d["paths"]["help"]}
    runs = {r["strategy"]: r for r in d["paths"]["run"]}
    floor = helps["interpreter floor"]["min_ms"]
    w = [20, 12, 11, 10, 12]
    out = [row(["strategy", "--help ms", "modules", "vs eager", "run ms"], w), rule(w)]
    for k in ["interpreter floor", "eager", "lazy keyword", "__lazy_modules__",
              "manual deferred", "global all"]:
        h = helps[k]
        r = runs.get(k)
        speed = "-" if k in ("eager", "interpreter floor") else \
                f"{helps['eager']['min_ms'] / h['min_ms']:.1f}x"
        runcell = "-" if r is None else ("CRASH" if not r["ok"] else f"{r['min_ms']:.0f}")
        out.append(row([k, f"{h['min_ms']:.2f}", h["modules"] or "-", speed, runcell], w))
    out.append("")
    out.append(f"floor = bare interpreter, {floor:.2f} ms. No strategy can beat it.")
    return "\n".join(out)


def sweep_table() -> str:
    d = load("sweep.json")
    rows = sorted(d["rows"], key=lambda r: -r["eager"]["min_ms"])
    w = [22, 11, 10, 10, 9]
    out = [row(["package", "eager ms", "all ms", "speedup", "status"], w), rule(w)]
    for r in rows:
        sp = f"{r['speedup']:.2f}x" if r["speedup"] else "-"
        out.append(row([r["package"], f"{r['eager']['min_ms']:.1f}",
                        f"{r['lazy_all']['min_ms']:.1f}", sp,
                        "ok" if r["lazy_all"]["ok"] else "BREAKS"], w))
    broke = d["broken_under_lazy_all"]
    out += ["", f"{len(broke)}/{d['packages']} break under -X lazy_imports=all."]
    return "\n".join(out)


def robustness_table() -> str:
    d = load("robustness.json")
    w = [14, 14, 12, 16, 14]
    out = [row(["package", "all: import", "all: use", "lazy keyword",
                "all + filter"], w), rule(w)]
    ok = lambda b: "ok" if b else "CRASH"
    for r in d["rows"]:
        out.append(row([r["package"], ok(r["all_import_only"]["ok"]),
                        ok(r["all_import_and_use"]["ok"]),
                        ok(r["lazy_keyword"]["ok"]),
                        ok(r["all_plus_first_party_filter"]["ok"])], w))
    out += ["", "Every failure survives import and fires on first use."]
    return "\n".join(out)


if __name__ == "__main__":
    for name, fn in [("STARTUP", startup_table), ("SWEEP", sweep_table),
                     ("ROBUSTNESS", robustness_table)]:
        print(f"\n===== {name} =====\n{fn()}")
