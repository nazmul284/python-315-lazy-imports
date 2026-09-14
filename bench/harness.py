"""Time the four import strategies on the same CLI.

Startup time is what a user feels, so every measurement is the wall clock of a
real subprocess, spawn included. The bare interpreter is measured too: it is the
floor no import strategy can beat, and without it the percentages are meaningless.
"""
from __future__ import annotations
import json, pathlib, statistics, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
APPS = HERE / "apps"
PY = sys.executable
REPS, WARMUP = 30, 3

# (label, extra interpreter flags, script, how the strategy is written)
CONFIGS = [
    ("interpreter floor", [], None,                      "nothing imported"),
    ("eager",             [], "app_eager.py",            "import x at module scope"),
    ("lazy keyword",      [], "app_lazy.py",             "lazy import x (PEP 810)"),
    ("__lazy_modules__",  [], "app_lazymods.py",         "__lazy_modules__ list"),
    ("manual deferred",   [], "app_deferred.py",         "import x inside the function"),
    ("global all",        ["-X", "lazy_imports=all"], "app_eager.py",
                                                         "-X lazy_imports=all, no code change"),
]


def cmd(flags, script, argv):
    if script is None:
        return [PY, *flags, "-c", "pass"]
    return [PY, *flags, str(APPS / script), *argv]


def time_once(c):
    t0 = time.perf_counter()
    p = subprocess.run(c, capture_output=True, text=True)
    return (time.perf_counter() - t0) * 1000, p


def measure(flags, script, argv):
    c = cmd(flags, script, argv)
    for _ in range(WARMUP):          # warm the filesystem cache for every config
        time_once(c)
    samples, last = [], None
    for _ in range(REPS):
        ms, last = time_once(c)
        samples.append(ms)
    mods = None
    for line in (last.stderr or "").splitlines():
        if line.startswith("MODULES"):
            mods = int(line.split()[1])
    return {
        "min_ms": round(min(samples), 2),
        "median_ms": round(statistics.median(samples), 2),
        "mean_ms": round(statistics.mean(samples), 2),
        "stdev_ms": round(statistics.stdev(samples), 2),
        "modules": mods,
        "ok": last.returncode == 0,
        "error": None if last.returncode == 0 else (last.stderr or "").strip().splitlines()[-1][:200],
    }


def main():
    out = {"python": sys.version, "reps": REPS, "warmup": WARMUP, "paths": {}}
    for path_name, argv in (("help", ["--help", "--count"]), ("run", ["run", "--count"])):
        rows = []
        for label, flags, script, how in CONFIGS:
            if script is None and path_name == "run":
                continue                      # the floor has no work path
            r = measure(flags, script, argv)
            r.update(strategy=label, how=how)
            rows.append(r)
            print(f"  {path_name:5} {label:18} {r['min_ms']:7.2f} ms min  "
                  f"{r['median_ms']:7.2f} med  mods={r['modules']}  ok={r['ok']}")
        out["paths"][path_name] = rows
    dest = HERE.parent / "results" / "startup.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
