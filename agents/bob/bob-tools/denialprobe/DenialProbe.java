package com.google.flatbuffers; // protected Table access is needed to read struct-typed
                                // union members out of Turn.actions(): the engine declares
                                // that vector as a union of STRUCTS, but the generated
                                // accessor only offers the Table form.

import battlecode.schema.*;

import java.io.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.zip.GZIPInputStream;

/**
 * Turns a .bc25 replay into a human-readable transcript, including ASCII
 * renderings of the arena.
 *
 * SHARED TOOL. This is the one replay dumper for the project; the three
 * lineages previously kept their own, which drifted apart and duplicated the
 * same flatbuffer plumbing three times. It reports only ENGINE-LEVEL facts, and
 * prints indicator strings verbatim without interpreting any bot's private
 * encoding, so nothing here is specific to a lineage.
 *
 * WHAT IT PRINTS
 *   - headers: map name, size, symmetry, wall density, ruin count, spawns
 *   - per-sample team aggregates: money, coverage, SRP count, alive units by
 *     type, tower paint pool, action counts, spawns, deaths, starvations
 *   - every tower spawn and upgrade, and every death
 *   - an optional detailed action window and a per-robot track
 *   - ASCII arena views (see below)
 *
 * ASCII VIEWS  (--map N, or --map-at R)
 *   terrain+paint+units in one grid, plus separate paint and mark grids with
 *   --views. Legend is printed with each frame.
 *
 * RECONSTRUCTION AND ITS LIMIT -- READ THIS BEFORE TRUSTING A PAINT VIEW.
 * Round carries no tile state, so tile paint is rebuilt from the initial map
 * plus every PaintAction/UnpaintAction, which carry exact locations.
 * SplashAction carries only its CENTRE, and the splash footprint is not in the
 * schema, so splashed tiles are NOT applied to the grid. Rather than hide that,
 * every frame prints reconstructed coverage beside the engine's own
 * teamCoverageAmounts and flags the gap. A small gap is splash; a large one
 * means the reconstruction is wrong and the view should not be believed. Splash
 * centres are marked '*' so you can see where the missing paint went.
 *
 * Usage: ReplayDump <file.bc25> [flags]
 *   --from R --to R   detailed action log window
 *   --robot ID        per-turn track of one robot
 *   --every N         aggregate sampling stride (default 25)
 *   --map N           render the arena every N rounds (0 = off, default)
 *   --map-at R        render the arena once, at round R (repeatable)
 *   --views           with --map/--map-at, also print separate paint and mark grids
 *   --quiet           suppress per-round aggregates (useful with --map)
 */
public class DenialProbe {
    // ===================== BOB'S DENIAL-UTILISATION PROBE =====================
    // Derived from the shared ReplayDump (coordinator-owned; NOT modified there).
    // Question it answers: my moppers/splashers act at ~1% of their action
    // ceiling. Is that because they never HAVE a target, or because they have
    // one and do not act on it? Those are different bugs with different fixes,
    // and the raw rate cannot tell them apart.
    //
    // The denominator is the thing my earlier instrument got wrong. Every living
    // robot emits exactly one Turn per round, so counting Turns of a type gives
    // unit-rounds exactly -- no cumulative-over-instantaneous mismatch.
    //
    // Slots: 0 = MOPPER, 1 = SPLASHER. Teams are 1-based.
    static long[][] dRounds = new long[4][2];      // unit-rounds alive
    static long[][] dReady = new long[4][2];       // ... with action off cooldown
    static long[][] dVis = new long[4][2];         // ... with enemy paint in VISION (r2<=20)
    static long[][] dInRange = new long[4][2];     // ... with enemy paint in ACTION range
    static long[][] dReadyVis = new long[4][2];
    static long[][] dReadyInRange = new long[4][2];// the true "could have denied" denominator
    static long[][] dActed = new long[4][2];       // took ANY action this turn
    static long[][] dDenied = new long[4][2];      // took an UNPAINT (mopper) / SPLASH (splasher)
    static long[][] dPainted = new long[4][2];     // splashers painting: PaintAction
    static long[][] dActedInRange = new long[4][2];// acted WHILE a denial target was in range
    static long[][] dIdleNoTarget = new long[4][2];// off cooldown, nothing even in VISION -- traversing
    static long[][] dSpawned = new long[4][2];     // total denial units ever spawned
    static long[][] dAliveEnd = new long[4][2];    // still alive at the last round seen
    static int lastRoundSeen = 0;
    static int curSlot = -1, curTeam = -1;
    static boolean curReady = false, curInRange = false, curActed = false, curDenied = false;

