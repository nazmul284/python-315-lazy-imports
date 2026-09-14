

def work():
    import pandas
    import numpy
    import requests
    import rich
    import jinja2
    import yaml
    import httpx
    import pydantic
    import click
    import json
    import csv
    import sqlite3
    import logging
    import decimal
    import datetime
    import zipfile
    import tarfile
    import statistics
    import xml.etree.ElementTree
    import email.message
    import http.client
    import urllib.request
    import hashlib
    import subprocess
    import concurrent.futures
    import dataclasses
    import ssl
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
