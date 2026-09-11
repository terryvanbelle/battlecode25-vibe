#!/usr/bin/env python3
"""
Darla's two charts, both read off disk so they regenerate as arms land.

WHY DARLA NEEDS DIFFERENT CHARTS FROM THE OTHER THREE. The standard pair
(cumulative_iterations, vs_old_bots) assumes a lineage that accumulates ACCEPTED
snapshots over days. Darla has one shipped build and a row of rejected
candidates, all measured as MATCHED PAIRS on the same two pinned 12-map samples
against the same three frozen opponents. So the informative axes are "which arms
were tried and what did they cost" and "what does the dose curve look like",
not "how did the bot climb over time". The standard charts are still produced;
cumulative_iterations is simply empty, which is the honest picture.

Reads gauntlet/<run>/{bot.txt,summary.txt} plus progress/arms.txt.
Writes progress/arm_ladder.png and progress/splash_floor_dose.png.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
OPPONENTS = ["carol", "bob", "alice"]

INK, MUTED, GRID = "#1c1c1e", "#6b7280", "#d9d9de"
BASE_C, WORSE_C, BETTER_C, TIE_C = "#2563a8", "#b4453c", "#2e7d5b", "#8a8a8f"


def load_arms():
    arms = {}
    for line in (WS / "progress" / "arms.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        pkg, axis, dose, label = (p.strip() for p in line.split("|"))
        arms[pkg] = {"axis": axis,
                     "dose": None if dose == "-" else int(dose),
                     "label": label}
    return arms


def parse_run(d):
    """(bot, overall_wins, overall_total, {opponent: (wins, total)}) or None."""
    bot_f, sum_f = d / "bot.txt", d / "summary.txt"
    if not (bot_f.is_file() and sum_f.is_file()):
        return None
    m = re.search(r"^bot=(\S+)", bot_f.read_text(), re.M)
    if not m:
        return None
    text = sum_f.read_text()
    mo = re.search(r"^overall: (\d+)/(\d+) wins", text, re.M)
    if not mo:
        return None
    per = {}
    for om in re.finditer(r"^  vs (\w+)\s+(\d+)/(\d+) ", text, re.M):
        per[om.group(1)] = (int(om.group(2)), int(om.group(3)))
    return m.group(1), int(mo.group(1)), int(mo.group(2)), per


def collect(arms):
    """Sum each arm over its pinned-sample runs. 72-game runs only."""
    tot = defaultdict(lambda: [0, 0, defaultdict(lambda: [0, 0])])
    for d in sorted((WS / "gauntlet").iterdir()):
        if not d.is_dir():
            continue
        got = parse_run(d)
        if not got:
            continue
        bot, w, n, per = got
        if n != 72 or bot not in arms:
            continue
        tot[bot][0] += w
        tot[bot][1] += n
        for opp, (ow, on) in per.items():
            tot[bot][2][opp][0] += ow
            tot[bot][2][opp][1] += on
    # An arm that has played only ONE of the two pinned samples is a PREFIX of
    # the baseline's map list, not a random subsample of it -- opponents are the
    # outer loop and maps play in fixed shared order. Plotting 72 games against
    # a 144-game baseline would compare different ground and read as a real
    # delta. Drop short arms rather than scale them; the chart redraws when the
    # arm completes. (Caught by this script plotting a half-finished darla6.)
    full = tot["darla"][1] if "darla" in tot else None
    if full:
        short = [b for b in tot if tot[b][1] != full]
        for b in short:
            print(f"   skipping {b}: {tot[b][1]}/{full} games -- run incomplete")
            del tot[b]
    return tot


def sd(n):
    return 0.5 * (n ** 0.5)          # binomial sd in GAMES at p=0.5


def arm_ladder(arms, tot, out):
    base_w, base_n = tot["darla"][0], tot["darla"][1]
    rows = [(p, d) for p, d in arms.items() if p in tot and p != "darla"]
    rows.sort(key=lambda r: tot[r[0]][0] / max(tot[r[0]][1], 1))

    fig, ax = plt.subplots(figsize=(10.5, 0.72 * len(rows) + 2.9))
    ys = range(len(rows))
    band = sd(base_n)
    ax.axvspan(base_w - band, base_w + band, color=TIE_C, alpha=0.16, lw=0,
               label=f"±1 sd of the baseline ({band:.1f} games)")
    ax.axvline(base_w, color=BASE_C, lw=2.2, zorder=3)

    for y, (pkg, meta) in zip(ys, rows):
        w, n, per = tot[pkg]
        delta = w - base_w
        colour = BETTER_C if delta > band else WORSE_C if delta < -band else TIE_C
        ax.barh(y, w, height=0.46, color=colour, alpha=0.9, zorder=2)
        for opp in OPPONENTS:                       # per-opponent, scaled to 144
            ow, on = per.get(opp, (0, 0))
            if on:
                ax.plot(ow * base_n / on, y, "o", ms=4.5, mfc="white",
                        mec=INK, mew=1.0, zorder=4)
        # Fixed label column, clear of the scaled opponent dots, so the
        # numbers line up and never sit on a marker.
        ax.text(base_n * 1.045, y, f"{w}/{n}", va="center", fontsize=9.5,
                color=INK, fontfamily="monospace")
        ax.text(base_n * 1.135, y, f"{w/n*100:5.1f}%", va="center",
                fontsize=9.5, color=INK, fontfamily="monospace")
        ax.text(base_n * 1.225, y, f"{delta:+d}", va="center", fontsize=9.5,
                color=colour, fontfamily="monospace", fontweight="bold")

    ax.set_yticks(list(ys))
    ax.set_yticklabels([f"{m['label']}\n{p}" for p, m in rows], fontsize=9)
    ax.set_xticks([0, 24, 48, 72, 96, 120, 144])
    ax.set_xlabel(f"wins out of {base_n} matched games   "
                  "(hollow dots: the carol / bob / alice legs, scaled)",
                  fontsize=9.5)
    ax.set_xlim(0, base_n * 1.30)
    ax.set_title("Darla — every arm against the shipped baseline\n"
                 f"matched pairs on two pinned 12-map samples vs three frozen "
                 f"opponents\nbaseline {base_w}/{base_n} "
                 f"({base_w/base_n*100:.1f}%), blue line",
                 fontsize=11, loc="left", color=INK, pad=11)
    ax.grid(axis="x", color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.legend(loc="lower left", fontsize=8.5, frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"wrote {out} ({len(rows)} arms)")


def dose(arms, tot, out):
    pts = sorted(((m["dose"], p) for p, m in arms.items()
                  if m["axis"] == "SPLASH_FLOOR" and p in tot))
    if len(pts) < 2:
        print("not enough SPLASH_FLOOR points yet")
        return
    xs = [d for d, _ in pts]
    ws = [tot[p][0] for _, p in pts]
    ns = [tot[p][1] for _, p in pts]
    ys = [w / n * 100 for w, n in zip(ws, ns)]
    errs = [sd(n) / n * 100 for n in ns]

    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.errorbar(xs, ys, yerr=errs, marker="o", ms=8, lw=2.2, capsize=5,
                color=BASE_C, mfc="white", mew=2, zorder=3)
    ax.axhline(50, color=MUTED, lw=1, ls=":", zorder=1)
    for x, y, w, n in zip(xs, ys, ws, ns):
        ax.annotate(f"{w}/{n}\n{y:.1f}%", (x, y), textcoords="offset points",
                    xytext=(0, 15), ha="center", fontsize=9, color=INK)
    inc = 2000
    if inc in xs:
        ax.annotate("inherited value\n(best measured)", (inc, ys[xs.index(inc)]),
                    textcoords="offset points", xytext=(-14, -46), ha="right",
                    fontsize=8.5, color=MUTED)
    ax.set_xlabel("SPLASH_FLOOR  (chips that must remain after a non-splasher build)")
    ax.set_ylabel(f"win rate over {ns[0]} matched games (%)")
    peak = max(range(len(xs)), key=lambda i: ys[i])
    ax.set_title("Darla — the SPLASH_FLOOR dose response\n"
                 f"an INTERIOR OPTIMUM at the inherited {xs[peak]}: the curve "
                 "rises to it and falls past it.\ncarol bracketed 0/1400/2000 "
                 "in self-play; the untested direction was up, and it is worse.",
                 fontsize=11, loc="left", color=INK, pad=11)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"wrote {out} ({len(pts)} doses)")


if __name__ == "__main__":
    a = load_arms()
    t = collect(a)
    if "darla" not in t:
        sys.exit("no baseline runs found")
    arm_ladder(a, t, WS / "progress" / "arm_ladder.png")
    dose(a, t, WS / "progress" / "splash_floor_dose.png")