    static boolean anyEnemyPaint(int cx, int cy, int enemyTeam, int r2) {
        int r = (int) Math.sqrt(r2);
        for (int dy = -r; dy <= r; dy++)
            for (int dx = -r; dx <= r; dx++) {
                if (dx * dx + dy * dy > r2) continue;
                int x = cx + dx, y = cy + dy;
                if (x < 0 || y < 0 || x >= mapWidth || y >= mapHeight) continue;
                int idx = y * mapWidth + x;
                if (wall[idx]) continue;
                if (paintTeam(paint[idx]) == enemyTeam) return true;
            }
        return false;
    }

    static void flushDenialTurn() {
        if (curSlot < 0) return;
        if (curActed) { dActed[curTeam][curSlot]++; if (curInRange) dActedInRange[curTeam][curSlot]++; }
        if (curDenied) dDenied[curTeam][curSlot]++;
        curSlot = -1; curActed = false; curDenied = false;
    }

    static void printDenialReport() {
        String[] nm = {"MOPPER  ", "SPLASHER"};
        double[] ceil = {1.0 / 3.0, 1.0 / 5.0};   // cd 30 and 50, regen 10/round
        System.out.println();
        System.out.println("=== DENIAL UTILISATION ===");
        System.out.println("  rate = actions / unit-rounds.  ceiling = 1/(cooldown/10).");
        System.out.printf("  %-4s %-8s %8s %8s %8s %8s %8s | %8s %8s %8s%n",
                "team", "type", "rounds", "ready", "vis", "inRange", "rdy&inR",
                "acted", "denied", "act/rnd");
        for (int t = 1; t <= 2; t++)
            for (int s = 0; s < 2; s++) {
                long n = dRounds[t][s];
                if (n == 0) continue;
                System.out.printf("  T%-3d %-8s %8d %8d %8d %8d %8d | %8d %8d %8.4f%n",
                        t, nm[s], n, dReady[t][s], dVis[t][s], dInRange[t][s], dReadyInRange[t][s],
                        dActed[t][s], dDenied[t][s], (double) dActed[t][s] / n);
            }
        System.out.println();
        System.out.println("  THE DISCRIMINATING RATIOS");
        System.out.println("  NB actionCooldown in a Turn is the POST-action value (verified on a");
        System.out.println("     tracked mopper: it reads 30 on exactly the rounds it UNPAINTs), so");
        System.out.println("     'ready' means ENDED the turn able to act and did NOT act. The");
        System.out.println("     opportunity denominator is therefore actedInRange + readyInRange.");
        for (int t = 1; t <= 2; t++)
            for (int s2 = 0; s2 < 2; s2++) {
                long n = dRounds[t][s2];
                if (n == 0) continue;
                double pctCeil = 100.0 * ((double) dActed[t][s2] / n) / ceil[s2];
                long opp = dActedInRange[t][s2] + dReadyInRange[t][s2];
                double take = opp == 0 ? Double.NaN : 100.0 * dActedInRange[t][s2] / opp;
                System.out.printf("  T%d %s  utilisation %5.1f%% of ceiling | target IN RANGE %5.1f%% of rounds"
                                + " | TAKE-RATE %5.1f%% (%d taken / %d opportunities)"
                                + " | idle with nothing in vision %5.1f%%%n",
                        t, nm[s2], pctCeil, 100.0 * dInRange[t][s2] / n, take,
                        dActedInRange[t][s2], opp, 100.0 * dIdleNoTarget[t][s2] / n);
            }
        System.out.println();
        System.out.println("  WHICH DENOMINATOR PRODUCES THE OLD ~0.004 FIGURE?");
        System.out.printf("  final round = %d%n", lastRoundSeen);
        for (int t = 1; t <= 2; t++)
            for (int s2 = 0; s2 < 2; s2++) {
                long n = dRounds[t][s2];
                if (n == 0) continue;
                long sp = Math.max(1, dSpawned[t][s2]);
                double aTrue = (double) dActed[t][s2] / n;
                double bSpawnRounds = (double) dActed[t][s2] / (sp * (double) lastRoundSeen);
                System.out.printf("  T%d %s  acted=%d | TRUE unit-rounds=%d -> %.4f | spawned=%d x rounds=%d -> %.4f%n",
                        t, nm[s2], dActed[t][s2], n, aTrue, sp, lastRoundSeen, bSpawnRounds);
            }
        System.out.println();
        System.out.println("  READ: low utilisation + low 'in RANGE' = a TARGET-AVAILABILITY problem");
        System.out.println("        (composition / where the units are), not a piloting one.");
        System.out.println("        Low utilisation + high 'in RANGE' + low 'denies when ready AND in");
        System.out.println("        range' = the unit is standing on a target and declining to act.");
        System.out.println("  CAVEAT: splash footprints are not in the schema, so the paint grid");
        System.out.println("        under-models splasher-cleared tiles; check the coverage gap above.");
    }
    // =========================== end of probe ================================

