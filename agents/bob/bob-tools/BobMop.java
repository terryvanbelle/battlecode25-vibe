// Bob's denial-opportunity tracer. Reconstructs the ENEMY paint set round by round
// from the replay's Paint/Unpaint/Splash actions, then measures -- for every one of
// our moppers and splashers, on every sampled round -- how far away the nearest
// enemy-painted tile actually was.
//
// Why this exists: the dumper showed our moppers and splashers acting at ~1% of
// their cooldown capacity, and mopping costs ZERO paint (engine: MOPPER attack cost
// 0, cooldown 30 => 0.33 actions/round ceiling). So the bottleneck cannot be cost.
// The two remaining candidates are "they can't reach enemy paint" (navigation) and
// "they never find it" (target acquisition), and those want completely different
// fixes. This tool separates them with a number instead of a story.
//
// Usage: java -cp .:<engine-jar> BobMop <replay.bc25> <A|B> [sampleEvery]
import battlecode.schema.*;
import java.io.*;
import java.util.*;
import java.nio.ByteBuffer;
import java.util.zip.GZIPInputStream;

class MCursor extends com.google.flatbuffers.Table {
    int pos() { return bb_pos; }
    java.nio.ByteBuffer buf() { return bb; }
}

public class BobMop {
    static int W, H;
    static int us;                                   // 0 = team A, 1 = team B
    static final Map<Integer,Integer> idTeam = new HashMap<>();
    static final Map<Integer,Integer> idType = new HashMap<>();
    // paintOwner[loc]: -1 none, 0 team A, 1 team B
    static byte[] owner;
    // Death forensics: bucket every one of OUR dead units by the paint it held on its
    // last recorded turn. A unit that dies at ~0 paint died of starvation (zero paint =>
    // NO_PAINT_DAMAGE 20 HP/turn); one that dies with a full stash was killed.
    static final Map<Integer,Integer> lastPaint = new HashMap<>();
    static final Map<Integer,Integer> lastHealth = new HashMap<>();
    static final int[][] deaths = new int[8][3];   // [type][0: paint<=10, 1: 11-50, 2: >50]
    static final int[] deathRounds = new int[8];
    static final int[] deathCount = new int[8];
    static int exceptionDeaths = 0;
    static final List<int[]> pendingDeaths = new ArrayList<>();  // [id, dieType]

