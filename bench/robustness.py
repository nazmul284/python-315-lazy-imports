"""Three checks on the breakage claim before it goes in a title.

1. Does the failure happen at import, or only when the API is used? A break that
   needs a specific call is a weaker claim than one that fires on import alone.
2. Does the explicit `lazy` keyword hit the same failures? If it does, the
   distinction the article draws between the two is not real.
3. Does sys.set_lazy_imports_filter rescue them? That is the practical fix, and
   an untested fix is not a recommendation.
"""
from __future__ import annotations
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
PY = sys.executable
BROKEN = ["pandas", "polars", "sqlalchemy", "orjson"]
USE = {"pandas": "pandas.DataFrame({'a':[1,2]}).sum()",
       "polars": "polars.DataFrame({'a':[1,2]}).sum()",
       "sqlalchemy": "sqlalchemy.create_engine('sqlite://')",
       "orjson": "orjson.dumps({'a':1})"}

# Only defer imports issued by our own module; let every installed package
# import its own dependencies eagerly, the way its authors tested it.
FILTER = (
    "import sys\n"
    "def only_first_party(importer, name, fromlist):\n"
    "    return importer == '__main__'\n"
    "sys.set_lazy_imports_filter(only_first_party)\n"
)


def run(src, flags=()):
    p = subprocess.run([PY, *flags, "-c", src], capture_output=True, text=True)
    if p.returncode == 0:
        return True, None
    lines = [l for l in (p.stderr or "").strip().splitlines() if l.strip()]
    return False, (lines[-1][:140] if lines else "unknown")


def main():
    rows = []
    for pkg in BROKEN:
        use = USE[pkg]
        imp_only, e1 = run(f"import {pkg}", ["-X", "lazy_imports=all"])
        with_use, e2 = run(f"import {pkg}\n{use}", ["-X", "lazy_imports=all"])
        kw, e3 = run(f"lazy import {pkg}\n{use}")
        filt, e4 = run(FILTER + f"import {pkg}\n{use}", ["-X", "lazy_imports=all"])
        rows.append({"package": pkg,
                     "all_import_only": {"ok": imp_only, "error": e1},
                     "all_import_and_use": {"ok": with_use, "error": e2},
                     "lazy_keyword": {"ok": kw, "error": e3},
                     "all_plus_first_party_filter": {"ok": filt, "error": e4}})
        print(f"  {pkg:12} all/import-only={imp_only!s:5} all/used={with_use!s:5} "
              f"lazy-keyword={kw!s:5} all+filter={filt!s:5}")
    dest = HERE.parent / "results" / "robustness.json"
    dest.write_text(json.dumps({"python": sys.version, "rows": rows}, indent=2))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