    static Map<Integer, String> label = new HashMap<>();
    static Map<Integer, Integer> teamOf = new HashMap<>();
    static Map<Integer, Byte> typeOf = new HashMap<>();
    static Map<Integer, int[]> posOf = new HashMap<>();      // id -> {x,y}, for the units view
    static int mapWidth = -1, mapHeight = -1;
    static int fromRound = Integer.MAX_VALUE, toRound = -1;
    static int trackRobot = -1;
    static int every = 25;
    static int mapEvery = 0;
    static boolean views = false, quiet = false;
    static Set<Integer> mapAt = new TreeSet<>();

    // --- reconstructed board state -------------------------------------------
    static boolean[] wall;
    static boolean[] ruin;
    static byte[] paint;      // engine encoding, straight from GameMap.paint()
    static byte[] mark;       // 0 = none, else same encoding as paint
    static Set<Integer> splashCentres = new HashSet<>();
    static long splashCount = 0;

    // per-sample-period per-team action counters
    static long[] paints = new long[4], unpaints = new long[4], attacks = new long[4],
                  splashes = new long[4], mops = new long[4];
    // Deaths and spawns per sample period. Robot deaths arrive as Action.DieAction
    // inside a Turn, NOT via Round.diedIds -- which carries none of them. A dumper
    // that trusts diedIds never decrements its alive counts, and every "alive"
    // figure it prints is cumulative spawns instead.
    static long[] deaths = new long[4], spawnSold = new long[4], spawnMop = new long[4], spawnSpl = new long[4];
    static long[] xfers = new long[4];
    // Death-cause classification. DieType carries only UNKNOWN/EXCEPTION, so cause is
    // derived: a robot at 0 paint takes damage every turn and dies of starvation, so
    // its last observed paint distinguishes that from being killed.
    static Map<Integer, Integer> lastPaint = new HashMap<>();
    static long[] starved = new long[4];
    static int[] engineCoverage = new int[4];

    public static void main(String[] args) throws Exception {
        for (int i = 1; i < args.length; i++) {
            String flag = args[i];
            if (flag.equals("--views")) { views = true; continue; }
            if (flag.equals("--quiet")) { quiet = true; continue; }
            if (i + 1 >= args.length) throw new IllegalArgumentException("flag " + flag + " needs a value");
            String val = args[++i];
            switch (flag) {
                case "--from": fromRound = Integer.parseInt(val); break;
                case "--to": toRound = Integer.parseInt(val); break;
                case "--robot": trackRobot = Integer.parseInt(val); break;
                case "--every": every = Integer.parseInt(val); break;
                case "--map": mapEvery = Integer.parseInt(val); break;
                case "--map-at": mapAt.add(Integer.parseInt(val)); break;
                default: throw new IllegalArgumentException("unknown flag: " + flag);
            }
        }
        byte[] raw = readAll(args[0]);
        byte[] bytes;
        if (raw.length > 2 && (raw[0] & 0xff) == 0x1f && (raw[1] & 0xff) == 0x8b) {
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            try (GZIPInputStream gz = new GZIPInputStream(new ByteArrayInputStream(raw))) {
                gz.transferTo(bos);
            }
            bytes = bos.toByteArray();
        } else bytes = raw;

        GameWrapper gw = GameWrapper.getRootAsGameWrapper(ByteBuffer.wrap(bytes));
        for (int i = 0; i < gw.eventsLength(); i++) {
            EventWrapper ew = gw.events(i);
            byte t = ew.eType();
            if (t == Event.GameHeader) {
                GameHeader gh = (GameHeader) ew.e(new GameHeader());
                StringBuilder sb = new StringBuilder("=== GameHeader");
                for (int k = 0; k < gh.teamsLength(); k++) {
                    TeamData td = gh.teams(k);
                    sb.append("  team").append(td.teamId()).append("=").append(td.packageName());
                }
                System.out.println(sb);
            } else if (t == Event.MatchHeader) {
                readMatchHeader((MatchHeader) ew.e(new MatchHeader()));
            } else if (t == Event.Round) {
                Round r = (Round) ew.e(new Round());
                int round = r.roundId();
                boolean inWindow = round >= fromRound && round <= toRound;
                for (int ti = 0; ti < r.turnsLength(); ti++) dumpTurn(r.turns(ti), round, inWindow);
                for (int k = 0; k < r.diedIdsLength(); k++) {
                    int id = r.diedIds(k);
                    System.out.println("round " + round + " DIED " + lbl(id));
                    teamOf.remove(id); posOf.remove(id);
                }
                for (int k = 0; k < r.teamIdsLength(); k++) engineCoverage[r.teamIds(k)] = r.teamCoverageAmounts(k);

                if (!quiet && (round % every == 0 || round <= 3 || inWindow)) printAggregates(r, round);
                if ((mapEvery > 0 && round % mapEvery == 0) || mapAt.contains(round)) renderArena(round);
            } else if (t == Event.MatchFooter) {
                MatchFooter mf = (MatchFooter) ew.e(new MatchFooter());
                flushDenialTurn(); printDenialReport(); System.out.println("=== MatchFooter winner=team" + mf.winner()
                        + " winType=" + WinType.name(mf.winType()) + " rounds=" + mf.totalRounds());
                for (int k = 0; k < mf.timelineMarkersLength(); k++) {
                    TimelineMarker tm = mf.timelineMarkers(k);
                    System.out.println("  marker r" + tm.round() + " team" + tm.team() + " " + tm.label());
                }
            }
        }
    }

