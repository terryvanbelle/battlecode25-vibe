// Zero-game measurement of what PERMANENT TOWER-PATTERN MARKS cost SRP siting.
//
// ENGINE FACTS this rests on (bytecode-verified 2026-09-09, engine 3.1.0):
//   * GameWorld.completeTowerPattern() and completeResourcePattern() write
//     towerLocations / resourcePatternCenters and NOTHING ELSE -- neither touches
//     markersA/markersB. The ONLY writer of a marker is GameWorld.setMarker, called
//     from markPattern(...) and from RobotControllerImpl.removeMark. So a mark laid
//     down by markTowerPattern is PERMANENT unless the bot removes it, and bob has
//     never called removeMark (API sweep: it is one of 24 RobotController methods
//     bob never calls).
//   * RobotControllerImpl.removeMark asserts only: robot (not tower) type,
//     assertCanActLocation(loc, r^2<=2), and that a marker exists. It then calls
//     setMarker(team, loc, 0) and returns. NO isActionReady check, NO cooldown, NO
//     paint. It is FREE, like upgradeTower -- bounded only by bytecode and by the
//     3x3 reach.
//
// THE GEOMETRY. markTowerPattern blankets the 5x5 around a ruin. Soldier.srpSiteSafe
// rejects a candidate centre c if ANY tile of c's own 5x5 carries a mark. A tile can
// be in both 5x5s iff Chebyshev(c,R) <= 4. Valid centres already require no ruin in
// the 5x5, i.e. Chebyshev(c,R) >= 3. So marking a ruin additionally kills exactly the
// centres at Chebyshev distance 3 or 4 from it -- a ring bob currently poisons for the
// rest of the game the first time a soldier marks that ruin, and never cleans up.
//
// This is a pure function of the map file, so the cost is answerable for all 75 maps
// with ZERO games played.
//
// Usage: java -cp .:<engine-jar> BobMarks <dir-of-map25>
import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class BobMarks {
    public static void main(String[] args) throws Exception {
        File[] fs = new File(args[0]).listFiles((d, n) -> n.endsWith(".map25"));
        Arrays.sort(fs);
        System.out.println("map,W,H,ruins,paintable,validCentres,afterMarks,pctKilledByMarks,zeroLeft");
        int n = 0, zeroAfter = 0, zeroBefore = 0;
        long sumValid = 0, sumAfter = 0;
        for (File f : fs) {
            byte[] raw = readAll(f);
            GameMap gm;
            try { gm = GameMap.getRootAsGameMap(ByteBuffer.wrap(raw)); } catch (Exception e) { continue; }
            int w, h; VecTable ruins;
            try { w = gm.size().x(); h = gm.size().y(); ruins = gm.ruins(); } catch (Exception e) { continue; }
            boolean[][] blocked = new boolean[w][h];
            int paintable = 0;
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) blocked[x][y] = gm.walls(y * w + x);
            int nr = ruins == null ? 0 : ruins.xsLength();
            int[] rx = new int[nr], ry = new int[nr];
            for (int i = 0; i < nr; i++) {
                rx[i] = ruins.xs(i); ry[i] = ruins.ys(i);
                blocked[rx[i]][ry[i]] = true;
            }
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) if (!blocked[x][y]) paintable++;

            int valid = 0, after = 0;
            for (int y = 2; y < h - 2; y++) for (int x = 2; x < w - 2; x++) {
                boolean ok = true;
                for (int dx = -2; dx <= 2 && ok; dx++) for (int dy = -2; dy <= 2 && ok; dy++)
                    if (blocked[x + dx][y + dy]) ok = false;
                if (!ok) continue;
                valid++;
                // survives once EVERY ruin has been tower-pattern-marked
                boolean free = true;
                for (int i = 0; i < nr && free; i++)
                    if (Math.max(Math.abs(x - rx[i]), Math.abs(y - ry[i])) <= 4) free = false;
                if (free) after++;
            }
            double killed = valid == 0 ? 0 : 100.0 * (valid - after) / valid;
            System.out.printf("%s,%d,%d,%d,%d,%d,%d,%.1f,%s%n",
                f.getName().replace(".map25", ""), w, h, nr, paintable, valid, after, killed,
                after == 0 ? "YES" : "");
            n++; sumValid += valid; sumAfter += after;
            if (after == 0) zeroAfter++;
            if (valid == 0) zeroBefore++;
        }
        System.out.printf("%nmaps=%d%n", n);
        System.out.printf("total valid centres  before marks = %d%n", sumValid);
        System.out.printf("total valid centres  after  marks = %d  (%.1f%% killed)%n",
            sumAfter, sumValid == 0 ? 0 : 100.0 * (sumValid - sumAfter) / sumValid);
        System.out.printf("maps with ZERO sites before marks = %d%n", zeroBefore);
        System.out.printf("maps with ZERO sites after  marks = %d%n", zeroAfter);
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
