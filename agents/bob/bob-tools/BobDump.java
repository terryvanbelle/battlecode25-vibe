// Bob's replay-to-text tool. Reads a .bc25 (gzipped flatbuffer GameWrapper) using
// the engine jar's own schema classes and prints per-round metrics.
// Usage: java -cp .:<engine-jar> BobDump <replay.bc25> [sampleEvery]
import battlecode.schema.*;
import java.io.*;
import java.util.HashMap;
import java.util.Map;
import java.nio.ByteBuffer;
import java.util.zip.GZIPInputStream;

/** Exposes flatbuffers' protected cursor so a struct union member can be read.
 *  The engine declares Turn.actions as a union of STRUCTS, but the generated
 *  accessor only offers the Table form, so we let it position a probe and then
 *  re-assign the same buffer position into the concrete struct. */
class Cursor extends com.google.flatbuffers.Table {
    int pos() { return bb_pos; }
    java.nio.ByteBuffer buf() { return bb; }
}

public class BobDump {
    public static void main(String[] args) throws Exception {
        String path = args[0];
        int every = args.length > 1 ? Integer.parseInt(args[1]) : 50;

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (InputStream in = maybeGzip(new BufferedInputStream(new FileInputStream(path)))) {
            byte[] buf = new byte[1 << 16];
            int n;
            while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
        }
        GameWrapper gw = GameWrapper.getRootAsGameWrapper(ByteBuffer.wrap(bos.toByteArray()));

        System.out.println("events=" + gw.eventsLength());
        // cov/money/srp are engine-reported team totals; the rest are accumulated here.
        // sold/spl/mop/ptow/mtow are CUMULATIVE SPAWN counts (this engine reports deaths
        // as DieAction rather than populating diedIds, so these are production totals,
        // not live population -- read their slope as the production rate).
        // paint = sum of paint held by that team's robots this round.
        // unpaint = enemy-paint-removal actions (Unpaint/Splash/Mop) SINCE THE LAST ROW,
        // i.e. already normalised per interval -- raw cumulative counts scale with game
        // length and read as "better" purely because a game ran longer.
        // maxbc = highest bytecode any of that team's robots used so far (limit 17500).
        System.out.println("round,covA,covB,moneyA,moneyB,srpA,srpB,died,turns,"
            + "soldA,splA,mopA,ptowA,mtowA,paintA,unpaintA,maxbcA,"
            + "soldB,splB,mopB,ptowB,mtowB,paintB,unpaintB,maxbcB");
        int lastPrinted = -1;
        Round lastRound = null;
        SpawnAction sa = new SpawnAction();
        Cursor cur = new Cursor();
        for (int i = 0; i < gw.eventsLength(); i++) {
            EventWrapper ew = gw.events(i);
            byte t = ew.eType();
            if (t == Event.Round) {
                Round r = (Round) ew.e(new Round());
                lastRound = r;
                scanRound(r, sa, cur);
                if (r.roundId() % every == 0) {
                    printRound(r);
                    lastPrinted = r.roundId();
                }
            } else if (t == Event.MatchFooter) {
                if (lastRound != null && lastRound.roundId() != lastPrinted) printRound(lastRound);
                MatchFooter f = (MatchFooter) ew.e(new MatchFooter());
                System.out.println("FOOTER winner=" + (char)('A' + f.winner() - 1)
                    + " winType=" + WinType.names[f.winType()]
                    + " totalRounds=" + f.totalRounds());
                for (int m = 0; m < f.timelineMarkersLength(); m++) {
                    TimelineMarker tm = f.timelineMarkers(m);
                    System.out.println("MARKER team=" + tm.team() + " r=" + tm.round()
                        + " " + tm.label());
                }
            }
        }
    }

