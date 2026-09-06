// Measures the tower-mix rule directly against the map pool, with no games at all.
// Every .map25 is a flatbuffer whose root is a GameMap, which carries the ruin list --
// so "what fraction of each map's ruins does towerTypeFor make money towers?" is a
// question about the maps, not about a match, and can be answered exactly for all 75.
// Usage: java -cp .:<engine-jar> BobRuins <dir-of-map25>
import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class BobRuins {
    public static void main(String[] args) throws Exception {
        File[] fs = new File(args[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        System.out.println("map,size,symmetry,ruins,oldMoney,newMoney,oldAllOne,newAllOne");
        int nOldAll = 0, nNewAll = 0, n = 0;
        double oldDev = 0, newDev = 0, worstOld = 0, worstNew = 0;
        for (File f : fs) {
            byte[] raw = readAll(f);
            GameMap gm;
            try { gm = GameMap.getRootAsGameMap(ByteBuffer.wrap(raw)); } catch (Exception e) { continue; }
            VecTable ruins;
            int w, h;
            try { ruins = gm.ruins(); w = gm.size().x(); h = gm.size().y(); }
            catch (Exception e) { continue; }
            if (ruins == null || ruins.xsLength() == 0) continue;
            int r = ruins.xsLength(), oldM = 0, newM = 0;
            for (int i = 0; i < r; i++) {
                int x = ruins.xs(i), y = ruins.ys(i);
                if (((x + y) & 1) == 0) oldM++;
                if ((hash(x, y) & 1) == 0) newM++;
            }
            boolean oa = (oldM == 0 || oldM == r), na = (newM == 0 || newM == r);
            if (oa) nOldAll++;
            if (na) nNewAll++;
            double od = Math.abs(100.0 * oldM / r - 50), nd = Math.abs(100.0 * newM / r - 50);
            oldDev += od; newDev += nd;
            worstOld = Math.max(worstOld, od); worstNew = Math.max(worstNew, nd);
            n++;
            System.out.printf("%s,%dx%d,%d,%d,%d,%d,%s,%s%n",
                gm.name(), w, h, gm.symmetry(), r, oldM, newM, oa ? "ALLONE" : "", na ? "ALLONE" : "");
        }
        System.out.println();
        System.out.printf("maps=%d  all-one-type: old %d (%.0f%%)  new %d (%.0f%%)%n",
            n, nOldAll, 100.0 * nOldAll / n, nNewAll, 100.0 * nNewAll / n);
        System.out.printf("mean deviation from a 50/50 mix: old %.1f pts  new %.1f pts%n",
            oldDev / n, newDev / n);
        System.out.printf("worst deviation:                 old %.1f pts  new %.1f pts%n",
            worstOld, worstNew);
    }

    /** Byte-identical to Soldier.towerTypeFor's hash. */
    static int hash(int x, int y) {
        int h = x * 0x27D4EB2D + y * 0x165667B1;
        h ^= h >>> 15; h *= 0x2545F491; h ^= h >>> 13;
        return h;
    }

    static byte[] readAll(File f) throws IOException {
        try (BufferedInputStream bi = new BufferedInputStream(new FileInputStream(f))) {
            bi.mark(2); int b1 = bi.read(), b2 = bi.read(); bi.reset();
            InputStream in = (b1 == 0x1f && b2 == 0x8b) ? new GZIPInputStream(bi) : bi;
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] buf = new byte[1 << 16]; int k;
            while ((k = in.read(buf)) > 0) bos.write(buf, 0, k);
            return bos.toByteArray();
        }
    }
}
