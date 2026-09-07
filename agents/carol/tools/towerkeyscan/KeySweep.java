package com.google.flatbuffers;

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

/**
 * Carol-private: score candidate replacement keys for towerTypeFor.
 *
 * Every candidate is a function of (mx, my) = (min(x,w-1-x), min(y,h-1-y)) ONLY, so it is
 * invariant under every map symmetry and both teams assign the same type to mirrored ruins --
 * the play-symmetry property the current key was chosen for (Phase 0 item 7). Reported per key:
 *   degen   maps where every ruin lands in one class  (the bug being fixed; current key = 6)
 *   ratio   corpus-wide money:paint (current = 447:927, about 1:2.07)
 *   churn   ruins whose class CHANGES vs the current key -- this is the PRICE, since every
 *           changed ruin perturbs a map that was not broken.
 */
public class KeySweep {
    static byte[] read(File f) throws IOException {
        byte[] raw = Files.readAllBytes(f.toPath());
        if (raw.length > 2 && (raw[0] & 0xff) == 0x1f && (raw[1] & 0xff) == 0x8b) {
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            try (GZIPInputStream gz = new GZIPInputStream(new ByteArrayInputStream(raw))) {
                byte[] b = new byte[8192]; int n;
                while ((n = gz.read(b)) > 0) bo.write(b, 0, n);
            }
            return bo.toByteArray();
        }
        return raw;
    }
    interface Key { boolean money(int mx, int my); }
    public static void main(String[] a) throws Exception {
        File[] fs = new File(a[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        LinkedHashMap<String, Key> keys = new LinkedHashMap<>();
        keys.put("CURRENT (mx+my)%3==0",  (mx,my) -> (mx+my) % 3 == 0);
        keys.put("(mx+my)%2==0",          (mx,my) -> (mx+my) % 2 == 0);
        keys.put("(mx+my)%4==0",          (mx,my) -> (mx+my) % 4 == 0);
        keys.put("(mx*my)%3==0",          (mx,my) -> (mx*my) % 3 == 0);
        keys.put("(mx+2*my)%3==0",        (mx,my) -> (mx+2*my) % 3 == 0);
        keys.put("mx%3==0",               (mx,my) -> mx % 3 == 0);
        keys.put("my%3==0",               (mx,my) -> my % 3 == 0);
        keys.put("(mx%3==0)&&(my%3==0)",  (mx,my) -> mx % 3 == 0 && my % 3 == 0);
        keys.put("(mx%2+my%2)==0",        (mx,my) -> (mx % 2 + my % 2) == 0);
        keys.put("(mx*3+my)%4==0",        (mx,my) -> (mx*3+my) % 4 == 0);
        keys.put("(mx+my)%5<2",           (mx,my) -> (mx+my) % 5 < 2);

        List<int[]> ruins = new ArrayList<>();   // mx, my, mapIndex
        List<String> names = new ArrayList<>();
        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            VecTable r = map.ruins();
            int n = r == null ? 0 : r.xsLength();
            int w = map.size().x(), h = map.size().y();
            int mi = names.size(); names.add(map.name());
            for (int i = 0; i < n; i++) {
                int x = r.xs(i), y = r.ys(i);
                ruins.add(new int[]{Math.min(x, w-1-x), Math.min(y, h-1-y), mi});
            }
        }
        Key cur = keys.get("CURRENT (mx+my)%3==0");
        System.out.printf("%-24s %6s %14s %8s   %s%n", "key", "degen", "money:paint", "churn", "degenerate maps");
        for (Map.Entry<String, Key> e : keys.entrySet()) {
            int[] m = new int[names.size()], p = new int[names.size()];
            int money = 0, paint = 0, churn = 0;
            for (int[] r : ruins) {
                boolean isM = e.getValue().money(r[0], r[1]);
                if (isM) { m[r[2]]++; money++; } else { p[r[2]]++; paint++; }
                if (isM != cur.money(r[0], r[1])) churn++;
            }
            List<String> bad = new ArrayList<>();
            for (int i = 0; i < names.size(); i++) if (m[i]+p[i] > 0 && (m[i]==0 || p[i]==0)) bad.add(names.get(i));
            System.out.printf("%-24s %6d %14s %7.1f%%   %s%n", e.getKey(), bad.size(),
                    money + ":" + paint, 100.0*churn/ruins.size(),
                    bad.size() <= 6 ? String.join(",", bad) : bad.size()+" maps");
        }
    }
}
