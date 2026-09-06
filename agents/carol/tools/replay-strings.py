#!/usr/bin/env python3
"""Extract printable strings (indicator strings etc.) from a .bc25 replay.

Usage: replay-strings.py <replay.bc25> [regex-filter]
Also: replay-strings.py --hash <replay.bc25>   -> sha256 of decompressed content
      (byte-identical content == byte-identical game; gzip wrapper carries a timestamp)
"""
import gzip, hashlib, re, sys

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return 1
    if args[0] == '--hash':
        for p in args[1:]:
            d = gzip.open(p, 'rb').read()
            print(hashlib.sha256(d).hexdigest(), len(d), p)
        return 0
    path = args[0]
    flt = re.compile(args[1].encode()) if len(args) > 1 else None
    d = gzip.open(path, 'rb').read()
    for m in re.finditer(rb'[ -~]{4,}', d):
        s = m.group()
        if flt is None or flt.search(s):
            sys.stdout.write(s.decode() + '\n')
    return 0

if __name__ == '__main__':
    sys.exit(main())