    static void readMatchHeader(MatchHeader mh) {
        GameMap map = mh.map();
        mapWidth = map.size().x();
        mapHeight = map.size().y();
        int tiles = mapWidth * mapHeight;
        wall = new boolean[tiles];
        ruin = new boolean[tiles];
        paint = new byte[tiles];
        mark = new byte[tiles];
        int wallN = 0;
        for (int w = 0; w < map.wallsLength() && w < tiles; w++) if (map.walls(w)) { wall[w] = true; wallN++; }
        for (int p = 0; p < tiles && p < map.paintLength(); p++) paint[p] = map.paint(p);
        int ruinN = 0;
        if (map.ruins() != null) {
            ruinN = map.ruins().xsLength();
            for (int k = 0; k < ruinN; k++) {
                int idx = map.ruins().ys(k) * mapWidth + map.ruins().xs(k);
                if (idx >= 0 && idx < tiles) ruin[idx] = true;
            }
        }
        // Wall density and ruin count decide whether a target-seeking unit can get
        // trapped and how far tower expansion can go, so they are printed here
        // rather than re-derived per investigation.
        System.out.println("=== MatchHeader map=" + map.name() + " " + mapWidth + "x" + mapHeight
                + " symmetry=" + map.symmetry() + " maxRounds=" + mh.maxRounds()
                + " walls=" + wallN + "/" + tiles
                + String.format(" (%.1f%%)", 100.0 * wallN / Math.max(1, tiles))
                + " ruins=" + ruinN);
        InitialBodyTable ibt = map.initialBodies();
        if (ibt != null) {
            for (int k = 0; k < ibt.spawnActionsLength(); k++) {
                SpawnAction sp = ibt.spawnActions(k);
                register(sp);
                posOf.put(sp.id(), new int[]{sp.x(), sp.y()});
                paintTowerTile(sp);
                System.out.println("  initial " + label.get(sp.id()) + " at (" + sp.x() + "," + sp.y() + ")");
            }
        }
    }

    static void printAggregates(Round r, int round) {
        StringBuilder sb = new StringBuilder("round " + round);
        for (int k = 0; k < r.teamIdsLength(); k++) {
            int tid = r.teamIds(k);
            int[] alive = aliveCounts(tid);
            sb.append(" | T").append(tid)
              .append(" $").append(r.teamResourceAmounts(k))
              .append(" cov").append(r.teamCoverageAmounts(k))
              .append("m srp").append(r.teamResourcePatternAmounts(k))
              .append(" sold").append(alive[0]).append(" spl").append(alive[1])
              .append(" mop").append(alive[2]).append(" tw").append(alive[3]).append(" twPaint").append(towerPaint(tid))
              .append(" acts[p").append(paints[tid]).append(" u").append(unpaints[tid])
              .append(" a").append(attacks[tid]).append(" s").append(splashes[tid])
              .append(" m").append(mops[tid]).append("]")
              .append(" +sold").append(spawnSold[tid]).append(" +mop").append(spawnMop[tid]).append(" +spl").append(spawnSpl[tid])
              .append(" died").append(deaths[tid])
              .append(" xfer").append(xfers[tid])
              .append(" starved").append(starved[tid]);
        }
        System.out.println(sb);
        Arrays.fill(paints, 0); Arrays.fill(unpaints, 0); Arrays.fill(attacks, 0);
        Arrays.fill(splashes, 0); Arrays.fill(mops, 0);
        Arrays.fill(deaths, 0); Arrays.fill(spawnSold, 0); Arrays.fill(spawnMop, 0); Arrays.fill(spawnSpl, 0);
        Arrays.fill(xfers, 0); Arrays.fill(starved, 0);
    }

    // ---------------------------------------------------------------- rendering

