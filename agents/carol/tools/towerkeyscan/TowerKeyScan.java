package com.google.flatbuffers;

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

/**
 * Carol-private: is `towerTypeFor`'s key single-branch on any official map?
 *
 * carol's RobotPlayer decides each ruin's tower type from
 *     k = min(x, w-1-x) + min(y, h-1-y);   k % 3 == 0 -> MONEY else PAINT
 * which is a coordinate-keyed modulus policy -- the same shape as the (x+y)&1
 * trap recorded in tools/mapdata/README.md, but a different modulus, so the
 * shared parity table cannot answer it. A map where every ruin lands in one
 * class builds ALL money towers (no paint income at all) or ALL paint towers.
 *
 * Adapted from the shared tools/mapdata/ruinscan/RuinScan.java (neutral ground).
 */
public class TowerKeyScan {
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
        int allMoney = 0, allPaint = 0, totM = 0, totP = 0;
        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            VecTable r = map.ruins();
            int n = r == null ? 0 : r.xsLength();
            int w = map.size().x(), h = map.size().y();
            int money = 0, paint = 0;
            for (int i = 0; i < n; i++) {
                int x = r.xs(i), y = r.ys(i);
                int k = Math.min(x, w - 1 - x) + Math.min(y, h - 1 - y);
                if (k % 3 == 0) money++; else paint++;
            }
            totM += money; totP += paint;
            String flag = "";
            if (n > 0 && paint == 0) { allMoney++; flag = "   <<< ALL MONEY - zero paint income"; }
            if (n > 0 && money == 0) { allPaint++; flag = "   <<< ALL PAINT - zero chip income"; }
            System.out.println(String.format("%-22s %3dx%-3d ruins=%3d money=%3d paint=%3d%s",
                    map.name(), w, h, n, money, paint, flag));
        }
        System.out.println("TOTAL allMoneyMaps=" + allMoney + " allPaintMaps=" + allPaint
                + " ruinsMoney=" + totM + " ruinsPaint=" + totP);
    }
}
