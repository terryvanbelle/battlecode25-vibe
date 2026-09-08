#!/usr/bin/env python3
"""Iteration 37's pre-registered manipulation check, paired within each game.

Both bots play in the same replay, so map, round count and opponent are held fixed and every
game is one paired observation. Reads through dumpcache.sh, so a dump is fetched from the VM
once and every later question about the same game is free.

Emits, per game and pooled:
  * realized soldier share  (direct SPAWN counts -- no post-turn-state bias)
  * mean tower count from round 800 onward  (the pre-registered second condition: the mix
    changing without towers moving means the ratchet did not unlock)

  paircheck.py <candidate-name> <replay.bc25> [...]
"""
import re, subprocess, sys, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "dumpcache.sh")
TOWER_FROM = 800

def dump(path):
    out = subprocess.run([CACHE, path, "--every", "200"], capture_output=True, text=True)
    return out.stdout.strip()

def parse(txt_path):
    n = {}
    spawn = {1: [0,0,0], 2: [0,0,0]}
    towers = {1: [], 2: []}
    cov = {1: [], 2: []}
    for line in open(txt_path):
        if line.startswith("=== GameHeader"):
            n[1] = re.search(r"team1=(\S+)", line).group(1)
            n[2] = re.search(r"team2=(\S+)", line).group(1)
        if " | T" not in line:
            continue
        rm = re.match(r"\s*round\s+(\d+)", line)
        rnd = int(rm.group(1)) if rm else 0
        for blk in line.split("| ")[1:]:
            t = re.match(r"T(\d+)\s", blk)
            if not t: continue
            tid = int(t.group(1))
            g = lambda p: int(re.search(p, blk).group(1)) if re.search(p, blk) else 0
            spawn[tid][0] += g(r"\+sold(\d+)"); spawn[tid][1] += g(r"\+mop(\d+)"); spawn[tid][2] += g(r"\+spl(\d+)")
            if rnd >= TOWER_FROM: towers[tid].append(g(r"\btw(\d+)"))
            cov[tid].append((rnd, g(r"cov(\d+)m")))
    return n, spawn, towers, cov

CAND = sys.argv[1]
rows = []
for r in sys.argv[2:]:
    p = dump(r)
    if not p or not os.path.exists(p):
        print(f"  !! dump failed: {r}", file=sys.stderr); continue
    n, sp, tw, cv = parse(p)
    if CAND not in n.values():
        print(f"  !! {CAND} not in {r}", file=sys.stderr); continue
    ci = 1 if n[1] == CAND else 2; ii = 3 - ci
    fin = lambda v: v[-1][1] if v else 0
    rows.append((os.path.basename(r), sp[ci], sp[ii],
                 statistics.mean(tw[ci]) if tw[ci] else 0.0,
                 statistics.mean(tw[ii]) if tw[ii] else 0.0,
                 fin(cv[ci]), fin(cv[ii])))

def share(s):
    t = sum(s); return 100.0*s[0]/t if t else 0.0

print(f"{'game':30}{'cand s/m/p':>15}{'sh%':>6}{'inc s/m/p':>15}{'sh%':>6}{'cTw':>6}{'iTw':>6}{'cCov':>7}{'iCov':>7}")
for g, c, i, ct, it_, cc, ic in rows:
    print(f"{g[:30]:30}{'/'.join(map(str,c)):>15}{share(c):6.1f}{'/'.join(map(str,i)):>15}{share(i):6.1f}{ct:6.1f}{it_:6.1f}{cc:7d}{ic:7d}")

if rows:
    cs = [sum(x) for x in zip(*[r[1] for r in rows])]
    is_ = [sum(x) for x in zip(*[r[2] for r in rows])]
    dtw = [r[3]-r[4] for r in rows]
    print(f"\nPOOLED n={len(rows)}")
    print(f"  candidate mix {cs}  soldier share {share(cs):.1f}%   [pre-registered: >= 60%]")
    print(f"  incumbent mix {is_}  soldier share {share(is_):.1f}%")
    print(f"  mean towers from round {TOWER_FROM}: candidate {statistics.mean([r[3] for r in rows]):.2f}"
          f"  incumbent {statistics.mean([r[4] for r in rows]):.2f}"
          f"  delta {statistics.mean(dtw):+.2f}   [pre-registered: strictly > 0]")
    print(f"  games where candidate had more towers: {sum(1 for d in dtw if d>0)}/{len(dtw)}")
    dc = [r[5]-r[6] for r in rows]
    print(f"  PRICE -- final coverage: candidate {statistics.mean([r[5] for r in rows]):.0f}"
          f"  incumbent {statistics.mean([r[6] for r in rows]):.0f}"
          f"  delta {statistics.mean(dc):+.0f}   [registered as the PRICE: fewer splashers = less"
          f" direct paint throughput; benefit is towers]")
    print(f"  games where candidate had more coverage: {sum(1 for d in dc if d>0)}/{len(dc)}")
