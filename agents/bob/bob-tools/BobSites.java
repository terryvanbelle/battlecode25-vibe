// Zero-game measurement of the GEOMETRIC ceiling on SRP construction.
// GameWorld.isValidPatternCenter(loc,false) = x>=2 && y>=2 && x<W-2 && y<H-2 &&
// areaIsPaintable(loc), i.e. none of the 25 tiles in the 5x5 is a wall or a ruin.
// That is a pure function of the map file, so "what fraction of tiles can host an
// SRP at all?" is answerable for all 75 maps with no matches played.
// Usage: java -cp .:<engine-jar> BobSites <dir-of-map25>
import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class BobSites {
    public static void main(String[] args) throws Exception {
        File[] fs = new File(args[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        System.out.println("map,W,H,ruins,paintable,validCentres,pctOfPaintable,pctBlockedByRuins");
        double sumPct = 0, sumRuinPct = 0; int n = 0; double worst = 1e9, bestv = -1;
        String worstMap = "", bestMap = "";
        for (File f : fs) {
            byte[] raw = readAll(f);
            GameMap gm;
            try { gm = GameMap.getRootAsGameMap(ByteBuffer.wrap(raw)); } catch (Exception e) { continue; }
            int w, h; VecTable ruins;
            try { w = gm.size().x(); h = gm.size().y(); ruins = gm.ruins(); } catch (Exception e) { continue; }
            boolean[][] blocked = new boolean[w][h];      // wall or ruin
            boolean[][] wall = new boolean[w][h];
            int paintable = 0;
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
                boolean b = gm.walls(y * w + x);
                wall[x][y] = b; blocked[x][y] = b;
            }
            int nr = ruins == null ? 0 : ruins.xsLength();
            for (int i = 0; i < nr; i++) blocked[ruins.xs(i)][ruins.ys(i)] = true;
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) if (!blocked[x][y]) paintable++;

            int valid = 0, validIgnoringRuins = 0;
            for (int y = 2; y < h - 2; y++) for (int x = 2; x < w - 2; x++) {
                boolean ok = true, okNoRuin = true;
                for (int dx = -2; dx <= 2 && ok; dx++) for (int dy = -2; dy <= 2 && ok; dy++) {
                    if (blocked[x + dx][y + dy]) ok = false;
                }
                for (int dx = -2; dx <= 2 && okNoRuin; dx++) for (int dy = -2; dy <= 2 && okNoRuin; dy++) {
                    if (wall[x + dx][y + dy]) okNoRuin = false;
                }
                if (ok) valid++;
                if (okNoRuin) validIgnoringRuins++;
            }
            double pct = 100.0 * valid / paintable;
            double ruinPct = validIgnoringRuins == 0 ? 0
                : 100.0 * (validIgnoringRuins - valid) / validIgnoringRuins;
            System.out.printf("%s,%d,%d,%d,%d,%d,%.1f,%.1f%n",
                f.getName().replace(".map25", ""), w, h, nr, paintable, valid, pct, ruinPct);
            sumPct += pct; sumRuinPct += ruinPct; n++;
            if (pct < worst) { worst = pct; worstMap = f.getName(); }
            if (pct > bestv) { bestv = pct; bestMap = f.getName(); }
        }
        System.out.printf("%nmaps=%d  mean valid-centre share of paintable tiles = %.1f%%%n", n, sumPct / n);
        System.out.printf("mean share of wall-legal centres killed by RUINS = %.1f%%%n", sumRuinPct / n);
        System.out.printf("worst %s %.1f%%   best %s %.1f%%%n", worstMap, worst, bestMap, bestv);
    }

    static byte[] readAll(File f) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        InputStream in = new BufferedInputStream(new FileInputStream(f));
        in.mark(2); int b1 = in.read(), b2 = in.read(); in.reset();
        if (b1 == 0x1f && (b2 & 0xff) == 0x8b) in = new GZIPInputStream(in);
        byte[] buf = new byte[1 << 16]; int k;
        while ((k = in.read(buf)) > 0) bos.write(buf, 0, k);
        in.close();
        return bos.toByteArray();
    }
}