    public static void main(String[] args) throws Exception {
        String path = args[0];
        us = args[1].equalsIgnoreCase("A") ? 0 : 1;
        int every = args.length > 2 ? Integer.parseInt(args[2]) : 100;

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (InputStream in = maybeGzip(new BufferedInputStream(new FileInputStream(path)))) {
            byte[] buf = new byte[1 << 16]; int n;
            while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
        }
        GameWrapper gw = GameWrapper.getRootAsGameWrapper(ByteBuffer.wrap(bos.toByteArray()));

        PaintAction pa = new PaintAction();
        UnpaintAction ua = new UnpaintAction();
        SplashAction sp = new SplashAction();
        SpawnAction sa = new SpawnAction();
        DieAction da = new DieAction();
        MCursor cur = new MCursor();
        Turn turn = new Turn();

        System.out.println("# denial-opportunity trace, our team = " + (char)('A'+us));
        System.out.println("round,ourMop,ourSpl,enemyTiles,ourTiles,"
            + "mopInAct,mopInVis,mopMedDist,splInAct,splInVis,splMedDist,"
            + "ourSold,mopAvgPaint,mopMinPaint,splAvgPaint");

        for (int i = 0; i < gw.eventsLength(); i++) {
            EventWrapper ew = gw.events(i);
            byte t = ew.eType();
            if (t == Event.MatchHeader) {
                MatchHeader mh = (MatchHeader) ew.e(new MatchHeader());
                GameMap gm = mh.map();
                W = gm.size().x(); H = gm.size().y();
                owner = new byte[W*H];
                Arrays.fill(owner, (byte)-1);
                VecTable ruins = gm.ruins();
                System.out.println("# map=" + gm.name() + " " + W + "x" + H
                    + " symmetry=" + gm.symmetry()
                    + " ruins=" + (ruins == null ? 0 : ruins.xsLength()));
                if (ruins != null) {
                    StringBuilder sb = new StringBuilder("# ruinLocs=");
                    for (int k = 0; k < ruins.xsLength(); k++)
                        sb.append(ruins.xs(k)).append(':').append(ruins.ys(k)).append(' ');
                    System.out.println(sb);
                }
                idTeam.clear(); idType.clear();
            } else if (t == Event.Round) {
                Round r = (Round) ew.e(new Round());
                // --- apply this round's paint changes, and collect our unit positions
                List<int[]> mops = new ArrayList<>(), spls = new ArrayList<>();
                int liveSold = 0, mopPaint = 0, splPaint = 0, mopLowest = 999;
                for (int j = 0; j < r.turnsLength(); j++) {
                    r.turns(turn, j);
                    Integer tm = idTeam.get(turn.robotId());
                    Integer ty = idType.get(turn.robotId());
                    if (tm != null && tm == us) {
                        lastPaint.put(turn.robotId(), turn.paint());
                        lastHealth.put(turn.robotId(), turn.health());
                    }
                    if (tm != null && tm == us && ty != null) {
                        if (ty == RobotType.MOPPER) {
                            mops.add(new int[]{turn.x(), turn.y()});
                            mopPaint += turn.paint();
                            if (turn.paint() < mopLowest) mopLowest = turn.paint();
                        } else if (ty == RobotType.SPLASHER) {
                            spls.add(new int[]{turn.x(), turn.y()});
                            splPaint += turn.paint();
                        } else if (ty == RobotType.SOLDIER) liveSold++;
                    }
                    for (int a = 0; a < turn.actionsLength(); a++) {
                        byte at = turn.actionsType(a);
                        try {
                            if (at == Action.SpawnAction) {
                                turn.actions(cur, a); sa.__assign(cur.pos(), cur.buf());
                                int team = sa.team() - 1; byte rt = sa.robotType();
                                if (team < 0 || team > 1 || rt < 0 || rt > 6) continue;
                                idTeam.put(sa.id(), team); idType.put(sa.id(), (int) rt);
                            } else if (at == Action.PaintAction && tm != null) {
                                turn.actions(cur, a); pa.__assign(cur.pos(), cur.buf());
                                set(pa.loc(), tm.byteValue());
                            } else if (at == Action.UnpaintAction) {
                                turn.actions(cur, a); ua.__assign(cur.pos(), cur.buf());
                                set(ua.loc(), (byte)-1);
                            } else if (at == Action.DieAction) {
                                turn.actions(cur, a); da.__assign(cur.pos(), cur.buf());
                                pendingDeaths.add(new int[]{da.id(), da.dieType()});
                            } else if (at == Action.SplashAction && tm != null) {
                                turn.actions(cur, a); sp.__assign(cur.pos(), cur.buf());
                                splash(sp.loc(), tm.byteValue());
                            }
                        } catch (RuntimeException e) { /* diagnostics only */ }
                    }
                }
                for (int j = 0; j < r.diedIdsLength(); j++)
                    pendingDeaths.add(new int[]{r.diedIds(j), 0});
                for (int[] pd : pendingDeaths) {
                    int id = pd[0];
                    Integer dtm = idTeam.remove(id);
                    Integer dty = idType.remove(id);
                    if (dtm != null && dtm == us && dty != null && dty < 8) {
                        Integer lp = lastPaint.get(id);
                        if (lp != null) {
                            deaths[dty][lp <= 10 ? 0 : lp <= 50 ? 1 : 2]++;
                            deathCount[dty]++;
                        }
                        if (pd[1] == DieType.EXCEPTION) exceptionDeaths++;
                    }
                    lastPaint.remove(id); lastHealth.remove(id);
                }
                pendingDeaths.clear();
                if (r.roundId() % every != 0) continue;

                // --- enemy tile list
                int them = 1 - us;
                List<int[]> enemyTiles = new ArrayList<>();
                int ourCount = 0;
                for (int loc = 0; loc < owner.length; loc++) {
                    if (owner[loc] == them) enemyTiles.add(new int[]{loc % W, loc / W});
                    else if (owner[loc] == us) ourCount++;
                }
                int[] mstat = stats(mops, enemyTiles);
                int[] sstat = stats(spls, enemyTiles);
                System.out.println(r.roundId() + "," + mops.size() + "," + spls.size()
                    + "," + enemyTiles.size() + "," + ourCount
                    + "," + mstat[0] + "," + mstat[1] + "," + mstat[2]
                    + "," + sstat[0] + "," + sstat[1] + "," + sstat[2]
                    + "," + liveSold
                    + "," + (mops.isEmpty() ? -1 : mopPaint / mops.size())
                    + "," + (mops.isEmpty() ? -1 : mopLowest)
                    + "," + (spls.isEmpty() ? -1 : splPaint / spls.size()));
            }
        }
        String[] tn = new String[8];
        tn[RobotType.SOLDIER] = "SOLDIER";
        tn[RobotType.SPLASHER] = "SPLASHER";
        tn[RobotType.MOPPER] = "MOPPER";
        System.out.println("# exceptionDeaths=" + exceptionDeaths);
        System.out.println("# DEATHS of our units, bucketed by paint held on the last turn");
        System.out.println("# type,deaths,paint<=10(starved),paint 11-50,paint>50(killed)");
        for (int k = 0; k < 8; k++) {
            if (deathCount[k] == 0 || tn[k] == null) continue;
            System.out.println("# " + tn[k] + "," + deathCount[k] + ","
                + deaths[k][0] + "," + deaths[k][1] + "," + deaths[k][2]);
        }
    }