    /** Paint/mark byte encoding. TEAMS ARE 1-BASED throughout the schema
     *  (team1/team2), and the tile encoding follows: 0 empty, then each team's
     *  primary and secondary in order -- team1 = 1,2 and team2 = 3,4. Getting this
     *  wrong is not subtle but it IS silent on the grid, which is why the coverage
     *  self-check below exists: the first version of this tool mixed 0- and 1-based
     *  teams, and the check caught it by attributing the map's initial paint to a
     *  team that does not exist. */
    static byte paintCode(int team, boolean secondary) { return (byte) ((team - 1) * 2 + 1 + (secondary ? 1 : 0)); }
    static int paintTeam(byte p) { return p == 0 ? -1 : (p - 1) / 2 + 1; }
    static boolean paintSecondary(byte p) { return p != 0 && ((p - 1) % 2) == 1; }

    static char terrainChar(int idx) {
        if (wall[idx]) return '#';
        if (ruin[idx]) return 'o';
        return '.';
    }

    static char paintChar(int idx) {
        byte p = paint[idx];
        if (p == 0) return terrainChar(idx);
        int team = paintTeam(p);
        char c = team == 1 ? 'a' : 'b';
        return paintSecondary(p) ? Character.toUpperCase(c) : c;
    }

    static void renderArena(int round) {
        if (paint == null) return;
        // Units drawn on top of paint; towers take precedence over mobile units.
        Map<Integer, Character> overlay = new HashMap<>();
        for (Map.Entry<Integer, int[]> e : posOf.entrySet()) {
            Integer team = teamOf.get(e.getKey());
            if (team == null) continue;
            Byte ty = typeOf.get(e.getKey());
            if (ty == null) continue;
            int idx = e.getValue()[1] * mapWidth + e.getValue()[0];
            if (idx < 0 || idx >= paint.length) continue;
            char c;
            boolean tower = ty == RobotType.PAINT_TOWER || ty == RobotType.MONEY_TOWER || ty == RobotType.DEFENSE_TOWER;
            // Tower and mobile letters MUST stay disjoint. Case encodes the team,
            // so any letter shared between a tower and a mobile unit is ambiguous:
            // with towers P/M/D and mobiles s/m/p, 'M' meant BOTH a team-1 money
            // tower and a team-2 mopper. On Gears r800 ten cells rendered 'M' and
            // only five were money towers -- the grid was not wrong, it was
            // unreadable, which is worse because it still looks like an answer.
            // Towers t/n/d, mobiles s/m/p: no letter appears in both sets.
            if (tower) c = ty == RobotType.PAINT_TOWER ? 't' : ty == RobotType.MONEY_TOWER ? 'n' : 'd';
            else if (ty == RobotType.SOLDIER) c = 's';
            else if (ty == RobotType.MOPPER) c = 'm';
            else c = 'p';
            if (team == 2) c = Character.toUpperCase(c);   // one rule for both kinds
            Character prev = overlay.get(idx);
            if (prev == null || (tower && Character.isLetter(prev))) overlay.put(idx, c);
        }

        System.out.println();
        System.out.println("=== ARENA round " + round + "  " + mapWidth + "x" + mapHeight);
        System.out.println("    terrain . empty   # wall   o ruin");
        System.out.println("    paint   a/A team1 primary/secondary    b/B team2 primary/secondary");
        System.out.println("    towers  t paint  n money  d defense");
        System.out.println("    mobile  s soldier  m mopper  p splasher");
        System.out.println("            team1 lower-case, team2 UPPER-CASE -- one rule for both rows,");
        System.out.println("            and the two letter sets are disjoint so no glyph is ambiguous");
        System.out.println("            * splash centre this frame (its footprint is NOT in the paint grid)");
        System.out.println("    NOTE units OCCLUDE the paint beneath them in this grid, so an unpainted tile");
        System.out.println("         with a robot on it reads as a unit. DO NOT census paint by counting");
        System.out.println("         characters here -- use the exact census printed below, or --views for");
        System.out.println("         the paint-only grid.");
        printGrid(idx -> {
            Character o = overlay.get(idx);
            if (o != null) return o;
            if (splashCentres.contains(idx)) return '*';
            return paintChar(idx);
        });
        coverageCheck(round);
        if (views) {
            System.out.println("--- paint only (units hidden) ---");
            printGrid(DenialProbe::paintChar);
            System.out.println("--- marks only ('.' none, m/M team1 pri/sec, n/N team2) ---");
            printGrid(idx -> {
                byte mk = mark[idx];
                if (mk == 0) return terrainChar(idx);
                int team = paintTeam(mk);
                char c = team == 1 ? 'm' : 'n';
                return paintSecondary(mk) ? Character.toUpperCase(c) : c;
            });
        }
        splashCentres.clear();
    }

