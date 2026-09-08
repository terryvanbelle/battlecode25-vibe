package com.google.flatbuffers;

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

/**
 * Carol, iteration 34. What money-tower share does MONEY_MOD actually deliver?
 *
 * towerTypeFor uses k = min(x, W-1-x) + min(y, H-1-y) and calls a ruin MONEY when
 * k % MONEY_MOD == 0. k is a distance-from-edge sum, NOT uniform, so "1 in MONEY_MOD" is an
 * assumption rather than a fact -- and the whole iteration is a dose on that constant. This
 * reads the real ruin coordinates out of the official corpus and reports the realized share,
 * for zero VM game time.
 */
public class MixScan {
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
        int[] mods = {3, 4, 5};
        int[] tot = new int[mods.length];
        int totRuins = 0;
        int[] zeroMoneyMaps = new int[mods.length];
        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            int w = map.size().x(), h = map.size().y();
            VecTable r = map.ruins();
            int n = r == null ? 0 : r.xsLength();
            totRuins += n;
            int[] money = new int[mods.length];
            for (int i = 0; i < n; i++) {
                int k = Math.min(r.xs(i), w - 1 - r.xs(i)) + Math.min(r.ys(i), h - 1 - r.ys(i));
                for (int m = 0; m < mods.length; m++) if (k % mods[m] == 0) money[m]++;
            }
            for (int m = 0; m < mods.length; m++) {
                tot[m] += money[m];
                if (money[m] == 0) zeroMoneyMaps[m]++;
            }
        }
        System.out.println("official corpus: " + fs.length + " maps, " + totRuins + " ruins");
        for (int m = 0; m < mods.length; m++) {
            System.out.println(String.format(
                "MONEY_MOD=%d  money ruins %4d  realized share %5.1f%%  (nominal %4.1f%%)   maps with ZERO money ruins: %d",
                mods[m], tot[m], 100.0 * tot[m] / totRuins, 100.0 / mods[m], zeroMoneyMaps[m]));
        }
    }
}
