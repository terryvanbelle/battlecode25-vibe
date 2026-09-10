#!/usr/bin/env python3
"""The tail-precondition check, scored against the candidate list committed FIRST.

Candidates were fixed in e9b6614, derived from the spawn decision in src/alice and
not from these replays, because n=3 against an unbounded candidate set always finds
something. Every candidate is scored as PREVALENCE-IN-TAIL vs PREVALENCE-IN-REST.

  C1 mopper SHARE of spawns elevated in tail (baseline ~23-25%)  -> PASS if >40%
  C2 total spawn volume elevated                                  -> KILL branch
  C3 tower paint in [100,200) more often                          -> guard-firing window
  C4 game length elevated                                         -> KILL branch
  C5 tower count elevated                                         -> KILL branch
"""
import sys, re, statistics

PAT = re.compile(r"(T[12]) \$\d+ cov\d+m srp\d+ sold\d+ spl\d+ mop\d+ tw(\d+) twPaint(\d+) "
                 r"acts\[p(\d+) u\d+ a\d+ s\d+ m\d+\] \+sold(\d+) \+mop(\d+) \+spl(\d+)")

def main():
    t1 = t2 = None; cur = None; g = {}
    for ln in open(sys.argv[1]):
        m = re.match(r"=== GameHeader\s+team1=(\S+)\s+team2=(\S+)", ln)
        if m: t1, t2 = m.group(1), m.group(2)
        m = re.match(r"=== MatchHeader map=(\S+) ", ln)
        if m:
            cur = m.group(1)
            g[cur] = dict(mop=0, sol=0, spl=0, rounds=0, tw=0, twp=0, n=0, poor=0, p=0)
        if "| T1 " not in ln or cur is None: continue
        rm = re.match(r"round (\d+) \|", ln)
        if rm: g[cur]['rounds'] = max(g[cur]['rounds'], int(rm.group(1)))
        for mm in PAT.finditer(ln):
            f = mm.groups(); who = t1 if f[0] == 'T1' else t2
            if 'alice' not in who: continue
            d = g[cur]
            tw, twp = int(f[1]), int(f[2])
            d['p'] += int(f[3]); d['sol'] += int(f[4]); d['mop'] += int(f[5]); d['spl'] += int(f[6])
            if tw:
                per = twp / tw
                d['tw'] += tw; d['twp'] += per; d['n'] += 1
                if 100 <= per < 200: d['poor'] += 1

    rows = []
    for mp, d in g.items():
        tot = d['sol'] + d['mop'] + d['spl']
        if tot == 0 or d['n'] == 0: continue
        rows.append(dict(map=mp, mop=d['mop'], tot=tot, share=d['mop']/tot,
                         rounds=d['rounds'], tw=d['tw']/d['n'], twp=d['twp']/d['n'],
                         poor=d['poor']/d['n'], p=d['p']))
    rows.sort(key=lambda r: -r['mop'])
    tail, rest = rows[:3], rows[3:]

    print(f"=== tail-precondition check: {len(rows)} games, tail = the 3 highest mopper counts ===\n")
    print(f"  {'map':<16}{'moppers':>9}{'spawns':>8}{'SHARE':>8}{'rounds':>8}"
          f"{'towers':>8}{'paint/tw':>10}{'in[100,200)':>12}")
    for r in rows:
        mark = "  <- TAIL" if r in tail else ""
        print(f"  {r['map']:<16}{r['mop']:>9}{r['tot']:>8}{100*r['share']:>7.1f}%"
              f"{r['rounds']:>8}{r['tw']:>8.2f}{r['twp']:>10.1f}{100*r['poor']:>11.1f}%{mark}")

    def cmp(lab, key, fmt="{:.1f}"):
        a = statistics.mean(x[key] for x in tail); b = statistics.mean(x[key] for x in rest)
        rat = a/b if b else float('inf')
        print(f"  {lab:<34} tail {fmt.format(a):>9}   rest {fmt.format(b):>9}   ratio {rat:>5.2f}x")
        return rat
    print("\n=== PREVALENCE IN TAIL vs REST, per the committed candidate list ===")
    c1 = cmp("C1  mopper SHARE of spawns", 'share', "{:.3f}")
    c2 = cmp("C2  total spawns", 'tot')
    c3 = cmp("C3  frames with tower paint 100-200", 'poor', "{:.3f}")
    c4 = cmp("C4  game length (rounds)", 'rounds')
    c5 = cmp("C5  mean towers", 'tw', "{:.2f}")
    ts = statistics.mean(x['share'] for x in tail)
    print(f"\n  registered PASS: C1 tail share > 40%.  measured tail share = {100*ts:.1f}%")
    print("  VERDICT: " + ("**PASS -- the guard is failing**" if ts > 0.40 else
                           "**KILL -- the tail is VOLUME, not a mopper pathology**"))
    print(f"\n  reading: mopper count = share x volume. Share is {c1:.2f}x in the tail while")
    print(f"  volume is {c2:.2f}x, so the tail's mopper count is driven by {'SHARE' if c1>c2 else 'VOLUME'}.")
    return 0

sys.exit(main())
