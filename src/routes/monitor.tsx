import { createFileRoute, Link } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { AnomalyGauge } from "@/components/dashboard/AnomalyGauge";
import { LevelDot } from "@/components/dashboard/StatBadge";
import { cn } from "@/lib/utils";
import { useMemo } from "react";

const searchSchema = z.object({
  stage: fallback(z.string(), "all").default("all"),
  gdp: fallback(z.string(), "all").default("all"),
  level: fallback(z.string(), "all").default("all"),
  sort: fallback(z.string(), "anomaly").default("anomaly"),
});

export const Route = createFileRoute("/monitor")({
  head: () => ({
    meta: [
      { title: "2026 Monitor — The Break Point" },
      { name: "description", content: "Match-by-match anomaly monitoring for the 2026 FIFA World Cup." },
      { property: "og:title", content: "2026 Monitor — The Break Point" },
      { property: "og:description", content: "Live match anomaly index and leaderboard." },
    ],
  }),
  validateSearch: zodValidator(searchSchema),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("matches2026")),
  component: Page,
});

function Page() {
  const { data } = useData("matches2026");
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  const filtered = useMemo(() => {
    let out = [...data];
    if (search.stage !== "all") out = out.filter((m) => m.stage === search.stage);
    if (search.gdp === "b-lead") out = out.filter((m) => (m.home.gdp === "B" || m.away.gdp === "B") && m.home.gdp !== m.away.gdp);
    if (search.gdp === "a-lead") out = out.filter((m) => m.home.gdp === "A" && m.away.gdp === "A");
    if (search.level !== "all") out = out.filter((m) => m.anomalyLevel === search.level);
    if (search.sort === "date") out.sort((a,b) => b.date.localeCompare(a.date));
    else if (search.sort === "swing") out.sort((a,b) => Math.abs(b.winProbSwing) - Math.abs(a.winProbSwing));
    else out.sort((a,b) => b.anomalyIndex - a.anomalyIndex);
    return out;
  }, [data, search]);

  const leaderboard = useMemo(() => [...data].sort((a,b) => b.anomalyIndex - a.anomalyIndex).slice(0, 12), [data]);

  const updateSearch = (patch: Partial<typeof search>) => navigate({ to: ".", search: (prev) => ({ ...prev, ...patch }) });

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">2026 Live Monitor</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">Match-by-match anomaly analysis</h1>
        <p className="mt-2 text-muted-foreground">Every 2026 match scored, filtered, and ranked in real time.</p>

        {/* Filters */}
        <div className="mt-6 glass rounded-xl p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <FilterSelect label="Stage" value={search.stage} onChange={(v) => updateSearch({ stage: v })}
            options={[["all","All Stages"],["Group","Group"],["R16","R16"],["QF","QF"],["SF","SF"],["Final","Final"]]} />
          <FilterSelect label="GDP Group" value={search.gdp} onChange={(v) => updateSearch({ gdp: v })}
            options={[["all","All"],["b-lead","B-involved"],["a-lead","A-only"]]} />
          <FilterSelect label="Anomaly Level" value={search.level} onChange={(v) => updateSearch({ level: v })}
            options={[["all","All Levels"],["high","High"],["moderate","Moderate"],["normal","Normal"]]} />
          <FilterSelect label="Sort" value={search.sort} onChange={(v) => updateSearch({ sort: v })}
            options={[["anomaly","By Anomaly Index"],["date","By Date"],["swing","By Win Prob Swing"]]} />
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_320px]">
          {/* Grid */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 content-start">
            {filtered.map((m) => (
              <Link
                key={m.id}
                to="/explorer"
                search={{ matchId: m.id }}
                className={cn(
                  "glass rounded-2xl p-5 flex flex-col gap-3 transition-all hover:border-primary/50",
                  m.anomalyLevel === "high" && "hover:shadow-[0_0_30px_-8px_#ef4444]",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono-num text-xs text-muted-foreground">{m.date}</span>
                  <span className="rounded-full border border-border bg-background/60 px-2 py-0.5 text-[10px] font-semibold uppercase">
                    {m.stage}{m.group ? ` ${m.group}` : ""}
                  </span>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold flex items-center justify-center gap-2 flex-wrap">
                    <span>{m.home.flag}</span>
                    <span>{m.home.name}</span>
                    <span className="font-mono-num text-2xl mx-2">{m.home.score} - {m.away.score}</span>
                    <span>{m.away.name}</span>
                    <span>{m.away.flag}</span>
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-1 flex justify-center gap-6">
                    <span>Group {m.home.gdp}</span>
                    <span>Group {m.away.gdp}</span>
                  </div>
                </div>
                <div className="flex items-end justify-between pt-2 border-t border-border">
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground">At break</div>
                    <div className="font-mono-num text-sm">{m.breakScore}</div>
                    <div className="mt-2 text-[10px] uppercase tracking-widest text-muted-foreground">WP swing</div>
                    <div className={cn("font-mono-num text-sm", m.winProbSwing > 0 ? "text-amber-400" : "text-emerald-400")}>
                      {m.winProbSwing > 0 ? "+" : ""}{(m.winProbSwing * 100).toFixed(1)}%
                    </div>
                  </div>
                  <AnomalyGauge score={m.anomalyIndex} size={80} />
                </div>
              </Link>
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full text-center text-muted-foreground py-16 text-sm">No matches for these filters.</div>
            )}
          </div>

          {/* Leaderboard */}
          <aside className="glass rounded-2xl p-5 h-fit lg:sticky lg:top-24">
            <div className="text-xs uppercase tracking-widest text-muted-foreground">Anomaly Leaderboard</div>
            <h3 className="mt-1 font-display text-lg font-bold">Top 12 by index</h3>
            <div className="mt-4 space-y-1">
              {leaderboard.map((m, i) => (
                <Link
                  key={m.id}
                  to="/explorer"
                  search={{ matchId: m.id }}
                  className={cn(
                    "flex items-center gap-3 rounded-lg p-2 text-xs hover:bg-primary/10 transition-colors",
                    m.anomalyLevel === "high" && "bg-red-500/5"
                  )}
                >
                  <span className="font-mono-num text-muted-foreground w-4">{i+1}</span>
                  <LevelDot level={m.anomalyLevel} />
                  <span className="flex-1 truncate">{m.home.flag} {m.home.name} v {m.away.name} {m.away.flag}</span>
                  <span className="font-mono-num font-semibold">{m.anomalyIndex}</span>
                </Link>
              ))}
            </div>
            <p className="mt-4 text-[10px] text-muted-foreground border-t border-border pt-3">
              Note: 2026 predictions are out-of-time. Anomaly scores may be re-calibrated as post-tournament data arrives.
            </p>
          </aside>
        </div>
      </div>
    </PageTransition>
  );
}

function FilterSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-border bg-background/60 px-3 py-2 text-sm focus:border-primary focus:outline-none"
      >
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  );
}
