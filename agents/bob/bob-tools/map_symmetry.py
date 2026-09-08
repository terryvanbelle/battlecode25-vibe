import zipfile, struct, gzip
import sys, glob, os
JAR = sys.argv[1] if len(sys.argv) > 1 else (glob.glob(os.path.expanduser('~/.gradle/**/battlecode25-java-*.jar'), recursive=True) + ['battlecode25-java-3.1.0.jar'])[0]
z=zipfile.ZipFile(JAR)
def load(n):
    d=z.read(n)
    return gzip.decompress(d) if d[:2]==b'\x1f\x8b' else d
u32=lambda d,p: struct.unpack_from('<I',d,p)[0]
i32=lambda d,p: struct.unpack_from('<i',d,p)[0]
u16=lambda d,p: struct.unpack_from('<H',d,p)[0]
def slots(d,p):
    vt=p-i32(d,p); return [u16(d,vt+4+2*i) for i in range((u16(d,vt)-4)//2)]
def vec(d,root,s,i):
    p=root+s[i]; t=p+u32(d,p); return u32(d,t), t+4

names=sorted(n for n in z.namelist() if n.endswith('.map25'))
rows=[]
for n in names:
    d=load(n); root=u32(d,0); s=slots(d,root)
    W=u32(d,root+s[1]); H=u32(d,root+s[1]+4)
    ln,off=vec(d,root,s,5)
    assert ln==W*H, (n,ln,W,H)
    g=d[off:off+ln]
    walls=sum(1 for b in g if b)
    idx=lambda x,y: y*W+x            # assume row-major, y outer
    vr = all(g[idx(x,y)]==g[idx(W-1-x,y)] for y in range(H) for x in range(W))
    hr = all(g[idx(x,y)]==g[idx(x,H-1-y)] for y in range(H) for x in range(W))
    rot= all(g[idx(x,y)]==g[idx(W-1-x,H-1-y)] for y in range(H) for x in range(W))
    rows.append((n.split('/')[-1][:-6],W,H,walls,100.0*walls/(W*H),vr,hr,rot))
print(f"{'map':<22}{'dims':>9}{'walls':>7}{'wall%':>7}   vert horz rot180")
none=0
for r in rows:
    tag=lambda b:' Y ' if b else ' . '
    if not (r[5] or r[6] or r[7]): none+=1
    print(f"{r[0]:<22}{r[1]:>4}x{r[2]:<4}{r[3]:>7}{r[4]:>7.1f}   {tag(r[5])}{tag(r[6])}{tag(r[7])}")
print(f"\nmaps={len(rows)}  with NO symmetry under any of the three: {none}")
import collections
c=collections.Counter((r[5],r[6],r[7]) for r in rows)
print("(vert,horz,rot) ->", dict(c))
