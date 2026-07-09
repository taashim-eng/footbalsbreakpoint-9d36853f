import { createFileRoute, Link } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { LevelDot } from "@/components/dashboard/StatBadge";
import { cn } from "@/lib/utils";
import { useMemo } from "react";

const searchSchema = z.object({
  level: fallback(z.string(), "all").default("all"),
  sort: fallback(z.string(), "residual").default("residual"),
  q: fallback(z.string(), "").default(""),
});

export const Route = createFileRoute("/monitor")({
  head: () => ({
    meta: [
      { title: "Anomaly Monitor — The Break Point" },
      { name: "description", content: "Match-by-match anomaly monitoring across 604 real historical FIFA World Cup matches." },
      { property: "og:title", content: "Anomaly Monitor — The Break Point" },
      { property: "og:description", content: "604 real matches scored, filtered, and ranked by residual and odds-move signal." },
    ],
  }),
  validateSearch: zodValidator(searchSchema),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("betting")),
  component: Page,
});

function Page() {
  const { data } = useData("betting");
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  const records = useMemo(() => {
    return data.scatter.map((s, i) => {
      const [home = s.match, away = "Opponent"] = s.match.split(" vs ");
      return {
        ...s,
        index: i,
        id: `${i}-${s.match.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")}`,
        home,
        away,
        absResidual: Math.abs(s.residual),
        absOddsMove: Math.abs(s.oddsMove),
        composite: Math.abs(s.residual) * 100 + Math.abs(s.oddsMove),
      };
    });
  }, [data.scatter]);

  const filtered = useMemo(() => {
    let out = records;
    if (search.level !== "all") out = out.filter((m) => m.anomalyLevel === search.level);
    if (search.q.trim()) {
      const q = search.q.toLowerCase();
      out = out.filter((m) => m.match.toLowerCase().includes(q));
    }
    const sorted = [...out];
    if (search.sort === "odds") sorted.sort((a, b) => b.absOddsMove - a.absOddsMove);
    else if (search.sort === "composite") sorted.sort((a, b) => b.composite - a.composite);
    else sorted.sort((a, b) => b.absResidual - a.absResidual);
    return sorted;
  }, [records, search]);

  const counts = useMemo(() => ({
    total: records.length,
    high: records.filter((r) => r.anomalyLevel === "high").length,
    moderate: records.filter((r) => r.anomalyLevel === "moderate").length,
    normal: records.filter((r) => r.anomalyLevel === "normal").length,
  }), [records]);

  const leaderboard = useMemo(
    () => [...records].sort((a, b) => b.composite - a.composite).slice(0, 12),
    [records],
  );

  const updateSearch = (patch: Partial<typeof search>) =>
    navigate({ search: { ...search, ...patch } });

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Anomaly Monitor</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">604 real matches, ranked by signal</h1>
        <p className="mt-2 text-muted-foreground">
          Every historical match scored on residual and odds-move magnitude, filtered and sorted live from the model output.
        </p>

        <div className="mt-6 grid gap-3 sm:grid-cols-4">
          <Stat label="Total matches" value={counts.total.toString()} tone="primary" />
          <Stat label="High anomaly" value={counts.high.toString()} tone="red" />
          <Stat label="Moderate" value={counts.moderate.toString()} tone="amber" />
          <Stat label="Normal" value={counts.normal.toString()} tone="emerald" />
        </div>

        <div className="mt-6 glass rounded-xl p-4 grid gap-3 sm:grid-cols-3">
          <label className="flex flex-col gap-1">
            <span className="text-[10px] uppercase tracking-widest text-muted-foreground">Search</span>
            <input
              value={search.q}
              onChange={(e) => updateSearch({ q: e.target.value })}
              placeholder="Team or match…"
              className="rounded-lg border border-border bg-background/60 px-3 py-2 text-sm focus:border-primary focus:outline-none"
            />
          </label>
          <FilterSelect
            label="Anomaly level"
            value={search.level}
            onChange={(v) => updateSearch({ level: v })}
            options={[["all", "All levels"], ["high", "High"], ["moderate", "Moderate"], ["normal", "Normal"]]}
          />
          <FilterSelect
            label="Sort"
            value={search.sort}
            onChange={(v) => updateSearch({ sort: v })}
            options={[["residual", "|Residual|"], ["odds", "|Odds move|"], ["composite", "Composite signal"]]}
          />
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_320px]">
          <div className="grid gap-3 content-start">
            <div className="text-xs text-muted-foreground">
              Showing {filtered.length} of {records.length} matches
            </div>
            {filtered.slice(0, 60).map((m, i) => (
              <Link
                key={m.id}
                to="/explorer"
                search={{ matchId: m.id }}
                className={cn(
                  "glass rounded-xl px-4 py-3 flex items-center gap-4 transition-all hover:border-primary/50",
                  m.anomalyLevel === "high" && "hover:shadow-[0_0_30px_-8px_#ef4444]",
                )}
              >
                <span className="font-mono-num text-xs text-muted-foreground w-10">#{m.index + 1}</span>
                <LevelDot level={m.anomalyLevel} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold truncate">{m.home} <span className="text-muted-foreground">vs</span> {m.away}</div>
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground mt-0.5">{m.anomalyLevel}</div>
                </div>
                <div className="hidden sm:block text-right">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Residual</div>
                  <div className={cn("font-mono-num text-sm", m.residual >= 0 ? "text-red-300" : "text-emerald-300")}>
                    {m.residual >= 0 ? "+" : ""}{m.residual.toFixed(4)}
                  </div>
                </div>
                <div className="hidden md:block text-right">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Odds move</div>
                  <div className={cn("font-mono-num text-sm", m.oddsMove >= 0 ? "text-amber-300" : "text-blue-300")}>
                    {m.oddsMove >= 0 ? "+" : ""}{(m.oddsMove * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Signal</div>
                  <div className="font-mono-num text-sm font-semibold text-primary">{m.composite.toFixed(2)}</div>
                </div>
                <span className="hidden lg:inline text-[10px] uppercase tracking-widest text-muted-foreground w-8 text-right">
                  {i === 0 ? "top" : ""}
                </span>
              </Link>
            ))}
            {filtered.length > 60 && (
              <div className="text-center text-xs text-muted-foreground py-3">
                Showing first 60 of {filtered.length} — narrow filters to see more.
              </div>
            )}
            {filtered.length === 0 && (
              <div className="text-center text-muted-foreground py-16 text-sm">No matches for these filters.</div>
            )}
          </div>

          <aside className="glass rounded-2xl p-5 h-fit lg:sticky lg:top-24">
            <div className="text-xs uppercase tracking-widest text-muted-foreground">Composite Leaderboard</div>
            <h3 className="mt-1 font-display text-lg font-bold">Top 12 by signal</h3>
            <div className="mt-4 space-y-1">
              {leaderboard.map((m, i) => (
                <Link
                  key={m.id}
                  to="/explorer"
                  search={{ matchId: m.id }}
                  className={cn(
                    "flex items-center gap-3 rounded-lg p-2 text-xs hover:bg-primary/10 transition-colors",
                    m.anomalyLevel === "high" && "bg-red-500/5",
                  )}
                >
                  <span className="font-mono-num text-muted-foreground w-4">{i + 1}</span>
                  <LevelDot level={m.anomalyLevel} />
                  <span className="flex-1 truncate">{m.match}</span>
                  <span className="font-mono-num font-semibold">{m.composite.toFixed(1)}</span>
                </Link>
              ))}
            </div>
            <p className="mt-4 text-[10px] text-muted-foreground border-t border-border pt-3">
              Composite = |residual| × 100 + |odds move|. Derived from the same 604-match model output that powers the scatter and explorer.
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

function Stat({ label, value, tone }: { label: string; value: string; tone: "primary" | "red" | "amber" | "emerald" }) {
  const toneClass = {
    primary: "text-primary",
    red: "text-red-300",
    amber: "text-amber-300",
    emerald: "text-emerald-300",
  }[tone];
  return (
    <div className="glass rounded-xl p-4">
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className={cn("mt-1 font-display font-mono-num text-2xl font-bold", toneClass)}>{value}</div>
    </div>
  );
}
