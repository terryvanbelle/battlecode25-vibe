#!/usr/bin/env python3
"""B0 -- vision-redundancy headroom, the R1 pre-check's first and cheapest gate.

Reads `replay-dump.sh --map-at` ASCII arena frames on stdin and reports, per team
per frame, how much of what the team's soldiers see is seen by MORE THAN ONE of
them.  No bot code, no games, no build: the frames are already on disk.

TWO NUMBERS, and they are not interchangeable:

  B0  (REGISTERED)  = |union of vision discs| / (n * 69)
      Exactly as pre-registered in TRAINING_LOG.md before any of this ran. 69 is
      the count of tiles with dx^2+dy^2 <= 20.  Its flaw is known and stated here
      rather than fixed silently: a soldier standing near a map edge has part of
      its disc off-board, which this scores as redundancy even though no second
      soldier is involved.  That biases B0 DOWNWARD -- i.e. toward B passing, i.e.
      toward spending the rewrite budget.  The registered bar is judged on it
      anyway, because moving a goalpost after seeing the data is worse than a
      known bias whose direction is declared.

  B0' (CLIP-CORRECTED) = |union| / sum(|disc clipped to the board|)
      Puts the boundary in numerator and denominator alike, so the only thing
      left is soldier-on-soldier overlap.  This is the quantity the mechanism
      could actually recover: no movement rule can win back a tile that is off
      the edge of the map.

Read them together.  B0' is the ceiling on what spacing could recover; B0 is the
number the bar was set on.
"""
import sys, re, collections

VIS = [(dx, dy) for dx in range(-5, 6) for dy in range(-5, 6) if dx*dx + dy*dy <= 20]
assert len(VIS) == 69, len(VIS)

GLYPHS = set(".#o*aAbBtTnNdDsSmMpP")
SOLDIER = {1: "s", 2: "S"}
MOBILE  = {1: set("smp"), 2: set("SMP")}

def frames(lines):
    """Yield (mapname, round, W, H, grid) -- grid[y][x], y=0 at the bottom."""
    mapname, W, H = None, None, None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"=== MatchHeader map=(\S+) (\d+)x(\d+)", ln)
        if m:
            mapname, W, H = m.group(1), int(m.group(2)), int(m.group(3))
            i += 1; continue
        m = re.match(r"=== ARENA round (\d+)\s+(\d+)x(\d+)", ln)
        if m:
            rnd, aw, ah = int(m.group(1)), int(m.group(2)), int(m.group(3))
            # width/height on the ARENA line are authoritative for this frame
            W, H = aw, ah
            rows = {}
            j = i + 1
            while j < len(lines) and not lines[j].startswith("    census"):
                rm = re.match(r"^\s*(\d+) (\S+)$", lines[j])
                if rm:
                    body = rm.group(2)
                    # the column ruler also starts with spaces and a digit; it is
                    # rejected by BOTH the width check and the glyph check, and
                    # needing to pass both is deliberate -- either alone has a
                    # width at which it silently admits the ruler as a map row.
                    if len(body) == W and set(body) <= GLYPHS:
                        rows[int(rm.group(1))] = body
                j += 1
            if len(rows) == H:
                grid = [rows[y] for y in range(H)]
                yield (mapname, rnd, W, H, grid)
            else:
                print(f"!! frame {mapname} r{rnd}: parsed {len(rows)} rows, expected {H}"
                      f" -- SKIPPED, not silently half-counted", file=sys.stderr)
            i = j; continue
        i += 1

def measure(grid, W, H, want):
    """Return (n, union, sum_clipped) for the unit glyphs in `want`."""
    pos = [(x, y) for y in range(H) for x in range(W) if grid[y][x] in want]
    union, tot = set(), 0
    for (x, y) in pos:
        seen = 0
        for dx, dy in VIS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H:
                union.add((nx, ny)); seen += 1
        tot += seen
    return len(pos), len(union), tot

def main():
    lines = [l.rstrip("\n") for l in sys.stdin]
    rows = []
    for (mapname, rnd, W, H, grid) in frames(lines):
        for team in (1, 2):
            n, u, tot = measure(grid, W, H, {SOLDIER[team]})
            nm, um, totm = measure(grid, W, H, MOBILE[team])
            rows.append(dict(map=mapname, rnd=rnd, W=W, H=H, team=team,
                             n=n, union=u, clipped=tot,
                             nm=nm, unionm=um, clippedm=totm))
    if not rows:
        print("!! no frames parsed -- refusing to print a ratio", file=sys.stderr)
        return 1

    print(f"{'map':<14}{'rnd':>5}{'size':>8}{'tm':>3}{'n':>4}"
          f"{'union':>7}{'n*69':>7}{'B0':>7}{'clip':>7}{'B0prime':>9}")
    for r in rows:
        if r["n"] == 0: continue
        b0 = r["union"] / (r["n"] * 69)
        b0p = r["union"] / r["clipped"] if r["clipped"] else float("nan")
        print(f"{r['map']:<14}{r['rnd']:>5}{str(r['W'])+'x'+str(r['H']):>8}"
              f"{r['team']:>3}{r['n']:>4}{r['union']:>7}{r['n']*69:>7}"
              f"{b0:>7.3f}{r['clipped']:>7}{b0p:>9.3f}")

    def agg(rs, key_n, key_u, key_c, label):
        rs = [r for r in rs if r[key_n] > 0]
        if not rs:
            print(f"  {label}: no cells"); return
        N  = sum(r[key_n] for r in rs)
        U  = sum(r[key_u] for r in rs)
        C  = sum(r[key_c] for r in rs)
        # pooled = one big population; mean-of-frames = each frame one vote.
        # Reported together because they answer different questions and a gap
        # between them means the big frames disagree with the small ones.
        pooled  = U / (N * 69)
        pooledp = U / C
        mf  = sum(r[key_u] / (r[key_n] * 69) for r in rs) / len(rs)
        mfp = sum(r[key_u] / r[key_c] for r in rs) / len(rs)
        print(f"  {label:<26} frames={len(rs):>3} units={N:>5}"
              f"  B0 pooled={pooled:.3f} mean-of-frames={mf:.3f}"
              f" | B0' pooled={pooledp:.3f} mean-of-frames={mfp:.3f}")

    print("\n=== AGGREGATE ===")
    agg(rows, "n", "union", "clipped", "soldiers (REGISTERED)")
    agg([r for r in rows if r["n"] >= 3], "n", "union", "clipped", "soldiers, n>=3")
    agg([r for r in rows if r["n"] >= 6], "n", "union", "clipped", "soldiers, n>=6")
    agg(rows, "nm", "unionm", "clippedm", "all mobile (diagnostic)")

    print("\n=== by map size ===")
    for lo, hi, lab in ((0, 30, "small (<30)"), (30, 45, "medium"), (45, 999, "large (>=45)")):
        sub = [r for r in rows if lo <= max(r["W"], r["H"]) < hi]
        agg(sub, "n", "union", "clipped", lab)
    return 0

sys.exit(main())
