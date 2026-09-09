package com.google.flatbuffers;

import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

/**
 * Print RUIN COORDINATES for every official map, read from the engine jar's own
 * .map25 flatbuffers. Modelled on tools/mapdata/ruinscan/RuinScan.java, which
 * prints only counts; this prints positions, which is what is needed to ask
 * "did alice ever paint NEAR this ruin".
 *
 * Output:  <mapname> <width> <height> x,y x,y x,y ...
 *
 * These are CLAIMABLE ruins -- the .map25 `ruins()` vector, which excludes the
 * four tiles the starting towers occupy. A replay MatchHeader reports four more.
 * Same convention as ruin_parity.txt, deliberately, so the two reconcile.
 */
public class RuinCoords {
    static byte[] read(InputStream in) throws IOException {
        ByteArrayOutputStream bo = new ByteArrayOutputStream();
        byte[] b = new byte[8192];
        int n;
        while ((n = in.read(b)) > 0) bo.write(b, 0, n);
        byte[] raw = bo.toByteArray();
        if (raw.length > 2 && (raw[0] & 0xff) == 0x1f && (raw[1] & 0xff) == 0x8b) {
            ByteArrayOutputStream o2 = new ByteArrayOutputStream();
            try (GZIPInputStream gz = new GZIPInputStream(new ByteArrayInputStream(raw))) {
                while ((n = gz.read(b)) > 0) o2.write(b, 0, n);
            }
            return o2.toByteArray();
        }
        return raw;
    }

    public static void main(String[] a) throws Exception {
        File dir = new File(a[0]);
        File[] fs = dir.listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        for (File f : fs) {
            GameMap map;
            try (InputStream in = new FileInputStream(f)) {
                map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(in)));
            }
            VecTable r = map.ruins();
            int n = r == null ? 0 : r.xsLength();
            StringBuilder sb = new StringBuilder();
            sb.append(map.name()).append(' ')
              .append(map.size().x()).append(' ').append(map.size().y());
            for (int i = 0; i < n; i++) sb.append(' ').append(r.xs(i)).append(',').append(r.ys(i));
            System.out.println(sb);
        }
    }
}
