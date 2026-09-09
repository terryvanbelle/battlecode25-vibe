package com.google.flatbuffers;
import battlecode.schema.*;
import java.io.*; import java.nio.ByteBuffer; import java.nio.file.*; import java.util.*;
import java.util.zip.GZIPInputStream;
/** Per-map distribution of carol's towerTypeFor key k = min(x,W-1-x)+min(y,H-1-y),
 *  which decides money vs paint via k % MONEY_MOD == 0. Prints the money share the
 *  rule INTENDS on each map, plus the raw ruin coords for offline subset analysis. */
public class KScan {
    static byte[] read(File f) throws IOException {
        byte[] raw = Files.readAllBytes(f.toPath());
        if (raw.length > 2 && (raw[0]&0xff)==0x1f && (raw[1]&0xff)==0x8b) {
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            try (GZIPInputStream gz = new GZIPInputStream(new ByteArrayInputStream(raw))) {
                byte[] b = new byte[8192]; int n; while ((n=gz.read(b))>0) bo.write(b,0,n);
            } return bo.toByteArray();
        } return raw;
    }
    public static void main(String[] a) throws Exception {
        File[] fs = new File(a[0]).listFiles((d,n)->n.endsWith(".map25"));
        Arrays.sort(fs);
        System.out.println("map,w,h,ruins,coords,ks");
        for (File f : fs) {
            GameMap map = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            VecTable r = map.ruins(); int n = r==null?0:r.xsLength();
            int W = map.size().x(), H = map.size().y();
            StringBuilder cs = new StringBuilder(), ks = new StringBuilder();
            for (int i=0;i<n;i++) {
                int x=r.xs(i), y=r.ys(i);
                int k = Math.min(x, W-1-x) + Math.min(y, H-1-y);
                if (i>0){cs.append(' ');ks.append(' ');}
                cs.append(x).append(':').append(y); ks.append(k);
            }
            System.out.println(map.name()+","+W+","+H+","+n+","+cs+","+ks);
        }
    }
}
