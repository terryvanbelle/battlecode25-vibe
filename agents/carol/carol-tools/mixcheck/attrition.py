#!/usr/bin/env python3
"""Where carol's units GO: death cause and splasher action utilisation, vs map area.

Two ceilings make these readable rather than relative:
  * splasher fire rate -- an attack adds +50 action cooldown falling 10/turn, so at most
    one shot per 5 rounds = 0.2 shots per splasher per round. Exact, from the engine.
  * starvation share -- ReplayDump classifies a death as starved when the robot's last
    observed paint was <= 0. A starved unit is one the bot walked to death; a killed one
    is the opponent's doing. The split says which problem attrition is.

NOT reported: any per-soldier rate from acts[p...]. `p` counts painted TILES and a splasher
paints ~10 per shot, so p/soldier is not a soldier statistic at all. Found by noticing p707
on a round where the team fielded zero soldiers.
"""
import re, sys
from collections import defaultdict

CEIL = 0.2

agg = defaultdict(lambda: [0,0,0,0,0,0,0])   # splTurns splashes died starved soldTurns xfer covLast
for path in sys.argv[1:]:
    names, prev, area, mapname = {}, 0, None, "?"
    for line in open(path):
        if line.startswith("=== GameHeader"):
            names[1] = re.search(r"team1=(\S+)", line).group(1)
            names[2] = re.search(r"team2=(\S+)", line).group(1)
        m = re.search(r"map=(\S+)\s+(\d+)x(\d+)", line)
        if m: mapname, area = m.group(1), int(m.group(2))*int(m.group(3))
        if " | T" not in line: continue
        rm = re.match(r"\s*round\s+(\d+)", line)
        if not rm: continue
        rnd = int(rm.group(1)); stride = rnd - prev; prev = rnd
        if stride <= 0 or rnd < 50: continue
        for blk in line.split("| ")[1:]:
            t = re.match(r"T(\d+)\s", blk)
            if not t: continue
            g = lambda p: int(re.search(p, blk).group(1)) if re.search(p, blk) else 0
            a = agg[(names[int(t.group(1))], mapname, area)]
            a[0] += g(r"\bspl(\d+)") * stride;  a[1] += g(r"\bs(\d+) m\d+\]")
            a[2] += g(r"\bdied(\d+)");          a[3] += g(r"\bstarved(\d+)")
            a[4] += g(r"\bsold(\d+)") * stride; a[5] += g(r"\bxfer(\d+)")
            a[6]  = g(r"cov(\d+)m")

print(f"{'map':<14}{'area':>6} {'team':<16}{'util%':>7}{'died':>6}{'starv':>6}{'starv%':>7}"
      f"{'sold~':>7}{'spl~':>6}{'xfer':>6}{'cov':>6}")
bands = defaultdict(lambda: [0,0,0,0,0,0])
for (name, mapname, area), a in sorted(agg.items(), key=lambda x: x[0][2]):
    if not name.startswith("carol"): continue
    util = 100*a[1]/(a[0]*CEIL) if a[0] else float('nan')
    stv  = 100*a[3]/a[2] if a[2] else float('nan')
    print(f"{mapname:<14}{area:>6} {name:<16}{util:>7.1f}{a[2]:>6}{a[3]:>6}{stv:>7.1f}"
          f"{a[4]/1950:>7.1f}{a[0]/1950:>6.1f}{a[5]:>6}{a[6]:>6}")
    b = bands["large" if area >= 2000 else "small"]
    for i,v in enumerate([a[0],a[1],a[2],a[3],a[4],a[5]]): b[i] += v
print()
for k, b in bands.items():
    print(f"{k:<6} splasher util {100*b[1]/(b[0]*CEIL):5.1f}%   "
          f"starvation share of deaths {100*b[3]/b[2]:5.1f}%  ({b[3]}/{b[2]})   "
          f"mean sold {b[4]/1950:5.1f}  spl {b[0]/1950:5.1f}  xfer {b[5]}")
