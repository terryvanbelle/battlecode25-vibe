// Play-symmetry audit for the tower-type rule (TRAINING_ALGORITHM.md Phase 0 item 7:
// "any fixed absolute-order decision ... interacts with map geometry to give one side
// a compounding tempo edge").
//
// Maps are guaranteed symmetric. Each team captures the ruins in its own half, so the
// ruins the two teams get are mirror images of each other. If towerTypeFor assigns
// DIFFERENT types to a mirrored ruin pair, the two teams end up with different tower
// mixes on a symmetric map -- a pure, unearned economic asymmetry that has nothing to
// do with either bot's play.
//
// The symmetry is inferred rather than trusted: whichever of the three transforms maps
// the ruin set onto itself is the one in force.
// Usage: java -cp .:<engine-jar> BobSym <dir-of-map25>
import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class BobSym {
    public static void main(String[] args) throws Exception {
        File[] fs = new File(args[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        System.out.println("map,sym,pairs,oldDisagree,newDisagree,oldTeamGap,newTeamGap");
        int n = 0, oldBad = 0, newBad = 0;
        double oldGap = 0, newGap = 0, oldWorst = 0, newWorst = 0, folGap = 0, folWorst = 0;
        int folBad = 0;
        for (File f : fs) {
            byte[] raw = readAll(f);
            GameMap gm;
            try { gm = GameMap.getRootAsGameMap(ByteBuffer.wrap(raw)); } catch (Exception e) { continue; }
            VecTable rt; int W, H;
            try { rt = gm.ruins(); W = gm.size().x(); H = gm.size().y(); } catch (Exception e) { continue; }
            if (rt == null || rt.xsLength() == 0) continue;
            int r = rt.xsLength();
            int[] xs = new int[r], ys = new int[r];
            Set<Long> set = new HashSet<>();
            for (int i = 0; i < r; i++) { xs[i] = rt.xs(i); ys[i] = rt.ys(i); set.add(key(xs[i], ys[i])); }

            // infer which symmetry actually holds for this ruin set
            String sym = null;
            for (int mode = 0; mode < 3 && sym == null; mode++) {
                boolean ok = true;
                for (int i = 0; i < r && ok; i++) {
                    int[] m = mirror(mode, xs[i], ys[i], W, H);
                    if (!set.contains(key(m[0], m[1]))) ok = false;
                }
                if (ok) sym = new String[]{"rot", "horiz", "vert"}[mode];
            }
            if (sym == null) { System.out.println(gm.name() + ",UNRESOLVED,,,,,"); continue; }
            int mode = sym.equals("rot") ? 0 : sym.equals("horiz") ? 1 : 2;

            // count mirrored pairs whose assigned type differs, and each half's money count
            int pairs = 0, oldD = 0, newD = 0, folD = 0;
            int oldA = 0, oldB = 0, newA = 0, newB = 0, folA = 0, folB = 0, halfA = 0, halfB = 0;
            for (int i = 0; i < r; i++) {
                int[] m = mirror(mode, xs[i], ys[i], W, H);
                if (xs[i] == m[0] && ys[i] == m[1]) continue;      // on the axis, shared
                boolean o1 = ((xs[i] + ys[i]) & 1) == 0, o2 = ((m[0] + m[1]) & 1) == 0;
                boolean n1 = (hash(xs[i], ys[i]) & 1) == 0, n2 = (hash(m[0], m[1]) & 1) == 0;
                boolean f1 = (fhash(xs[i], ys[i], W, H) & 1) == 0, f2 = (fhash(m[0], m[1], W, H) & 1) == 0;
                // count each ruin once into "its" half, chosen consistently by the transform
                boolean isA = mode == 0 ? (ys[i] * W + xs[i]) < (m[1] * W + m[0])
                            : mode == 1 ? xs[i] < m[0] : ys[i] < m[1];
                if (isA) { halfA++; if (o1) oldA++; if (n1) newA++; if (f1) folA++; }
                else     { halfB++; if (o1) oldB++; if (n1) newB++; if (f1) folB++; }
                if (isA) { pairs++; if (o1 != o2) oldD++; if (n1 != n2) newD++; if (f1 != f2) folD++; }
            }
            if (pairs == 0 || halfA == 0 || halfB == 0) continue;
            double og = Math.abs(100.0 * oldA / halfA - 100.0 * oldB / halfB);
            double ng = Math.abs(100.0 * newA / halfA - 100.0 * newB / halfB);
            oldGap += og; newGap += ng;
            oldWorst = Math.max(oldWorst, og); newWorst = Math.max(newWorst, ng);
            double fg = Math.abs(100.0 * folA / halfA - 100.0 * folB / halfB);
            folGap += fg; folWorst = Math.max(folWorst, fg);
            if (folD > 0) folBad++;
            if (oldD > 0) oldBad++;
            if (newD > 0) newBad++;
            n++;
            System.out.printf("%s,%s,%d,%d,%d,%.0f,%.0f%n", gm.name(), sym, pairs, oldD, newD, og, ng);
        }
        System.out.println();
        System.out.printf("maps=%d%n", n);
        System.out.printf("maps with ANY mirrored pair assigned different types: old %d (%.0f%%)  new %d (%.0f%%)%n",
            oldBad, 100.0 * oldBad / n, newBad, 100.0 * newBad / n);
        System.out.printf("mean money%%-gap between the two halves: old %.1f pts  new %.1f pts%n", oldGap / n, newGap / n);
        System.out.printf("worst gap:                              old %.0f pts  new %.0f pts%n", oldWorst, newWorst);
        System.out.printf("FOLDED rule: maps with a mismatched mirrored pair %d (%.0f%%)  mean gap %.1f  worst %.0f%n",
            folBad, 100.0 * folBad / n, folGap / n, folWorst);
    }

    static int[] mirror(int mode, int x, int y, int W, int H) {
        if (mode == 0) return new int[]{W - 1 - x, H - 1 - y};
        if (mode == 1) return new int[]{W - 1 - x, y};
        return new int[]{x, H - 1 - y};
    }
    static long key(int x, int y) { return ((long) x << 20) | y; }
    static int hash(int x, int y) {
        int h = x * 0x27D4EB2D + y * 0x165667B1;
        h ^= h >>> 15; h *= 0x2545F491; h ^= h >>> 13;
        return h;
    }
    static byte[] readAll(File f) throws IOException {
        try (BufferedInputStream bi = new BufferedInputStream(new FileInputStream(f))) {
            bi.mark(2); int b1 = bi.read(), b2 = bi.read(); bi.reset();
            InputStream in = (b1 == 0x1f && b2 == 0x8b) ? new GZIPInputStream(bi) : bi;
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] buf = new byte[1 << 16]; int k;
            while ((k = in.read(buf)) > 0) bos.write(buf, 0, k);
            return bos.toByteArray();
        }
    }
}
