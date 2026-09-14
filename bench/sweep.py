"""Does -X lazy_imports=all work on packages nobody wrote for it?

Global lazy mode is the only variant that needs no code change, which is why
every write-up recommends it first. It also applies recursively to third-party
code, so the question is not how much faster it is but how often it still runs.

Each package gets a smoke expression that touches its real API, because an
import that never reifies proves nothing.
"""
from __future__ import annotations
import json, pathlib, statistics, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
PY = sys.executable
REPS, WARMUP = 7, 2

# (import statement, expression that exercises the public API)
PKGS = [
    ("import numpy",        "numpy.arange(10).sum()"),
    ("import pandas",       "pandas.DataFrame({'a':[1,2]}).sum()"),
    ("import polars",       "polars.DataFrame({'a':[1,2]}).sum()"),
    ("import duckdb",       "duckdb.sql('select 42').fetchall()"),
    ("import requests",     "requests.Request('GET','http://x').prepare()"),
    ("import httpx",        "httpx.Request('GET','http://x')"),
    ("import pydantic",     "pydantic.BaseModel"),
    ("import sqlalchemy",   "sqlalchemy.create_engine('sqlite://')"),
    ("import flask",        "flask.Flask('t')"),
    ("import fastapi",      "fastapi.FastAPI()"),
    ("import starlette",    "__import__('starlette.applications').applications.Starlette()"),
    ("import rich",         "rich.get_console()"),
    ("import click",        "click.Command('x')"),
    ("import jinja2",       "jinja2.Template('{{a}}').render(a=1)"),
    ("import yaml",         "yaml.safe_load('a: 1')"),
    ("import boto3",        "boto3.session.Session()"),
    ("import PIL.Image",    "PIL.Image.new('RGB',(2,2))"),
    ("import lxml.etree",   "lxml.etree.fromstring('<a/>')"),
    ("import cryptography.fernet", "cryptography.fernet.Fernet.generate_key()"),
    ("import bs4",          "bs4.BeautifulSoup('<a/>','html.parser')"),
    ("import orjson",       "orjson.dumps({'a':1})"),
    ("import msgspec",      "msgspec.json.encode({'a':1})"),
    ("import tqdm",         "tqdm.tqdm(range(2), disable=True)"),
    ("import loguru",       "loguru.logger"),
    ("import structlog",    "structlog.get_logger()"),
    ("import anyio",        "anyio.Event"),
]

SRC = "{imp}\n{expr}\nimport sys; print('MODULES', len(sys.modules))\n"


def run(flags, imp, expr):
    src = SRC.format(imp=imp, expr=expr)
    c = [PY, *flags, "-c", src]
    for _ in range(WARMUP):
        subprocess.run(c, capture_output=True, text=True)
    samples, last = [], None
    for _ in range(REPS):
        t0 = time.perf_counter()
        last = subprocess.run(c, capture_output=True, text=True)
        samples.append((time.perf_counter() - t0) * 1000)
    mods = None
    for line in (last.stdout or "").splitlines():
        if line.startswith("MODULES"):
            mods = int(line.split()[1])
    err = None
    if last.returncode != 0:
        lines = [l for l in (last.stderr or "").strip().splitlines() if l.strip()]
        err = lines[-1][:160] if lines else "unknown"
    return {"min_ms": round(min(samples), 2),
            "median_ms": round(statistics.median(samples), 2),
            "modules": mods, "ok": last.returncode == 0, "error": err}


def main():
    rows = []
    for imp, expr in PKGS:
        name = imp.split()[1]
        eager = run([], imp, expr)
        allm = run(["-X", "lazy_imports=all"], imp, expr)
        speedup = (round(eager["min_ms"] / allm["min_ms"], 2)
                   if allm["ok"] and allm["min_ms"] else None)
        rows.append({"package": name, "eager": eager, "lazy_all": allm,
                     "speedup": speedup})
        status = "ok " if allm["ok"] else "BREAK"
        print(f"  {name:28} eager {eager['min_ms']:7.1f} ms  all {allm['min_ms']:7.1f} ms"
              f"  {status}  {'' if allm['ok'] else allm['error'][:70]}")
    broke = [r['package'] for r in rows if not r['lazy_all']['ok']]
    out = {"python": sys.version, "reps": REPS, "packages": len(rows),
           "broken_under_lazy_all": broke, "rows": rows}
    dest = HERE.parent / "results" / "sweep.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"\n{len(broke)}/{len(rows)} broke under -X lazy_imports=all: {broke}")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