    interface CellFn { char at(int idx); }

    static void printGrid(CellFn fn) {
        // Column ruler every 10 columns, so a coordinate can be read off directly.
        StringBuilder ruler = new StringBuilder("     ");
        for (int x = 0; x < mapWidth; x++) ruler.append(x % 10 == 0 ? String.valueOf((x / 10) % 10) : ' ');
        System.out.println(ruler);
        for (int y = mapHeight - 1; y >= 0; y--) {   // y increases upward, as in the client
            StringBuilder sb = new StringBuilder(String.format("%4d ", y));
            for (int x = 0; x < mapWidth; x++) sb.append(fn.at(y * mapWidth + x));
            System.out.println(sb);
        }
    }

    /** Close the accounting before anyone reads the grid: compare reconstructed
     *  coverage against the engine's own figure for the same round, and print an
     *  EXACT tile census.
     *
     *  The census exists because the combined grid overlays units on paint, so
     *  counting characters there undercounts empty tiles by however many robots
     *  are standing on them -- a reader once got 116 by eye against ~149 from
     *  arithmetic, and both were defensible from what was on screen. Counting
     *  from the arrays removes the question. */
    static void coverageCheck(int round) {
        int tiles = mapWidth * mapHeight;
        int[] mine = new int[4];
        int empty = 0, walls = 0, ruins = 0;
        for (int i = 0; i < tiles; i++) {
            if (wall[i]) walls++;
            else if (paint[i] == 0) { empty++; if (ruin[i]) ruins++; }
            int tm = paintTeam(paint[i]);
            if (tm >= 1 && tm < 4) mine[tm]++;
        }
        System.out.printf("    census  %d tiles = %d painted (T1 %d, T2 %d) + %d unpainted + %d wall"
                        + "   [%d unpainted tiles are ruins]%n",
                tiles, mine[1] + mine[2], mine[1], mine[2], empty, walls, ruins);
        // Denominator is PASSABLE area, not total. Proved by contradiction rather
        // than by fit: on Gears (140/3025 walls) the engine's two team figures sum
        // to 989 per-mille, which total area caps at 2885/3025 = 954. A sum cannot
        // exceed its own bound, so the walls are not in the denominator.
        // The earlier claim that it was total area was "verified" on a map with
        // 2.6% walls, where the two candidates differ by 2 per-mille -- inside the
        // gap that unmodelled splashes already produce. A check that cannot
        // separate the hypotheses is not a check.
        int passable = Math.max(1, tiles - walls);
        StringBuilder sb = new StringBuilder("    coverage per-mille  ");
        boolean bad = false;
        for (int tm = 1; tm <= 2; tm++) {
            int recon = (int) Math.round(1000.0 * mine[tm] / passable);
            int eng = engineCoverage[tm];
            int gap = recon - eng;
            if (Math.abs(gap) > 15) bad = true;   // was 40, which hid the 18-22 denominator error
            sb.append("T").append(tm).append(" recon=").append(recon)
              .append(" engine=").append(eng).append(" gap=").append(gap >= 0 ? "+" : "").append(gap).append("  ");
        }
        System.out.println(sb);
        System.out.println("    (" + splashCount + " splashes so far are unmodelled -- a gap of a few per-mille is"
                + (bad ? " NOT enough to explain this one: TREAT THE PAINT GRID AS UNRELIABLE)" : " expected)"));
    }

    // ---------------------------------------------------------------- per-turn

    static void register(SpawnAction sp) {
        label.put(sp.id(), "id" + sp.id() + "(T" + sp.team() + "," + RobotType.name(sp.robotType()) + ")");
        teamOf.put(sp.id(), (int) sp.team());
        typeOf.put(sp.id(), sp.robotType());
    }

    /** A tower's own tile is painted by the engine when the tower appears, not via a
     *  PaintAction, so reconstruction misses it unless it is applied here. Found by
     *  the coverage self-check: without this the gap sat at exactly -2 per-mille for
     *  BOTH teams at every round of a game with no splashes -- about 2 tiles, which
     *  is the two starting towers. */
    static void paintTowerTile(SpawnAction sp) {
        byte ty = sp.robotType();
        boolean tower = ty == RobotType.PAINT_TOWER || ty == RobotType.MONEY_TOWER || ty == RobotType.DEFENSE_TOWER;
        if (!tower || paint == null) return;
        int idx = sp.y() * mapWidth + sp.x();
        if (idx >= 0 && idx < paint.length) paint[idx] = paintCode(sp.team(), false);
    }

    static String lbl(int id) {
        String s = label.get(id);
        return s == null ? ("id" + id) : s;
    }

