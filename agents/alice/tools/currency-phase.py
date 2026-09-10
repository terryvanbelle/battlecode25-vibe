#!/usr/bin/env python3
"""Does the chip/paint anti-correlation close a CLASS, not just one pair?

Measured in ONE PASS: every frame contributes (team chips, tower paint) TOGETHER.
Nothing here is assembled from a chip curve and a paint curve -- that composition is
the error that produced 8.9% where the truth was 1.4%.

The class in question: mechanisms gated on a HIGH team-chip threshold whose output
costs TOWER paint. Chips are a team stock that accumulates; tower paint is a
per-structure stock that depletes. If they move oppositely, such a mechanism is
phase-mismatched by construction -- the currency is only abundant once the thing it
must buy has run out.
"""
import sys, re, statistics

PAT = re.compile(r"(T[12]) \$(\d+) cov\d+m srp\d+ sold\d+ spl\d+ mop\d+ tw(\d+) twPaint(\d+)")

def main():
    t1 = t2 = None; rows = []
    for ln in open(sys.argv[1]):
        m = re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)", ln)
        if m: t1, t2 = m.group(1), m.group(2)
        if "| T1 " not in ln: continue
        rm = re.match(r"round (\d+) \|", ln)
        if not rm: continue
        for g in PAT.finditer(ln):
            who = t1 if g.group(1) == 'T1' else t2
            if 'alice' not in who: continue
            tw = int(g.group(3))
            if tw: rows.append((int(rm.group(1)), int(g.group(2)), int(g.group(4))/tw))
    n = len(rows)
    ch = [c for _, c, _ in rows]; pa = [p for _, _, p in rows]
    mc, mp = statistics.mean(ch), statistics.mean(pa)
    num = sum((c-mc)*(p-mp) for c, p in zip(ch, pa))
    den = (sum((c-mc)**2 for c in ch) * sum((p-mp)**2 for p in pa)) ** 0.5
    print(f"=== chips vs tower paint, {n} frames, measured together ===\n")
    print(f"  correlation(team chips, paint per tower) = {num/den:+.3f}")
    # rank correlation, robust to the chip curve's huge tail
    rc = {v: i for i, v in enumerate(sorted(set(ch)))}
    rp = {v: i for i, v in enumerate(sorted(set(pa)))}
    a = [rc[c] for c in ch]; b = [rp[p] for p in pa]
    ma, mb = statistics.mean(a), statistics.mean(b)
    num2 = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    den2 = (sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b)) ** 0.5
    print(f"  rank correlation (robust to the chip tail)  = {num2/den2:+.3f}\n")
    print(f"  {'chip threshold':>16}{'frames >= C':>13}{'of those, paint>=300':>22}{'JOINT share':>13}")
    for C in (1450, 1850, 3950, 10000, 30000):
        s = [(c, p) for _, c, p in rows if c >= C]
        j = sum(1 for c, p in s if p >= 300)
        print(f"  {C:>16}{100*len(s)/n:>12.1f}%"
              f"{(100*j/len(s) if s else 0):>21.1f}%{100*j/n:>12.1f}%")
    print("\n  and the same, split by phase (chips rise, paint falls):")
    print(f"  {'band':>14}{'mean chips':>12}{'mean paint/tw':>15}{'paint>=300':>12}")
    for lo, hi, lab in ((1,300,"1-300"),(300,600,"300-600"),(600,1200,"600-1200"),(1200,9999,"1200+")):
        s = [(c,p) for r,c,p in rows if lo <= r < hi]
        if not s: continue
        print(f"  {lab:>14}{statistics.mean(c for c,_ in s):>12.0f}"
              f"{statistics.mean(p for _,p in s):>15.1f}"
              f"{100*sum(1 for _,p in s if p>=300)/len(s):>11.1f}%")
    return 0

sys.exit(main())
