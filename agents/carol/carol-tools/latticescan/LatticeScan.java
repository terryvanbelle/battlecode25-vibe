package com.google.flatbuffers;

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

/**
 * Carol, iteration 32. How much of the official map corpus can host a lattice SRP?
 *
 * A "lattice cell" is the 5x5 block centred at (5*(x/5)+2, 5*(y/5)+2) -- a pure function of
 * the tile, so every soldier agrees on it with nothing communicated, and 5x5 blocks on a
 * 5-stride lattice tile the plane exactly with no overlap.
 *
 * A cell is VIABLE only if all 25 tiles are on the map, none is a wall, and none is a ruin
 * (ruin tiles are unpaintable, and an SRP needs all 25 tiles painted exactly). Also reported:
 * how many cells a ruin's 5x5 TOWER pattern overlaps, since recolouring those tiles would set
 * SRP work and workOnRuin repainting each other.
 *
 * This is a static property of the map, so it bounds the whole direction for zero VM game
 * time -- the cheapest possible pre-check, and it is the ceiling no in-game tuning can raise.
 */
public class LatticeScan {
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

    public static void main(String[] a) throws Exception {
        File[] fs = new File(a[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        int totCells = 0, totViable = 0, totFree = 0;
        List<double[]> pct = new ArrayList<>();
        System.out.println(String.format("%-24s %-8s %5s %5s %6s %5s %6s",
                "map", "size", "cells", "viab", "viab%", "free", "free%"));
        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            int w = map.size().x(), h = map.size().y();
            boolean[] wall = new boolean[w * h];
            for (int i = 0; i < w * h && i < map.wallsLength(); i++) wall[i] = map.walls(i);
            boolean[] ruin = new boolean[w * h];
            VecTable r = map.ruins();
            int nr = r == null ? 0 : r.xsLength();
            int[] rx = new int[nr], ry = new int[nr];
            for (int i = 0; i < nr; i++) {
                rx[i] = r.xs(i); ry[i] = r.ys(i);
                ruin[ry[i] * w + rx[i]] = true;
            }
            int cells = 0, viable = 0, free = 0;
            for (int cx = 2; cx + 2 < w; cx += 5) {
                for (int cy = 2; cy + 2 < h; cy += 5) {
                    cells++;
                    boolean ok = true;
                    for (int dx = -2; dx <= 2 && ok; dx++)
                        for (int dy = -2; dy <= 2; dy++) {
                            int i = (cy + dy) * w + (cx + dx);
                            if (wall[i] || ruin[i]) { ok = false; break; }
                        }
                    if (!ok) continue;
                    viable++;
                    // ... and does any ruin's 5x5 tower pattern reach into this cell?
                    boolean clash = false;
                    for (int i = 0; i < nr; i++)
                        if (Math.abs(rx[i] - cx) <= 4 && Math.abs(ry[i] - cy) <= 4) { clash = true; break; }
                    if (!clash) free++;
                }
            }
            totCells += cells; totViable += viable; totFree += free;
            pct.add(new double[]{100.0 * viable / cells, 100.0 * free / cells});
            System.out.println(String.format("%-24s %3dx%-4d %5d %5d %5.1f%% %5d %5.1f%%",
                    map.name(), w, h, cells, viable, 100.0 * viable / cells, free, 100.0 * free / cells));
        }
        pct.sort((p, q) -> Double.compare(p[0], q[0]));
        System.out.println("\nTOTAL cells=" + totCells + " viable=" + totViable
                + String.format(" (%.1f%%)", 100.0 * totViable / totCells)
                + " ruin-free=" + totFree + String.format(" (%.1f%%)", 100.0 * totFree / totCells));
        System.out.println(String.format("per-map viable%%: min %.1f  median %.1f  max %.1f",
                pct.get(0)[0], pct.get(pct.size() / 2)[0], pct.get(pct.size() - 1)[0]));
        int dead = 0; for (double[] p : pct) if (p[0] == 0) dead++;
        System.out.println("maps with ZERO viable cells: " + dead);
    }
}
