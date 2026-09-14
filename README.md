# python-315-lazy-imports

Four ways to defer an import in Python 3.15, measured. Companion repository for
the article *Python 3.15 Has 4 Ways to Defer an Import. All Gave Me 20x. One
Breaks pandas, polars and SQLAlchemy.*

Measured **2026-09-14** on CPython **3.15.0rc2**, Apple M2 / 8 GB / macOS 26.6.2
(arm64). Absolute milliseconds are properties of this laptop. The ratios should
travel; the 14 ms floor will not.

## Headline results

### Startup: the same 27-import CLI, four deferral strategies

```
strategy            --help ms   modules    vs eager  run ms
-----------------------------------------------------------------
interpreter floor   14.19       -          -         -
eager               296.85      945        -         299
lazy keyword        14.44       47         20.6x     299
__lazy_modules__    14.47       47         20.5x     297
manual deferred     14.45       47         20.5x     297
global all          14.33       47         20.7x     CRASH

floor = bare interpreter, 14.19 ms. No strategy can beat it.
```

All four mechanisms converge on the bare-interpreter floor, so they tie. Moving
imports into functions is not a new technique and matches PEP 810's `lazy`
keyword to within 0.01 ms. On the `run` path, where every module is used, a
reified lazy import costs nothing measurable.

### Ecosystem: 26 installed packages under `-X lazy_imports=all`

```
package               eager ms   all ms    speedup   status
--------------------------------------------------------------
pandas                196.7      74.8      -         BREAKS
fastapi               138.9      73.0      1.90x     ok
sqlalchemy            109.7      71.5      -         BREAKS
boto3                 102.6      46.1      2.22x     ok
polars                86.8       38.8      -         BREAKS
flask                 83.0       48.6      1.71x     ok
httpx                 76.9       42.1      1.83x     ok
structlog             73.0       41.1      1.77x     ok
tqdm                  68.5       46.2      1.48x     ok
requests              68.0       44.4      1.53x     ok
duckdb                54.5       35.8      1.52x     ok
pydantic              53.5       40.4      1.32x     ok
loguru                51.3       28.0      1.83x     ok
bs4                   50.6       32.4      1.56x     ok
numpy                 49.1       40.2      1.22x     ok
starlette             43.5       21.2      2.05x     ok
jinja2                40.0       28.7      1.39x     ok
PIL.Image             35.2       24.0      1.47x     ok
rich                  30.3       25.6      1.18x     ok
anyio                 28.9       25.4      1.14x     ok
lxml.etree            27.4       26.3      1.04x     ok
click                 27.2       21.2      1.29x     ok
msgspec               26.9       25.2      1.07x     ok
cryptography.fernet   23.7       21.2      1.12x     ok
yaml                  22.1       21.9      1.01x     ok
orjson                20.1       29.0      -         BREAKS

4/26 break under -X lazy_imports=all.
```

### The failures survive import and fire on first use

```
package       all: import   all: use    lazy keyword    all + filter
----------------------------------------------------------------------
pandas        ok            CRASH       ok              ok
polars        ok            CRASH       ok              ok
sqlalchemy    ok            CRASH       ok              ok
orjson        ok            CRASH       ok              ok

Every failure survives import and fires on first use.
```

`sys.set_lazy_imports_filter` restricted to `__main__` fixes all four and keeps
startup at 14.72 ms:

```python
import sys
sys.set_lazy_imports_filter(
    lambda importer, name, fromlist: importer == "__main__"
)
```

## Also worth knowing

`-X lazy_imports` in 3.15.0rc2 accepts only `all` and `normal`. The third mode
`none` that several summaries of PEP 810 describe is a **fatal error** before the
interpreter starts:

```
Fatal Python error: config_init_lazy_imports: -X lazy_imports: invalid value;
expected 'all' or 'normal'
```

CPython also ships lazy imports inside its own standard library: `sys.lazy_modules`
is non-empty at startup in the default `normal` mode.

## Reproducing

```bash
uv python install 3.15
uv venv --python 3.15 .venv
uv pip install --python .venv/bin/python -r requirements.txt

.venv/bin/python bench/gen_variants.py   # emit the 4 CLI variants from one spec
.venv/bin/python bench/harness.py        # startup, 30 reps + 3 warmups
.venv/bin/python bench/sweep.py          # 26 packages, normal vs all
.venv/bin/python bench/robustness.py     # import-vs-use, keyword, filter
.venv/bin/python bench/tables.py         # regenerate the tables above
```

The chart needs matplotlib, which had no cp315 wheel at time of writing, so it
runs on a separate 3.14 environment:

```bash
uv venv --python 3.14 .venv-plot
uv pip install --python .venv-plot/bin/python matplotlib
.venv-plot/bin/python bench/chart.py
```

## Layout

| Path | What it is |
|---|---|
| `bench/gen_variants.py` | generates the 4 CLI variants from one module list |
| `bench/harness.py` | subprocess wall-clock startup, 30 reps, 3 warmups |
| `bench/sweep.py` | imports *and* exercises 26 packages under both modes |
| `bench/robustness.py` | import-only vs used, `lazy` keyword, first-party filter |
| `bench/tables.py` | renders every table in this README from the JSON |
| `bench/chart.py` | the cover figure |
| `results/*.json` | raw results, committed |
| `results/startup.png` | the figure |
| `requirements.txt` | exact pinned versions |

## Method notes

- **Variants are generated, not hand-written**, so the four differ only in how
  imports are spelled.
- **Startup is measured as a real subprocess**, spawn included, because that is
  what a user waits for.
- **Three warmup runs per configuration** before timing. Without them whichever
  variant ran first paid to page the interpreter into the OS cache for the rest.
- **Minimum of 30 runs** is reported; medians and standard deviations are in the
  JSON.
- **The floor row is load-bearing.** A bare `python -c pass` takes 14.19 ms here,
  and a speedup quoted without it implies headroom that does not exist.
- **Every package in the sweep is imported and then called.** An import that never
  reifies proves nothing.

## Limits

- 3.15.0rc2, not the 1 October 3.15.0 final.
- One machine, one OS, one run of each suite.
- 26 packages is a sample. Four breakages is a floor on the real count.
- pyarrow had no cp315 wheel and is absent for that reason, not because it passed.
- The breakages are library bugs and may be fixed; check their trackers.

## License

MIT.