    /** For each unit: is an enemy tile within action range (r2<=2) / vision (r2<=20)?
     *  Third value is the MEDIAN Chebyshev distance to the nearest enemy tile, which
     *  is the number that separates "cannot reach" from "never found it". */
    static int[] stats(List<int[]> units, List<int[]> enemy) {
        if (units.isEmpty() || enemy.isEmpty()) return new int[]{0,0,-1};
        int inAct = 0, inVis = 0;
        int[] dists = new int[units.size()];
        for (int i = 0; i < units.size(); i++) {
            int[] u = units.get(i);
            int bestSq = Integer.MAX_VALUE, bestCheb = Integer.MAX_VALUE;
            for (int[] e : enemy) {
                int dx = e[0]-u[0], dy = e[1]-u[1];
                int sq = dx*dx + dy*dy;
                if (sq < bestSq) bestSq = sq;
                int cheb = Math.max(Math.abs(dx), Math.abs(dy));
                if (cheb < bestCheb) bestCheb = cheb;
            }
            if (bestSq <= 2) inAct++;
            if (bestSq <= 20) inVis++;
            dists[i] = bestCheb;
        }
        Arrays.sort(dists);
        return new int[]{inAct, inVis, dists[dists.length/2]};
    }

    static void set(int loc, byte v) { if (loc >= 0 && loc < owner.length) owner[loc] = v; }

    /** Splash paints ally/empty within r2<=4 and overwrites enemy paint within r2<=2. */
    static void splash(int loc, byte team) {
        if (loc < 0 || loc >= owner.length) return;
        int cx = loc % W, cy = loc / W;
        for (int dx = -2; dx <= 2; dx++) for (int dy = -2; dy <= 2; dy++) {
            int sq = dx*dx + dy*dy;
            if (sq > 4) continue;
            int x = cx+dx, y = cy+dy;
            if (x < 0 || y < 0 || x >= W || y >= H) continue;
            int l = y*W + x;
            if (owner[l] == team) continue;
            if (owner[l] == -1 || sq <= 2) owner[l] = team;
        }
    }

    static InputStream maybeGzip(BufferedInputStream in) throws IOException {
        in.mark(2); int b1 = in.read(), b2 = in.read(); in.reset();
        if (b1 == 0x1f && b2 == 0x8b) return new GZIPInputStream(in);
        return in;
    }
}
