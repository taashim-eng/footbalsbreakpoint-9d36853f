import { createFileRoute, Link } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { cn } from "@/lib/utils";
import { useMemo } from "react";

const searchSchema = z.object({
  stage: fallback(z.string(), "all").default("all"),
  sort: fallback(z.string(), "date").default("date"),
  q: fallback(z.string(), "").default(""),
});

export const Route = createFileRoute("/monitor")({
  head: () => ({
    meta: [
      { title: "2026 Monitor — The Break Point" },
      { name: "description", content: "Live results tracker for the 2026 FIFA World Cup — every completed match, sourced from observed final scores." },
      { property: "og:title", content: "2026 Monitor — The Break Point" },
      { property: "og:description", content: "Real 2026 FIFA World Cup results as they are played." },
    ],
  }),
  validateSearch: zodValidator(searchSchema),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("matches2026")),
  component: Page,
});

function stageKind(stage: string): "group" | "knockout" {
  return stage.startsWith("Group") ? "group" : "knockout";
}

function Page() {
  const { data } = useData("matches2026");
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  const matches = data.matches;

  const stages = useMemo(() => {
    const order = ["Group A", "Group B", "Group C", "Group D", "Group E", "Group F", "Group G", "Group H", "Group I", "Group J", "Group K", "Group L", "Round of 32", "Round of 16", "Quarter-finals", "Semi-finals", "Third-place match", "Final"];
    const present = Array.from(new Set(matches.map((m) => m.stage)));
    return present.sort((a, b) => order.indexOf(a) - order.indexOf(b));
  }, [matches]);

  const filtered = useMemo(() => {
    let out = matches;
    if (search.stage !== "all") out = out.filter((m) => m.stage === search.stage);
    if (search.q.trim()) {
      const q = search.q.toLowerCase();
      out = out.filter((m) =>
        `${m.homeTeam} ${m.awayTeam} ${m.venue} ${m.city} ${m.stage}`.toLowerCase().includes(q),
      );
    }
    const sorted = [...out];
    if (search.sort === "goals") {
      sorted.sort((a, b) => (b.finalScore.home + b.finalScore.away) - (a.finalScore.home + a.finalScore.away));
    } else {
      sorted.sort((a, b) => b.date.localeCompare(a.date));
    }
    return sorted;
  }, [matches, search]);

  const counts = useMemo(() => ({
    total: matches.length,
    group: matches.filter((m) => stageKind(m.stage) === "group").length,
    knockout: matches.filter((m) => stageKind(m.stage) === "knockout").length,
    latest: matches.reduce((acc, m) => (m.date > acc ? m.date : acc), ""),
  }), [matches]);

  const updateSearch = (patch: Partial<typeof search>) =>
    navigate({ search: { ...search, ...patch } });

  if (matches.length === 0) {
    return (
      <PageTransition>
        <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
          <div className="text-xs uppercase tracking-[0.3em] text-primary">2026 Monitor</div>
          <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">No 2026 fixtures completed yet</h1>
          <p className="mt-3 text-muted-foreground max-w-2xl">{data.note}</p>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">2026 Monitor</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">{counts.total} matches played — 2026 FIFA World Cup</h1>
        <p className="mt-2 text-muted-foreground">
          Observed final results only, through the Round of 16. Group stage and knockout matches sourced from live fixtures — no projected or simulated fixtures.
        </p>

        <div className="mt-6 grid gap-3 sm:grid-cols-4">
          <Stat label="Matches played" value={counts.total.toString()} tone="primary" />
          <Stat label="Group stage" value={counts.group.toString()} tone="emerald" />
          <Stat label="Knockout" value={counts.knockout.toString()} tone="amber" />
          <Stat label="Latest match" value={counts.latest} tone="primary" />
        </div>

        <div className="mt-6 glass rounded-xl p-4 grid gap-3 sm:grid-cols-3">
          <label className="flex flex-col gap-1">
            <span className="text-[10px] uppercase tracking-widest text-muted-foreground">Search</span>
            <input
              value={search.q}
              onChange={(e) => updateSearch({ q: e.target.value })}
              placeholder="Team, venue, city…"
              className="rounded-lg border border-border bg-background/60 px-3 py-2 text-sm focus:border-primary focus:outline-none"
            />
          </label>
          <FilterSelect
            label="Stage"
            value={search.stage}
            onChange={(v) => updateSearch({ stage: v })}
            options={[["all", "All stages"], ...stages.map((s) => [s, s] as [string, string])]}
          />
          <FilterSelect
            label="Sort"
            value={search.sort}
            onChange={(v) => updateSearch({ sort: v })}
            options={[["date", "Most recent"], ["goals", "Most goals"]]}
          />
        </div>

        <div className="mt-8 grid gap-3 content-start">
          <div className="text-xs text-muted-foreground">
            Showing {filtered.length} of {matches.length} matches
          </div>
          {filtered.map((m) => {
            const decided = m.penalties
              ? `${m.homeTeam} ${m.penalties.home}-${m.penalties.away} ${m.awayTeam} on penalties`
              : null;
            return (
              <Link
                key={m.matchId}
                to="/explorer"
                search={{ matchId: m.matchId }}
                className="glass rounded-xl px-4 py-3 flex items-center gap-4 transition-all hover:border-primary/50"
              >
                <div className="w-24 shrink-0">
                  <div className="font-mono-num text-xs text-muted-foreground">{m.date}</div>
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground mt-0.5">{m.stage}</div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 text-sm font-semibold">
                    <span className="truncate">{m.homeFlag} {m.homeTeam}</span>
                    <span className="font-mono-num text-base font-bold text-primary shrink-0">
                      {m.finalScore.home}–{m.finalScore.away}
                    </span>
                    <span className="truncate">{m.awayTeam} {m.awayFlag}</span>
                  </div>
                  {decided && (
                    <div className="text-[10px] uppercase tracking-widest text-amber-300/80 mt-0.5">{decided}</div>
                  )}
                </div>
                <div className="hidden md:block text-right w-40 shrink-0">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Venue</div>
                  <div className="text-xs truncate">{m.venue}</div>
                </div>
              </Link>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-center text-muted-foreground py-16 text-sm">No matches for these filters.</div>
          )}
        </div>

        <p className="mt-8 text-[11px] text-muted-foreground border-t border-border pt-4">
          Source: {data.source}. Last updated {data.lastUpdated}.
        </p>
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

function Stat({ label, value, tone }: { label: string; value: string; tone: "primary" | "amber" | "emerald" }) {
  const toneClass = {
    primary: "text-primary",
    amber: "text-amber-400",
    emerald: "text-emerald-400",
  }[tone];
  return (
    <div className="glass rounded-xl p-4">
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className={cn("mt-1 font-display text-2xl font-bold font-mono-num", toneClass)}>{value}</div>
    </div>
  );
}
