package com.google.flatbuffers;
import battlecode.schema.*;
import java.io.*; import java.nio.ByteBuffer; import java.nio.file.*; import java.util.*;
import java.util.zip.GZIPInputStream;
/** How many VALID SRP centres does each official map have?
 *  isValidPatternCenter (disassembled, TRAINING_LOG iteration-7 probe) requires
 *  2 <= x < W-2, 2 <= y < H-2 and areaIsPaintable(loc): all 25 tiles of the 5x5
 *  free of walls AND ruins. Starting-tower tiles are ruins too and are added from
 *  initialBodies, since .map25 ruins() excludes them.
 *  Prints wall count as a reconciliation handle against the replay MatchHeader. */
public class SrpScan {
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
        System.out.println("map,w,h,walls,ruins,srp_centres,pct_of_tiles,srp_per_ruin");
        for (File f : fs) {
            GameMap m = GameMap.getRootAsGameMap(ByteBuffer.wrap(read(f)));
            int W=m.size().x(), H=m.size().y();
            boolean[][] blocked = new boolean[W][H];
            int walls=0;
            for (int i=0;i<m.wallsLength();i++) if (m.walls(i)) { blocked[i%W][i/W]=true; walls++; }
            VecTable r=m.ruins(); int nr = r==null?0:r.xsLength();
            for (int i=0;i<nr;i++) blocked[r.xs(i)][r.ys(i)]=true;
            InitialBodyTable ib = m.initialBodies();
            int nb=0;
            if (ib!=null) { nb=ib.spawnActionsLength();
                for (int i=0;i<nb;i++) { SpawnAction sa=ib.spawnActions(i);
                    blocked[sa.x()][sa.y()]=true; } }
            int ok=0;
            for (int x=2;x<W-2;x++) for (int y=2;y<H-2;y++) {
                boolean good=true;
                for (int dx=-2;dx<=2&&good;dx++) for (int dy=-2;dy<=2&&good;dy++)
                    if (blocked[x+dx][y+dy]) good=false;
                if (good) ok++;
            }
            System.out.printf("%s,%d,%d,%d,%d,%d,%.1f,%.2f%n", m.name(), W, H, walls, nr+nb, ok,
                100.0*ok/(W*H), nr==0?0.0:(double)ok/nr);
        }
    }
}
