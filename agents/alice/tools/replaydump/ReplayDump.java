package com.google.flatbuffers; // protected Table access needed to read struct-typed
                                // union members out of Turn.actions() (same trick as
                                // the BC26 project's dump tool).

import battlecode.schema.*;

import java.io.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.zip.GZIPInputStream;

/**
 * Turns a .bc25 replay into a human-readable transcript.
 *
 * Default output: per-round-sampled team aggregates (money, coverage per-mille,
 * SRP count, alive units by type, summed robot paint), all deaths, tower
 * spawns/upgrades, and the match footer.
 *
 * Flags (each takes a value):
 *   --from R --to R   detailed action log window (attacks, paints-counts,
 *                     transfers, messages, indicator strings)
 *   --robot ID        per-turn track of one robot (pos, hp, paint, cooldowns)
 *   --every N         aggregate sampling stride (default 25)
 *
 * Usage: ReplayDump <file.bc25> [flags]
 */
public class ReplayDump {
    static Map<Integer, String> label = new HashMap<>();
    static Map<Integer, Integer> teamOf = new HashMap<>();
    static Map<Integer, Byte> typeOf = new HashMap<>();
    static int mapWidth = -1;
    static int fromRound = Integer.MAX_VALUE, toRound = -1;
    static int trackRobot = -1;
    static int every = 25;

    // per-sample-period per-team action counters
    static long[] paints = new long[3], unpaints = new long[3], attacks = new long[3],
                  splashes = new long[3], mops = new long[3];
    // deaths and spawns-by-type per sample period (BUGFIX: robot deaths arrive as
    // Action.DieAction inside a Turn, NOT via Round.diedIds -- which carries none of
    // them. Before this, aliveCounts() never decremented and every "alive" figure in
    // a dump was cumulative spawns. It made the accepted bot look like it fielded
    // more units than the map has tiles.)
    static long[] deaths = new long[3], spawnSold = new long[3], spawnMop = new long[3], spawnSpl = new long[3];
    static long[] xfers = new long[3];   // paint transfers/withdrawals per window
    // Death-cause classification. DieType carries only UNKNOWN/EXCEPTION, so cause is
    // derived: a robot sitting at 0 paint takes -20 HP/turn and dies of starvation, so
    // its last observed paint distinguishes that from being killed.
    static Map<Integer, Integer> lastPaint = new HashMap<>();
    static long[] starved = new long[3];

