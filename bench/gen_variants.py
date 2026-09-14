"""Generate the four CLI variants from one shared spec.

The point of generating them is that the variants provably differ only in how
the imports are written. Editing four files by hand is how you end up comparing
two things that are not the same program.
"""
from __future__ import annotations
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
APPS = HERE / "apps"

# A realistic "data CLI" dependency set: heavy third-party plus the stdlib
# modules that argparse-era CLIs habitually pull in at module scope.
THIRD_PARTY = ["pandas", "numpy", "requests", "rich", "jinja2", "yaml",
               "httpx", "pydantic", "click"]
STDLIB = ["json", "csv", "sqlite3", "logging", "decimal", "datetime",
          "zipfile", "tarfile", "statistics", "xml.etree.ElementTree",
          "email.message", "http.client", "urllib.request", "hashlib",
          "subprocess", "concurrent.futures", "dataclasses", "ssl"]
MODULES = THIRD_PARTY + STDLIB

BODY = '''

def work():
    """Touch every imported name so the lazy variants must reify all of them."""
    df = pandas.DataFrame({"a": numpy.arange(1000)})
    total = int(df["a"].sum())
    blob = json.dumps({"total": total})
    h = hashlib.sha256(blob.encode()).hexdigest()[:8]
    names = [requests.__name__, rich.__name__, jinja2.__name__, yaml.__name__,
             httpx.__name__, pydantic.__name__, click.__name__, csv.__name__,
             sqlite3.__name__, logging.__name__, decimal.__name__,
             datetime.__name__, zipfile.__name__, tarfile.__name__,
             statistics.__name__, xml.etree.ElementTree.__name__,
             email.message.__name__, http.client.__name__,
             urllib.request.__name__, subprocess.__name__,
             concurrent.futures.__name__, dataclasses.__name__, ssl.__name__]
    return total, h, len(names)


def main(argv):
    if "--help" in argv or not argv:
        print("usage: app [--help] [--version] run")
        return 0
    if "--version" in argv:
        print("app 1.0")
        return 0
    if argv[0] == "run":
        print(work())
        return 0
    return 2


if __name__ == "__main__":
    import sys as _sys
    code = main(_sys.argv[1:])
    if "--count" in _sys.argv:
        print("MODULES", len(_sys.modules), file=_sys.stderr)
    raise SystemExit(code)
'''


def imports(style: str) -> str:
    if style == "eager":
        return "\n".join(f"import {m}" for m in MODULES)
    if style == "lazy":
        return "\n".join(f"lazy import {m}" for m in MODULES)
    if style == "lazymods":
        listing = ", ".join(repr(m) for m in MODULES)
        return (f"__lazy_modules__ = [{listing}]\n"
                + "\n".join(f"import {m}" for m in MODULES))
    raise ValueError(style)


def deferred_body() -> str:
    """The pre-3.15 technique: every import moved inside the function."""
    inner = "\n".join(f"    import {m}" for m in MODULES)
    return BODY.replace("def work():\n", "def work():\n" + inner + "\n", 1)


def main() -> None:
    APPS.mkdir(exist_ok=True)
    for style in ("eager", "lazy", "lazymods"):
        (APPS / f"app_{style}.py").write_text(imports(style) + BODY)
    # deferred: nothing at module scope, everything inside work()
    (APPS / "app_deferred.py").write_text(deferred_body())
    print(f"wrote 4 variants to {APPS} ({len(MODULES)} modules each)")


if __name__ == "__main__":
    main()
