#!/usr/bin/env python3
"""Tower-build census over a tournament's replays.

Counts, per (map, side), how many PAINT_TOWER and MONEY_TOWER each team BUILT
(SPAWN events; the 2 'initial' towers are excluded and reported separately),
alongside ruins, winner, win type and round count.

Referent note: this is the ONLY instrument here whose opponents carol did not
produce, so it is the only one that can test a claim of the form "we are worse
than others at X" (doctrine 17).

  towercensus.py <replaydir> <jar> > out.csv
"""
import re, sys, os, subprocess, collections

HDR   = re.compile(r'team1=(\S+)\s+team2=(\S+)')
MHDR  = re.compile(r'map=(\S+) (\d+)x(\d+) symmetry=(\d+) maxRounds=(\d+) walls=(\d+)/(\d+) \([\d.]+%\) ruins=(\d+)')
SPAWN = re.compile(r'^round (\d+) id\d+\((T\d),\w+\) SPAWN id\d+\(T\d,(\w+)\) at')
INIT  = re.compile(r'^  initial id\d+\((T\d),(\w+)\) at')
FOOT  = re.compile(r'winner=(\S+) winType=(\S+) rounds=(\d+)')

def one(path, jar):
    out = subprocess.run(
        ["java", "-classpath", ".:" + jar, "com.google.flatbuffers.ReplayDump",
         path, "--quiet", "--every", "9999"],
        capture_output=True, text=True).stdout
    t1 = t2 = None; mp = None; ruins = w = h = None
    win = wt = rnds = None
    built = collections.defaultdict(collections.Counter)
    init  = collections.defaultdict(collections.Counter)
    for ln in out.splitlines():
        m = HDR.search(ln)
        if m: t1, t2 = m.group(1), m.group(2); continue
        m = MHDR.search(ln)
        if m:
            mp, w, h, ruins = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(8))
            continue
        m = INIT.match(ln)
        if m: init[m.group(1)][m.group(2)] += 1; continue
        m = SPAWN.match(ln)
        if m: built[m.group(2)][m.group(3)] += 1; continue
        m = FOOT.search(ln)
        if m: win, wt, rnds = m.group(1), m.group(2), int(m.group(3))
    if mp is None or win is None: return None
    return dict(map=mp, w=w, h=h, ruins=ruins, t1=t1, t2=t2,
                winner=win, wintype=wt, rounds=rnds,
                t1p=built["T1"]["PAINT_TOWER"], t1m=built["T1"]["MONEY_TOWER"],
                t2p=built["T2"]["PAINT_TOWER"], t2m=built["T2"]["MONEY_TOWER"],
                t1i=sum(init["T1"].values()), t2i=sum(init["T2"].values()))

def main(d, jar):
    cols = ["map","w","h","ruins","t1","t2","winner","wintype","rounds",
            "t1p","t1m","t2p","t2m","t1i","t2i"]
    print(",".join(cols))
    for f in sorted(os.listdir(d)):
        if not f.endswith(".bc25"): continue
        r = one(os.path.join(d, f), jar)
        if r: print(",".join(str(r[c]) for c in cols)); sys.stdout.flush()

main(sys.argv[1], sys.argv[2])