    static int[] aliveCounts(int tid) {
        int[] c = new int[4]; // soldier, splasher, mopper, tower
        for (Map.Entry<Integer, Integer> e : teamOf.entrySet()) {
            if (e.getValue() != tid) continue;
            byte ty = typeOf.get(e.getKey());
            if (ty == RobotType.SOLDIER) c[0]++;
            else if (ty == RobotType.SPLASHER) c[1]++;
            else if (ty == RobotType.MOPPER) c[2]++;
            else c[3]++;
        }
        return c;
    }

    /** Total paint across a team's towers -- the shared pool that funds spawning and
     *  any tower-to-robot transfer. A change that alters who draws on a contested
     *  pool should instrument the pool itself in its first run. */
    static int towerPaint(int tid) {
        int sum = 0;
        for (Map.Entry<Integer, Integer> e : teamOf.entrySet()) {
            if (e.getValue() != tid) continue;
            byte ty = typeOf.get(e.getKey());
            if (ty == RobotType.SOLDIER || ty == RobotType.SPLASHER || ty == RobotType.MOPPER) continue;
            Integer p = lastPaint.get(e.getKey());
            if (p != null) sum += p;
        }
        return sum;
    }

    static String loc(int l) { return "(" + (l % mapWidth) + "," + (l / mapWidth) + ")"; }

