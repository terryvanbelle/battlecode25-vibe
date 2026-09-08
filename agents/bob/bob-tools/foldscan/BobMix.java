package com.google.flatbuffers;

// Iteration 23 offline design check (bob). Scores candidate tower-type rules over all 75
// official maps WITHOUT playing a game, on the four quantities this lineage has measured
// prices for:
//   money share      -- the thing the chip-surplus evidence says is too high (53.3% today)
//   all-one-type     -- maps where the rule yields a single type (catastrophe dimension)
//   spread           -- sd of per-map share around the RULE'S OWN mean. This is the
//                       n/2-independent-draws penalty; deviation-from-50 is the wrong
//                       measure once the target share is not 50.
//   mirror mismatch  -- mirrored ruin pairs given opposite types (iteration 12's quantity)
//
// Rule family: parity picks MONEY as today, then a FOLDED (hence exactly symmetric)
// selector flips a fraction of those MONEY ruins to PAINT. The flip fraction is the dose,
// and flip=0 must reproduce the incumbent exactly.

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class BobMix {
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

    // mask 0 = no flip (incumbent); 1 = flip half the money ruins; 3 = flip a quarter.
    static boolean isMoney(int x, int y, int W, int H, int mask) {
        if (((x + y) & 1) != 0) return false;                 // parity says PAINT
        if (mask == 0) return true;
        int a = Math.min(x, W - 1 - x), b = Math.min(y, H - 1 - y);
        return ((a * 3 + b * 5) & mask) != 0;                 // folded => exactly symmetric
    }

    public static void main(String[] args) throws Exception {
        File[] fs = new File(args[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        int[] masks = {0, 15, 7, 3, 1};
        String[] names = {"parity (incumbent)", "parity, mask 15", "parity, mask 7", "parity, mask 3", "parity, mask 1"};
        List<int[]> maps = new ArrayList<>();       // W,H
        List<int[][]> ruins = new ArrayList<>();    // xs,ys
        List<boolean[]> mir = new ArrayList<>();    // has a mirror partner under inferred sym
        List<int[][]> mirloc = new ArrayList<>();

        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            int W = map.size().x(), H = map.size().y();
            VecTable r = map.ruins();
            int n = r == null ? 0 : r.xsLength();
            if (n == 0) continue;
            int[] xs = new int[n], ys = new int[n];
            Set<Long> set = new HashSet<>();
            for (int i = 0; i < n; i++) { xs[i] = r.xs(i); ys[i] = r.ys(i); set.add(xs[i] * 1000L + ys[i]); }
            boolean fx = true, fy = true, rot = true;
            for (int i = 0; i < n; i++) {
                if (!set.contains((W - 1 - xs[i]) * 1000L + ys[i])) fx = false;
                if (!set.contains(xs[i] * 1000L + (H - 1 - ys[i]))) fy = false;
                if (!set.contains((W - 1 - xs[i]) * 1000L + (H - 1 - ys[i]))) rot = false;
            }
            int[][] ml = new int[n][2];
            for (int i = 0; i < n; i++) {
                int mx = xs[i], my = ys[i];
                if (fx) mx = W - 1 - xs[i];
                else if (fy) my = H - 1 - ys[i];
                else if (rot) { mx = W - 1 - xs[i]; my = H - 1 - ys[i]; }
                ml[i][0] = mx; ml[i][1] = my;
            }
            maps.add(new int[]{W, H});
            ruins.add(new int[][]{xs, ys});
            mirloc.add(ml);
        }

        System.out.println(String.format("%-22s %8s %8s %8s %10s", "rule", "money%", "allOne", "spread", "mismatch%"));
        for (int k = 0; k < masks.length; k++) {
            int mask = masks[k];
            int tot = 0, money = 0, allOne = 0, mis = 0, pairs = 0;
            List<Double> shares = new ArrayList<>();
            for (int m = 0; m < maps.size(); m++) {
                int W = maps.get(m)[0], H = maps.get(m)[1];
                int[] xs = ruins.get(m)[0], ys = ruins.get(m)[1];
                int[][] ml = mirloc.get(m);
                int n = xs.length, mo = 0;
                for (int i = 0; i < n; i++) {
                    boolean a = isMoney(xs[i], ys[i], W, H, mask);
                    if (a) mo++;
                    boolean b = isMoney(ml[i][0], ml[i][1], W, H, mask);
                    pairs++;
                    if (a != b) mis++;
                }
                tot += n; money += mo;
                if (mo == 0 || mo == n) allOne++;
                shares.add(100.0 * mo / n);
            }
            double mean = shares.stream().mapToDouble(Double::doubleValue).average().orElse(0);
            double var = shares.stream().mapToDouble(s -> (s - mean) * (s - mean)).average().orElse(0);
            System.out.println(String.format("%-22s %7.1f%% %8d %8.1f %9.1f%%",
                    names[k], 100.0 * money / tot, allOne, Math.sqrt(var), 100.0 * mis / pairs));
        }
    }
}