    public static void main(String[] args) throws Exception {
        for (int i = 1; i < args.length; i++) {
            String flag = args[i];
            if (i + 1 >= args.length) throw new IllegalArgumentException("flag " + flag + " needs a value");
            String val = args[++i];
            switch (flag) {
                case "--from": fromRound = Integer.parseInt(val); break;
                case "--to": toRound = Integer.parseInt(val); break;
                case "--robot": trackRobot = Integer.parseInt(val); break;
                case "--every": every = Integer.parseInt(val); break;
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
                MatchHeader mh = (MatchHeader) ew.e(new MatchHeader());
                GameMap map = mh.map();
                mapWidth = map.size().x();
                int wallN = 0;
                for (int w = 0; w < map.wallsLength(); w++) if (map.walls(w)) wallN++;
                int tiles = map.size().x() * map.size().y();
                int ruinN = map.ruins() != null ? map.ruins().xsLength() : 0;
                // Wall density and ruin count are the two map properties that decide
                // whether a target-seeking unit can get trapped and how far tower
                // expansion can go. Printed so map-class effects are checkable
                // without re-deriving them per investigation.
                System.out.println("=== MatchHeader map=" + map.name() + " " + map.size().x() + "x" + map.size().y()
                        + " symmetry=" + map.symmetry() + " maxRounds=" + mh.maxRounds()
                        + " walls=" + wallN + "/" + tiles
                        + String.format(" (%.1f%%)", 100.0 * wallN / Math.max(1, tiles))
                        + " ruins=" + ruinN);
                InitialBodyTable ibt = map.initialBodies();
                if (ibt != null) {
                    int o2 = ibt.__offset(4); // spawnActions vector of structs
                    for (int k = 0; k < ibt.spawnActionsLength(); k++) {
                        SpawnAction sp = ibt.spawnActions(k);
                        register(sp);
                        System.out.println("  initial " + label.get(sp.id()) + " at (" + sp.x() + "," + sp.y() + ")");
                    }
                }
            } else if (t == Event.Round) {
                Round r = (Round) ew.e(new Round());
                int round = r.roundId();
                boolean inWindow = round >= fromRound && round <= toRound;
                for (int ti = 0; ti < r.turnsLength(); ti++) {
                    Turn turn = r.turns(ti);
                    dumpTurn(turn, round, inWindow);
                }
                for (int k = 0; k < r.diedIdsLength(); k++) {
                    int id = r.diedIds(k);
                    System.out.println("round " + round + " DIED " + lbl(id));
                    teamOf.remove(id); // stop counting as alive
                }
                if (round % every == 0 || round <= 3 || inWindow) {
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
            } else if (t == Event.MatchFooter) {
                MatchFooter mf = (MatchFooter) ew.e(new MatchFooter());
                System.out.println("=== MatchFooter winner=team" + mf.winner()
                        + " winType=" + WinType.name(mf.winType()) + " rounds=" + mf.totalRounds());
                for (int k = 0; k < mf.timelineMarkersLength(); k++) {
                    TimelineMarker tm = mf.timelineMarkers(k);
                    System.out.println("  marker r" + tm.round() + " team" + tm.team() + " " + tm.label());
                }
            }
        }
    }

    static void register(SpawnAction sp) {
        label.put(sp.id(), "id" + sp.id() + "(T" + sp.team() + "," + RobotType.name(sp.robotType()) + ")");
        teamOf.put(sp.id(), (int) sp.team());
        typeOf.put(sp.id(), sp.robotType());
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

    /** Total paint held across a team's towers -- the SHARED POOL that funds both
     *  spawning (200/soldier, 100/mopper) and, from iteration 6, soldier refills.
     *  The algorithm requires instrumenting a contested pool in the first run of any
     *  change that alters who draws on it; three iterations once failed identically
     *  because a global cap was never printed. */
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

    static String loc(int l) {
        return "(" + (l % mapWidth) + "," + (l / mapWidth) + ")";
    }

    static void dumpTurn(Turn turn, int round, boolean print) {
        int id = turn.robotId();
        Integer team = teamOf.get(id);
        int tid = team == null ? 0 : team;
        if (trackRobot >= 0 && id == trackRobot) {
            System.out.println("round " + round + " TRACK " + lbl(id) + " (" + turn.x() + "," + turn.y()
                    + ") hp=" + turn.health() + " paint=" + turn.paint()
                    + " mCD=" + turn.moveCooldown() + " aCD=" + turn.actionCooldown()
                    + " bc=" + turn.bytecodesUsed());
        }
        lastPaint.put(id, turn.paint());
        int o = turn.__offset(22); // actions union vector
        if (o == 0) return;
        int len = turn.__vector_len(o);
        int vecStart = turn.__vector(o);
        ByteBuffer bb = turn.getByteBuffer();
        for (int j = 0; j < len; j++) {
            byte at = turn.actionsType(j);
            int elemOffset = vecStart + j * 4;
            int pos = Table.__indirect(elemOffset, bb);
            switch (at) {
                case Action.SpawnAction: {
                    SpawnAction sp = new SpawnAction(); sp.__init(pos, bb);
                    boolean tower = sp.robotType() == RobotType.PAINT_TOWER
                            || sp.robotType() == RobotType.MONEY_TOWER || sp.robotType() == RobotType.DEFENSE_TOWER;
                    register(sp);
                    if (!tower) {
                        int st = sp.team();
                        if (sp.robotType() == RobotType.SOLDIER) spawnSold[st]++;
                        else if (sp.robotType() == RobotType.MOPPER) spawnMop[st]++;
                        else if (sp.robotType() == RobotType.SPLASHER) spawnSpl[st]++;
                    }
                    if (print || tower)
                        System.out.println("round " + round + " " + lbl(id) + " SPAWN " + label.get(sp.id())
                                + " at (" + sp.x() + "," + sp.y() + ")");
                    break;
                }
                case Action.UpgradeAction: {
                    UpgradeAction u = new UpgradeAction(); u.__init(pos, bb);
                    System.out.println("round " + round + " UPGRADE " + lbl(u.id())
                            + " hp->" + u.newMaxHealth());
                    break;
                }
                case Action.PaintAction: paints[tid]++; break;
                case Action.UnpaintAction: unpaints[tid]++; break;
                case Action.SplashAction: {
                    splashes[tid]++;
                    if (print) {
                        SplashAction s = new SplashAction(); s.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " SPLASH " + loc(s.loc()));
                    }
                    break;
                }
                case Action.AttackAction: {
                    attacks[tid]++;
                    if (print) {
                        AttackAction a = new AttackAction(); a.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " ATTACK -> " + lbl(a.id()));
                    }
                    break;
                }
                case Action.MopAction: mops[tid]++; break;
                case Action.DamageAction: {
                    if (print) {
                        DamageAction d = new DamageAction(); d.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " DAMAGE " + lbl(d.id())
                                + " -" + d.damage());
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
                    teamOf.remove(d.id());
                    break;
                }
                case Action.TransferAction: {
                    xfers[tid]++;
                    if (print) {
                        TransferAction tr = new TransferAction(); tr.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " TRANSFER " + tr.amount()
                                + " -> " + lbl(tr.id()));
                    }
                    break;
                }
                case Action.MessageAction: {
                    if (print) {
                        MessageAction m = new MessageAction(); m.__init(pos, bb);
                        System.out.println("round " + round + " " + lbl(id) + " MSG " + m.data()
                                + " -> " + lbl(m.id()));
                    }
                    break;
                }
                case Action.IndicatorStringAction: {
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
        try (FileInputStream in = new FileInputStream(path)) {
            return in.readAllBytes();
        }
    }
}
