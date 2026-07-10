import { createFileRoute } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useMemo } from "react";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { cn } from "@/lib/utils";

const searchSchema = z.object({
  matchId: fallback(z.string(), "").default(""),
});

export const Route = createFileRoute("/explorer")({
  head: () => ({
    meta: [
      { title: "Match Explorer — The Break Point" },
      { name: "description", content: "Explore every completed 2026 FIFA World Cup match — real scores, venues, and stages." },
      { property: "og:title", content: "Match Explorer — The Break Point" },
      { property: "og:description", content: "2026 FIFA World Cup match-by-match results explorer." },
    ],
  }),
  validateSearch: zodValidator(searchSchema),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("matches2026")),
  component: Page,
});

function Page() {
  const { data } = useData("matches2026");
  const { matchId } = Route.useSearch();
  const navigate = Route.useNavigate();

  const matches = data.matches;
  const ordered = useMemo(
    () => [...matches].sort((a, b) => b.date.localeCompare(a.date)),
    [matches],
  );
  const record = matches.find((m) => m.matchId === matchId) ?? ordered[0];

  if (!record) {
    return (
      <PageTransition>
        <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
          <div className="text-xs uppercase tracking-[0.3em] text-primary">Match Explorer</div>
          <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">No 2026 matches available</h1>
          <p className="mt-3 text-muted-foreground max-w-2xl">{data.note}</p>
        </div>
      </PageTransition>
    );
  }

  const related = ordered.filter((m) => m.stage === record.stage && m.matchId !== record.matchId).slice(0, 8);
  const totalGoals = record.finalScore.home + record.finalScore.away;
  const decided = record.penalties
    ? `Decided on penalties: ${record.homeTeam} ${record.penalties.home}–${record.penalties.away} ${record.awayTeam}`
    : null;

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Match Explorer</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">2026 FIFA World Cup — match detail</h1>

        <div className="mt-4">
          <select
            value={record.matchId}
            onChange={(e) => navigate({ search: { matchId: e.target.value } })}
            className="w-full max-w-2xl rounded-lg border border-border bg-background/60 px-3 py-2 text-sm focus:border-primary focus:outline-none"
          >
            {ordered.map((m) => (
              <option key={m.matchId} value={m.matchId}>
                {m.date} · {m.stage} · {m.homeTeam} {m.finalScore.home}–{m.finalScore.away} {m.awayTeam}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="space-y-6">
            <GlassCard>
              <div className="text-xs uppercase tracking-widest text-muted-foreground">{record.stage} · {record.date}</div>
              <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-4 text-center">
                <div className="flex flex-col items-center gap-2">
                  <span className="text-5xl">{record.homeFlag}</span>
                  <span className="font-display text-xl font-bold">{record.homeTeam}</span>
                </div>
                <div className="font-display text-5xl font-extrabold font-mono-num">
                  {record.finalScore.home}<span className="text-muted-foreground px-2">–</span>{record.finalScore.away}
                </div>
                <div className="flex flex-col items-center gap-2">
                  <span className="text-5xl">{record.awayFlag}</span>
                  <span className="font-display text-xl font-bold">{record.awayTeam}</span>
                </div>
              </div>
              {decided && (
                <div className="mt-4 text-center text-sm font-semibold text-amber-300">{decided}</div>
              )}
            </GlassCard>

            <GlassCard>
              <h3 className="font-display text-lg font-bold">Match facts</h3>
              <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
                <Meta label="Competition" value={record.competition} />
                <Meta label="Stage" value={record.stage} />
                <Meta label="Date" value={record.date} />
                <Meta label="Venue" value={record.venue} />
                <Meta label="City" value={record.city} />
                <Meta label="Total goals" value={totalGoals.toString()} />
              </div>
              <p className="mt-5 text-[11px] text-muted-foreground border-t border-border pt-3">
                Source: {record.source}. Only observed final results are shown — no per-minute trajectory, odds, or radar data is synthesised for 2026 matches.
              </p>
            </GlassCard>

            {record.shockIndex != null && record.expectedGoals && (
              <GlassCard>
                <div className="flex items-baseline justify-between gap-2">
                  <h3 className="font-display text-lg font-bold">Shock index</h3>
                  <span className="font-mono-num text-2xl font-bold text-primary">
                    {record.shockIndex.toFixed(2)}
                    <span className="ml-2 text-xs text-muted-foreground">pctl {record.shockPercentile}</span>
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <Meta label="Model xG (home)" value={record.expectedGoals.home.toFixed(2)} />
                  <Meta label="Model xG (away)" value={record.expectedGoals.away.toFixed(2)} />
                  <Meta label="Actual" value={`${record.finalScore.home}–${record.finalScore.away}`} />
                  <Meta label="Winner's pre-match prob" value={record.winnerPreMatchProb != null ? `${(record.winnerPreMatchProb * 100).toFixed(0)}%` : "—"} />
                </div>
                <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground">
                  <span className="font-semibold text-primary">ELI5:</span> A Poisson model guesses each team's goals
                  from how they've scored so far this tournament. The <span className="font-semibold">shock index</span> is
                  how <em>surprised</em> the model is by the real scoreline — big blowouts and out-of-nowhere results score
                  high, routine 1–0s score low. It measures a surprising <em>scoreline</em>, not necessarily an upset:
                  a tight draw that a favourite lost on penalties won't rank high, because 1–1 itself isn't surprising.
                </div>
              </GlassCard>
            )}
          </div>

          <div className="space-y-6">
            <GlassCard>
              <h3 className="text-xs uppercase tracking-widest text-muted-foreground">Other {record.stage} results</h3>
              <div className="mt-4 space-y-1">
                {related.length === 0 && (
                  <div className="text-xs text-muted-foreground py-4">No other matches in this stage.</div>
                )}
                {related.map((m) => (
                  <button
                    key={m.matchId}
                    type="button"
                    onClick={() => navigate({ search: { matchId: m.matchId } })}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-lg p-2 text-left text-xs transition-colors hover:bg-primary/10",
                    )}
                  >
                    <span className="flex-1 truncate">{m.homeFlag} {m.homeTeam} <span className="font-mono-num font-semibold">{m.finalScore.home}–{m.finalScore.away}</span> {m.awayTeam} {m.awayFlag}</span>
                  </button>
                ))}
              </div>
            </GlassCard>

            <GlassCard>
              <div className="text-xs uppercase tracking-widest text-muted-foreground">About this data</div>
              <p className="mt-3 text-sm text-muted-foreground">
                The 2026 tournament is in progress. This explorer lists the {matches.length} matches completed to date
                ({data.competition}). Statistical anomaly modeling requires event-level and market data not available
                for live 2026 fixtures, so those signals appear only on the Historical and Betting pages.
              </p>
            </GlassCard>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="mt-0.5 font-mono-num text-sm">{value}</div>
    </div>
  );
}
