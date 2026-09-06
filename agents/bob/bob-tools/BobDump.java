// Bob's replay-to-text tool. Reads a .bc25 (gzipped flatbuffer GameWrapper) using
// the engine jar's own schema classes and prints per-round metrics.
// Usage: java -cp .:<engine-jar> BobDump <replay.bc25> [sampleEvery]
import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.util.zip.GZIPInputStream;

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
        System.out.println("round,covA_permil,covB_permil,moneyA,moneyB,srpA,srpB,died,turns");
        int lastPrinted = -1;
        Round lastRound = null;
        for (int i = 0; i < gw.eventsLength(); i++) {
            EventWrapper ew = gw.events(i);
            byte t = ew.eType();
            if (t == Event.Round) {
                Round r = (Round) ew.e(new Round());
                lastRound = r;
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

    static void printRound(Round r) {
        StringBuilder sb = new StringBuilder();
        sb.append(r.roundId());
        for (int j = 0; j < 2; j++) sb.append(',').append(cov(r, j));
        for (int j = 0; j < 2; j++) sb.append(',').append(res(r, j));
        for (int j = 0; j < 2; j++) sb.append(',').append(srp(r, j));
        sb.append(',').append(r.diedIdsLength());
        sb.append(',').append(r.turnsLength());
        System.out.println(sb);
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