    // --- accumulated state, indexed [team 0/1] ---
    static final Map<Integer,Integer> idTeam = new HashMap<>();   // robotId -> 0/1
    static final Map<Integer,Integer> idType = new HashMap<>();   // robotId -> RobotType byte
    static final int[][] live = new int[2][8];                    // [team][RobotType], cumulative spawns
    static final int[] paintNow = new int[2];
    static final int[] maxBc = new int[2];
    static final int[] unpaint = new int[2];                      // since last printed row

    /** Walk one round's turns, maintaining live unit counts, paint, bytecode and
     *  enemy-paint-removal counts. Deaths are applied from diedIds. */
    static void scanRound(Round r, SpawnAction sa, Cursor cur) {
        paintNow[0] = 0; paintNow[1] = 0;
        Turn turn = new Turn();
        for (int i = 0; i < r.turnsLength(); i++) {
            r.turns(turn, i);
            Integer tm = idTeam.get(turn.robotId());
            if (tm != null) {
                paintNow[tm] += turn.paint();
                if (turn.bytecodesUsed() > maxBc[tm]) maxBc[tm] = turn.bytecodesUsed();
            }
            for (int a = 0; a < turn.actionsLength(); a++) {
                byte at = turn.actionsType(a);
                try {
                    if (at == Action.SpawnAction) {
                        turn.actions(cur, a);
                        sa.__assign(cur.pos(), cur.buf());
                        int team = sa.team() - 1;           // schema teams are 1-based
                        byte rt = sa.robotType();
                        if (team < 0 || team > 1 || rt < 0 || rt > 6) continue;
                        idTeam.put(sa.id(), team);
                        idType.put(sa.id(), (int) rt);
                        live[team][rt]++;
                    } else if (tm != null
                            && (at == Action.UnpaintAction || at == Action.SplashAction
                                || at == Action.MopAction)) {
                        unpaint[tm]++;
                    }
                } catch (RuntimeException e) {
                    // A malformed or unexpected union entry must not kill the dump;
                    // every counter here is a diagnostic, never a decision input.
                }
            }
        }
        for (int i = 0; i < r.diedIdsLength(); i++) {
            int id = r.diedIds(i);
            Integer team = idTeam.remove(id);
            Integer ty = idType.remove(id);
            if (team != null && ty != null) live[team][ty]--;
        }
    }

    static void printRound(Round r) {
        StringBuilder sb = new StringBuilder();
        sb.append(r.roundId());
        for (int j = 0; j < 2; j++) sb.append(',').append(cov(r, j));
        for (int j = 0; j < 2; j++) sb.append(',').append(res(r, j));
        for (int j = 0; j < 2; j++) sb.append(',').append(srp(r, j));
        sb.append(',').append(r.diedIdsLength());
        sb.append(',').append(r.turnsLength());
        for (int j = 0; j < 2; j++) {
            sb.append(',').append(live[j][RobotType.SOLDIER]);
            sb.append(',').append(live[j][RobotType.SPLASHER]);
            sb.append(',').append(live[j][RobotType.MOPPER]);
            sb.append(',').append(live[j][RobotType.PAINT_TOWER]);
            sb.append(',').append(live[j][RobotType.MONEY_TOWER]);
            sb.append(',').append(paintNow[j]);
            sb.append(',').append(unpaint[j]);
            sb.append(',').append(maxBc[j]);
        }
        System.out.println(sb);
        unpaint[0] = 0; unpaint[1] = 0;   // per-interval, not cumulative
    }

    static int cov(Round r, int i) { return i < r.teamCoverageAmountsLength() ? r.teamCoverageAmounts(i) : -1; }
    static int res(Round r, int i) { return i < r.teamResourceAmountsLength() ? r.teamResourceAmounts(i) : -1; }
    static int srp(Round r, int i) { return i < r.teamResourcePatternAmountsLength() ? r.teamResourcePatternAmounts(i) : -1; }

    static InputStream maybeGzip(BufferedInputStream in) throws IOException {
        in.mark(2);
        int b1 = in.read(), b2 = in.read();
        in.reset();
        if (b1 == 0x1f && b2 == 0x8b) return new GZIPInputStream(in);
        return in;
    }
}
