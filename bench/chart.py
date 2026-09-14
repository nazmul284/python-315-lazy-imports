"""Cover figure: --help startup for the same CLI under five import strategies.

Emphasis form, not categorical: one hue for the strategies that work, the
reserved critical status colour for the one that crashes, grey for the eager
baseline being beaten. The status colour ships with a written label, never alone.
Values come from results/startup.json so the figure cannot drift from the tables.
"""
from __future__ import annotations
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "results" / "startup.json").read_text())
H = {r["strategy"]: r for r in D["paths"]["help"]}
RUN = {r["strategy"]: r for r in D["paths"]["run"]}

SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"
GRID, AXIS, GREY = "#e1e0d9", "#c3c2b7", "#898781"
BLUE, CRITICAL = "#2a78d6", "#d03b3b"

ORDER = ["eager", "lazy keyword", "__lazy_modules__", "manual deferred", "global all"]
LABEL = {"eager": "eager\nimport x",
         "lazy keyword": "lazy keyword\nlazy import x",
         "__lazy_modules__": "__lazy_modules__\nlist at module top",
         "manual deferred": "manual deferred\nimport inside function",
         "global all": "global all\n-X lazy_imports=all"}
floor = H["interpreter floor"]["min_ms"]

fig, ax = plt.subplots(figsize=(8.6, 4.9), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

ys = range(len(ORDER))
vals = [H[k]["min_ms"] for k in ORDER]
colors = [GREY if k == "eager" else (CRITICAL if k == "global all" else BLUE)
          for k in ORDER]
ax.barh(list(ys), vals, height=0.58, color=colors, zorder=3)

ax.axvline(floor, color=AXIS, ls=(0, (4, 3)), lw=1.4, zorder=4)
ax.text(floor + 7, -0.62, f"bare interpreter floor, {floor:.2f} ms",
        color=MUTED, fontsize=8.5, va="center")

for y, k, v in zip(ys, ORDER, vals):
    mods = H[k]["modules"]
    note = f"{v:.2f} ms   {mods} modules"
    if k != "eager":
        note += f"   {H['eager']['min_ms'] / v:.1f}x faster"
    ax.text(v + 4, y, note, va="center", fontsize=9, color=INK, zorder=5)
    if k == "global all":
        ax.text(v + 4, y - 0.34, "crashes on first use: pandas, polars, "
                "SQLAlchemy, orjson", va="center", fontsize=8.5,
                color=CRITICAL, style="italic", zorder=5)

ax.set_yticks(list(ys))
ax.set_yticklabels([LABEL[k] for k in ORDER], fontsize=9, color=INK, linespacing=1.5)
ax.set_ylim(4.72, -0.92)
ax.set_xlim(0, 430)
ax.set_xlabel("time to print --help, milliseconds (minimum of 30 runs)",
              fontsize=9, color=MUTED, labelpad=8)
ax.tick_params(axis="x", colors=MUTED, labelsize=8.5, length=0)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for side in ("top", "right", "bottom"):
    ax.spines[side].set_visible(False)
ax.spines["left"].set_color(AXIS)

handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (GREY, BLUE, CRITICAL)]
ax.legend(handles, ["eager baseline", "defers correctly", "breaks on first use"],
          loc="lower right", frameon=False, fontsize=8.5, labelcolor=MUTED,
          handlelength=1.1, handleheight=1.1, borderpad=0.2)

fig.text(0.035, 0.945, "Same CLI, same 27 imports, four ways to defer them",
         fontsize=14, color=INK, ha="left", va="center", weight="bold")
fig.text(0.035, 0.882, "Python 3.15.0rc2 on an Apple M2. Every strategy lands at "
         "the interpreter floor. One crashes when the program runs.",
         fontsize=9.2, color=MUTED, ha="left", va="center")

fig.subplots_adjust(left=0.215, right=0.985, top=0.825, bottom=0.15)
out = ROOT / "results" / "startup.png"
fig.savefig(out, facecolor=SURFACE)
print("wrote", out)
