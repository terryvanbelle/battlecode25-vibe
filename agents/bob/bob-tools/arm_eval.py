#!/usr/bin/env python3
"""Evaluate a multi-arm gauntlet run: per-arm score vs the reference, sweeps,
splits, and the map-size breakdown that iteration 21 pre-registered.

Usage: arm_eval.py <run-dir> [jar]
SIGN CONVENTION -- read this before quoting a number. `bot_result` in
results.csv is the REFERENCE bot's result, so this tool inverts it and every
score printed is the ARM's. TRAINING_LOG tables written before 2026-09-08 print
the *reference's* score instead, so the same game appears as 17/50 there and
33/50 here. Both are right; they answer different questions. Validated against
run 20260908-000848, where it reproduces the logged iteration-20 dose curve
exactly (mirror +0 se 0 / s2 +8, 8 swept 0 against / s3 +4, 7 swept 3 against).

`sd` is a plain binomial se over GAMES (sqrt(n)/2). It is NOT the statistic the
older log rows quote, which is finer-grained; the accept gate is registered in
games for exactly that reason. A run's map sample is shared by all arms, so
cross-arm comparison within one run is exact.
"""
import csv, sys, collections, zipfile, struct, gzip, glob, os, math

run = sys.argv[1]
jar = sys.argv[2] if len(sys.argv) > 2 else (
    glob.glob(os.path.expanduser('~/.gradle/**/battlecode25-java-*.jar'), recursive=True)
    + glob.glob('/tmp/**/battlecode25-java-*.jar', recursive=True))[0]

z = zipfile.ZipFile(jar)
ld = lambda n: (lambda d: gzip.decompress(d) if d[:2] == b'\x1f\x8b' else d)(z.read(n))
u32 = lambda d, p: struct.unpack_from('<I', d, p)[0]
i32 = lambda d, p: struct.unpack_from('<i', d, p)[0]
u16 = lambda d, p: struct.unpack_from('<H', d, p)[0]
def slots(d, p):
    vt = p - i32(d, p)
    return [u16(d, vt + 4 + 2 * i) for i in range((u16(d, vt) - 4) // 2)]
area = {}
for n in (x for x in z.namelist() if x.endswith('.map25')):
    d = ld(n); r = u32(d, 0); s = slots(d, r)
    area[n.split('/')[-1][:-6]] = u32(d, r + s[1]) * u32(d, r + s[1] + 4)

rows = list(csv.DictReader(open(os.path.join(run, 'results.csv'))))
by = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    # bot_result is the REFERENCE bot's result; the arm's is the opposite
    by[r['opponent']][r['map']].append(r['bot_result'] != 'win')

print(f"run {os.path.basename(run)}   scores are the ARM's, vs the reference bot\n")
hdr = f"{'arm':<12}{'score':>9}{'vs null':>9}{'sd':>7}{'swept':>7}{'swept-against':>15}{'split':>7}"
print(hdr); print('-' * len(hdr))
null = None
summary = {}
for arm in sorted(by):
    maps = by[arm]
    wins = sum(sum(v) for v in maps.values()); games = sum(len(v) for v in maps.values())
    sw = sum(1 for v in maps.values() if len(v) == 2 and all(v))
    sa = sum(1 for v in maps.values() if len(v) == 2 and not any(v))
    sp = sum(1 for v in maps.values() if len(v) == 2 and any(v) and not all(v))
    se = math.sqrt(games) / 2
    print(f"{arm:<12}{wins:>4}/{games:<4}{wins-games/2:>+9.0f}{(wins-games/2)/se:>+7.2f}"
          f"{sw:>7}{sa:>15}{sp:>7}")
    summary[arm] = (wins, games, maps)

print("\nmap-size breakdown (iteration 21 pre-registered: gain concentrates on LARGE maps)")
hdr2 = f"{'arm':<12}{'small <2500':>16}{'large >=2500':>16}{'gain small':>12}{'gain large':>12}"
print(hdr2); print('-' * len(hdr2))
base = {}
for arm in sorted(summary):
    _, _, maps = summary[arm]
    agg = {'small': [0, 0], 'large': [0, 0]}
    for m, v in maps.items():
        b = 'small' if area.get(m, 0) < 2500 else 'large'
        agg[b][0] += sum(v); agg[b][1] += len(v)
    if not base:
        base = agg  # first arm alphabetically is the null (bob_m0)
    gs = agg['small'][0] - base['small'][0]
    gl = agg['large'][0] - base['large'][0]
    print(f"{arm:<12}{agg['small'][0]:>7}/{agg['small'][1]:<8}{agg['large'][0]:>7}/{agg['large'][1]:<8}"
          f"{gs:>+12}{gl:>+12}")
print("\n(gains are games vs the FIRST arm listed, which must be the identity control)")