    static void dumpTurn(Turn turn, int round, boolean print) {
        if (round > lastRoundSeen) lastRoundSeen = round;
        int id = turn.robotId();
        Integer team = teamOf.get(id);
        int tid = team == null ? 1 : team;
        posOf.put(id, new int[]{turn.x(), turn.y()});
        if (trackRobot >= 0 && id == trackRobot) {
            System.out.println("round " + round + " TRACK " + lbl(id) + " (" + turn.x() + "," + turn.y()
                    + ") hp=" + turn.health() + " paint=" + turn.paint()
                    + " mCD=" + turn.moveCooldown() + " aCD=" + turn.actionCooldown()
                    + " bc=" + turn.bytecodesUsed());
        }
        lastPaint.put(id, turn.paint());
        // --- probe: classify this denial unit's turn BEFORE its actions apply ---
        flushDenialTurn();
        Byte pty = typeOf.get(id);
        boolean pIsMop = pty != null && pty == RobotType.MOPPER;
        boolean pIsSpl = pty != null && pty == RobotType.SPLASHER;
        if ((pIsMop || pIsSpl) && paint != null && tid >= 1 && tid <= 2) {
            curSlot = pIsMop ? 0 : 1;
            curTeam = tid;
            int enemy = 3 - tid;
            curReady = turn.actionCooldown() < 10;
            boolean vis = anyEnemyPaint(turn.x(), turn.y(), enemy, 20);
            curInRange = anyEnemyPaint(turn.x(), turn.y(), enemy, pIsMop ? 2 : 4);
            dRounds[tid][curSlot]++;
            if (curReady) dReady[tid][curSlot]++;
            if (vis) dVis[tid][curSlot]++;
            if (curInRange) dInRange[tid][curSlot]++;
            if (curReady && vis) dReadyVis[tid][curSlot]++;
            if (curReady && !vis) dIdleNoTarget[tid][curSlot]++;
            if (curReady && curInRange) dReadyInRange[tid][curSlot]++;
        }
        int o = turn.__offset(22); // actions union vector
        if (o == 0) return;
        int len = turn.__vector_len(o);
        int vecStart = turn.__vector(o);
        ByteBuffer bb = turn.getByteBuffer();
        for (int j = 0; j < len; j++) {
            byte at = turn.actionsType(j);
            int pos = Table.__indirect(vecStart + j * 4, bb);
            switch (at) {
                case Action.SpawnAction: {
                    SpawnAction sp = new SpawnAction(); sp.__init(pos, bb);
                    boolean tower = sp.robotType() == RobotType.PAINT_TOWER
                            || sp.robotType() == RobotType.MONEY_TOWER || sp.robotType() == RobotType.DEFENSE_TOWER;
                    register(sp);
                    posOf.put(sp.id(), new int[]{sp.x(), sp.y()});
                    paintTowerTile(sp);
                    if (!tower) {
                        int st = sp.team();
                        if (sp.robotType() == RobotType.SOLDIER) spawnSold[st]++;
                        else if (sp.robotType() == RobotType.MOPPER) { spawnMop[st]++; if (st>=1&&st<=2) dSpawned[st][0]++; }
                        else if (sp.robotType() == RobotType.SPLASHER) { spawnSpl[st]++; if (st>=1&&st<=2) dSpawned[st][1]++; }
                    }
                    if (print || tower)
                        System.out.println("round " + round + " " + lbl(id) + " SPAWN " + label.get(sp.id())
                                + " at (" + sp.x() + "," + sp.y() + ")");
                    break;
                }
                case Action.UpgradeAction: {
                    UpgradeAction u = new UpgradeAction(); u.__init(pos, bb);
                    System.out.println("round " + round + " UPGRADE " + lbl(u.id()) + " hp->" + u.newMaxHealth());
                    break;
                }
                case Action.PaintAction: {
                    paints[tid]++; if (curSlot >= 0) { curActed = true; dPainted[curTeam][curSlot]++; }
                    PaintAction pa = new PaintAction(); pa.__init(pos, bb);
                    int idx = pa.loc();
                    if (paint != null && idx >= 0 && idx < paint.length)
                        paint[idx] = paintCode(tid, pa.isSecondary() != 0);
                    if (print) System.out.println("round " + round + " " + lbl(id) + " PAINT " + loc(idx)
                            + (pa.isSecondary() != 0 ? " secondary" : ""));
                    break;
                }
                case Action.UnpaintAction: {
                    unpaints[tid]++; curActed = true; if (curSlot == 0) curDenied = true;
                    UnpaintAction ua = new UnpaintAction(); ua.__init(pos, bb);
                    int idx = ua.loc();
                    if (paint != null && idx >= 0 && idx < paint.length) paint[idx] = 0;
                    if (print) System.out.println("round " + round + " " + lbl(id) + " UNPAINT " + loc(idx));
                    break;
                }
                case Action.MarkAction: {
                    MarkAction ma = new MarkAction(); ma.__init(pos, bb);
                    int idx = ma.loc();
                    if (mark != null && idx >= 0 && idx < mark.length)
                        mark[idx] = paintCode(tid, ma.isSecondary() != 0);
                    if (print) System.out.println("round " + round + " " + lbl(id) + " MARK " + loc(idx));
                    break;
                }
                case Action.UnmarkAction: {
                    UnmarkAction ua = new UnmarkAction(); ua.__init(pos, bb);
                    int idx = ua.loc();
                    if (mark != null && idx >= 0 && idx < mark.length) mark[idx] = 0;
                    if (print) System.out.println("round " + round + " " + lbl(id) + " UNMARK " + loc(idx));
                    break;
                }
                case Action.SplashAction: {
                    splashes[tid]++; splashCount++; curActed = true; if (curSlot == 1) curDenied = true;
                    SplashAction s = new SplashAction(); s.__init(pos, bb);
                    if (splashCentres != null) splashCentres.add(s.loc());
                    if (print) System.out.println("round " + round + " " + lbl(id) + " SPLASH " + loc(s.loc()));
                    break;
                }
                case Action.AttackAction: {
                    attacks[tid]++; curActed = true;
                    if (print) {
                        AttackAction a = new AttackAction(); a.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " ATTACK -> " + lbl(a.id()));
                    }
                    break;
                }
                case Action.MopAction: mops[tid]++; curActed = true; break;
                case Action.DamageAction: {
                    if (print) {
                        DamageAction d = new DamageAction(); d.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " DAMAGE " + lbl(d.id()) + " -" + d.damage());
                    }
                    break;
                }
                case Action.DieAction: {
                    DieAction d = new DieAction(); d.__init(pos, bb);
                    if (d.dieType() == DieType.EXCEPTION)
                        System.out.println("round " + round + " DIE-EXCEPTION " + lbl(d.id()));
                    Integer dt = teamOf.get(d.id());
                    if (dt != null) {
                        deaths[dt]++;
                        Integer lp = lastPaint.get(d.id());
                        if (lp != null && lp <= 0) starved[dt]++;
                    }
                    if (print) System.out.println("round " + round + " DIED " + lbl(d.id()));
                    teamOf.remove(d.id()); posOf.remove(d.id());
                    break;
                }
                case Action.TransferAction: {
                    xfers[tid]++;
                    if (print) {
                        TransferAction tr = new TransferAction(); tr.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " TRANSFER " + tr.amount() + " -> " + lbl(tr.id()));
                    }
                    break;
                }
                case Action.MessageAction: {
                    if (print) {
                        MessageAction m = new MessageAction(); m.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " MSG " + m.data() + " -> " + lbl(m.id()));
                    }
                    break;
                }
                case Action.IndicatorStringAction: {
                    // Printed verbatim. This tool never interprets a bot's private
                    // indicator encoding -- that would make a shared tool carry one
                    // lineage's internals.
                    if (print) {
                        IndicatorStringAction s = new IndicatorStringAction(); s.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " IND \"" + s.value() + "\"");
                    }
                    break;
                }
                default: break;
            }
        }
    }

    static byte[] readAll(String path) throws IOException {
        try (FileInputStream in = new FileInputStream(path)) { return in.readAllBytes(); }
    }
}
