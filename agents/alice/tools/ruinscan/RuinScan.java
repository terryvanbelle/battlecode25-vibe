package com.google.flatbuffers;

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class RuinScan {
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
        File dir = new File(a[0]);
        File[] fs = dir.listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        int totEven = 0, totOdd = 0, maps = 0, mapsAllEven = 0;
        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            VecTable r = map.ruins();
            int n = r == null ? 0 : r.xsLength();
            int even = 0, odd = 0;
            for (int i = 0; i < n; i++) {
                if (((r.xs(i) + r.ys(i)) & 1) == 0) even++; else odd++;
            }
            totEven += even; totOdd += odd; maps++;
            if (odd == 0) mapsAllEven++;
            System.out.println(String.format("%-22s %3dx%-3d ruins=%3d even=%3d odd=%3d",
                    map.name(), map.size().x(), map.size().y(), n, even, odd));
        }
        System.out.println("TOTAL maps=" + maps + " allEvenMaps=" + mapsAllEven
                + " ruinsEven=" + totEven + " ruinsOdd=" + totOdd);
    }
}
