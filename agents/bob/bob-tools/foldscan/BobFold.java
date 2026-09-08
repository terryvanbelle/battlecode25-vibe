package com.google.flatbuffers;

// Iteration 22 pre-check (bob). For every official map, compare two tower-type rules:
//   PLAIN  ((x+y)&1)==0 -> MONEY          -- the accepted iteration-12 rule
//   FOLD   ((min(x,W-1-x)+min(y,H-1-y))&1)==0 -> MONEY
// and report, per map: money share, all-one-type maps, and MIRROR MISMATCH -- the
// fraction of mirrored ruin pairs that get OPPOSITE types under the map's own symmetry.
// Mirror mismatch is the quantity iteration 12 was accepted for reducing (+26 points).

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class BobFold {
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
    static boolean plain(int x, int y, int W, int H) { return ((x + y) & 1) == 0; }
    static boolean fold(int x, int y, int W, int H) {
        return ((Math.min(x, W - 1 - x) + Math.min(y, H - 1 - y)) & 1) == 0;
    }
    public static void main(String[] a) throws Exception {
        File[] fs = new File(a[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        int nMaps = 0, plainAllOne = 0, foldAllOne = 0;
        int plainMisTot = 0, foldMisTot = 0, pairsTot = 0;
        int plainMoney = 0, foldMoney = 0, ruinsTot = 0;
        int plainBadMaps = 0, foldBadMaps = 0;
        System.out.println(String.format("%-22s %-9s %-6s  %-13s  %-13s",
                "map", "dims", "ruins", "PLAIN m/allOne/mis", "FOLD m/allOne/mis"));
        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            int W = map.size().x(), H = map.size().y();
            VecTable r = map.ruins();
            int n = r == null ? 0 : r.xsLength();
            if (n == 0) continue;
            int[] xs = new int[n], ys = new int[n];
            Set<Long> set = new HashSet<>();
            for (int i = 0; i < n; i++) { xs[i] = r.xs(i); ys[i] = r.ys(i); set.add(xs[i] * 1000L + ys[i]); }

            // infer which of the three transforms maps the ruin set onto itself
            boolean fx = true, fy = true, rot = true;
            for (int i = 0; i < n; i++) {
                if (!set.contains((W - 1 - xs[i]) * 1000L + ys[i])) fx = false;
                if (!set.contains(xs[i] * 1000L + (H - 1 - ys[i]))) fy = false;
                if (!set.contains((W - 1 - xs[i]) * 1000L + (H - 1 - ys[i]))) rot = false;
            }
            int pm = 0, fm = 0, pMis = 0, fMis = 0, pairs = 0;
            for (int i = 0; i < n; i++) {
                if (plain(xs[i], ys[i], W, H)) pm++;
                if (fold(xs[i], ys[i], W, H)) fm++;
                int mx = xs[i], my = ys[i];
                if (fx) mx = W - 1 - xs[i];
                else if (fy) my = H - 1 - ys[i];
                else if (rot) { mx = W - 1 - xs[i]; my = H - 1 - ys[i]; }
                else continue;
                pairs++;
                if (plain(xs[i], ys[i], W, H) != plain(mx, my, W, H)) pMis++;
                if (fold(xs[i], ys[i], W, H) != fold(mx, my, W, H)) fMis++;
            }
            nMaps++; ruinsTot += n; plainMoney += pm; foldMoney += fm;
            pairsTot += pairs; plainMisTot += pMis; foldMisTot += fMis;
            boolean pAll = (pm == 0 || pm == n), fAll = (fm == 0 || fm == n);
            if (pAll) plainAllOne++;
            if (fAll) foldAllOne++;
            if (pMis > 0) plainBadMaps++;
            if (fMis > 0) foldBadMaps++;
            System.out.println(String.format("%-22s %3dx%-5d %-6d  %3d/%-5s/%-5d  %3d/%-5s/%-5d",
                    map.name(), W, H, n, pm, pAll ? "ALL" : "-", pMis, fm, fAll ? "ALL" : "-", fMis));
        }
        System.out.println();
        System.out.println("maps=" + nMaps + " ruins=" + ruinsTot + " mirrored-pairs=" + pairsTot);
        System.out.println(String.format("PLAIN  money %d/%d (%.1f%%)  all-one-type maps %d  mirror-mismatched ruins %d (%.1f%%) on %d maps",
                plainMoney, ruinsTot, 100.0 * plainMoney / ruinsTot, plainAllOne, plainMisTot, 100.0 * plainMisTot / pairsTot, plainBadMaps));
        System.out.println(String.format("FOLD   money %d/%d (%.1f%%)  all-one-type maps %d  mirror-mismatched ruins %d (%.1f%%) on %d maps",
                foldMoney, ruinsTot, 100.0 * foldMoney / ruinsTot, foldAllOne, foldMisTot, 100.0 * foldMisTot / pairsTot, foldBadMaps));
    }
}
