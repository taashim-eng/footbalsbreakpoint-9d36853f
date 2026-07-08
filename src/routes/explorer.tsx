import { createFileRoute } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useState } from "react";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { AnomalyGauge } from "@/components/dashboard/AnomalyGauge";
import { cn } from "@/lib/utils";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea, RadarChart, PolarGrid, PolarAngleAxis, Radar, PolarRadiusAxis, BarChart, Bar, Cell,
} from "recharts";

const searchSchema = z.object({
  matchId: fallback(z.string(), "").default(""),
});

export const Route = createFileRoute("/explorer")({
  head: () => ({
    meta: [
      { title: "Match Explorer — The Break Point" },
      { name: "description", content: "Deep dive into individual match anomalies with timeline, radar comparison, and SHAP feature attribution." },
      { property: "og:title", content: "Match Explorer — The Break Point" },
      { property: "og:description", content: "Per-match anomaly deep dive." },
    ],
  }),
  validateSearch: zodValidator(searchSchema),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("matches2026")),
  component: Page,
});

const darkTooltip = { background: "#0f172a", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, fontSize: 12 };

function Page() {
  const { data } = useData("matches2026");
  const { matchId } = Route.useSearch();
  const navigate = Route.useNavigate();
  const [oddsOpen, setOddsOpen] = useState(true);

  const defaultMatch = [...data].sort((a,b) => b.anomalyIndex - a.anomalyIndex)[0];
  const match = data.find((m) => m.id === matchId) ?? defaultMatch;

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Match Explorer</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">Deep dive</h1>

        <div className="mt-4">
          <select
            value={match.id}
            onChange={(e) => navigate({ search: { matchId: e.target.value } })}
            className="w-full max-w-md rounded-lg border border-border bg-background/60 px-3 py-2 text-sm focus:border-primary focus:outline-none"
          >
            {data.map((m) => (
              <option key={m.id} value={m.id}>
                {m.date} · {m.home.name} {m.home.score}-{m.away.score} {m.away.name} (idx {m.anomalyIndex})
              </option>
            ))}
          </select>
        </div>

        {/* Header banner */}
        <GlassCard className="mt-6">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="flex items-center gap-4 text-center">
              <div>
                <div className="text-4xl">{match.home.flag}</div>
                <div className="mt-1 font-semibold">{match.home.name}</div>
                <div className="text-[10px] text-muted-foreground">Group {match.home.gdp}</div>
              </div>
              <div className="font-display font-extrabold text-5xl font-mono-num">
                {match.home.score} <span className="text-muted-foreground">-</span> {match.away.score}
              </div>
              <div>
                <div className="text-4xl">{match.away.flag}</div>
                <div className="mt-1 font-semibold">{match.away.name}</div>
                <div className="text-[10px] text-muted-foreground">Group {match.away.gdp}</div>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <Meta label="Date" value={match.date} />
              <Meta label="Stage" value={match.stage} />
              <Meta label="Venue" value={match.venue} />
              <Meta label="Temp" value={`${match.temperatureC}°C`} />
            </div>
          </div>
        </GlassCard>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_400px]">
          <div className="space-y-6">
            {/* Timeline */}
            <GlassCard>
              <h3 className="font-display text-lg font-bold">Match Timeline</h3>
              <div className="relative mt-6 h-16">
                <div className="absolute inset-y-1/2 -translate-y-1/2 h-px w-full bg-border" />
                <div className="absolute inset-y-0 bg-primary/10 border-x border-dashed border-primary/40" style={{ left: `${65/95*100}%`, width: `${15/95*100}%` }}>
                  <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] uppercase tracking-widest text-primary">Break</div>
                </div>
                {match.events.map((e, i) => {
                  const emoji = e.type === "goal" ? "⚽" : e.type === "card" ? "🟨" : "🔄";
                  const above = e.team === "home";
                  return (
                    <div key={i} className="absolute text-sm" style={{ left: `${Math.min(97, e.minute/95*100)}%`, top: above ? "0%" : "60%" }}>
                      <span title={`${e.minute}' ${e.label}`}>{emoji}</span>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 flex justify-between text-[10px] font-mono-num text-muted-foreground">
                <span>0'</span><span>15'</span><span>30'</span><span>45'</span><span>60'</span><span>75'</span><span>90'</span>
              </div>
            </GlassCard>

            {/* Score trajectory */}
            <GlassCard>
              <h3 className="font-display text-lg font-bold">Score trajectory · Group B perspective</h3>
              <div className="h-56 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={match.scoreTrajectory}>
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis dataKey="minute" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip contentStyle={darkTooltip} />
                    <ReferenceArea x1={65} x2={80} fill="#3b82f6" fillOpacity={0.1} />
                    <Line type="stepAfter" dataKey="diff" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>

            {/* Radar */}
            <GlassCard>
              <h3 className="font-display text-lg font-bold">Pre vs Post Break</h3>
              <div className="h-72 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={match.radar}>
                    <PolarGrid stroke="rgba(148,163,184,0.2)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <PolarRadiusAxis stroke="#475569" fontSize={10} />
                    <Radar name="Pre-break" dataKey="pre" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
                    <Radar name="Post-break" dataKey="post" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.25} />
                    <Tooltip contentStyle={darkTooltip} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          </div>

          <div className="space-y-6">
            <GlassCard className="text-center">
              <div className="text-xs uppercase tracking-widest text-muted-foreground">Anomaly Index</div>
              <div className="mt-2 flex justify-center">
                <AnomalyGauge score={match.anomalyIndex} size={180} />
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="text-xs uppercase tracking-widest text-muted-foreground">Component Breakdown</h3>
              <div className="mt-4 space-y-3">
                {match.componentBreakdown.map((c) => (
                  <div key={c.label}>
                    <div className="flex items-baseline justify-between text-xs">
                      <span>{c.label}</span>
                      <span className="font-mono-num text-muted-foreground">w={c.weight}</span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-muted overflow-hidden">
                      {c.score === null ? (
                        <div className="h-full bg-muted-foreground/20 grid place-items-center text-[10px] text-muted-foreground">No data</div>
                      ) : (
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${c.score}%`,
                            background: c.score > 70 ? "#ef4444" : c.score > 45 ? "#f59e0b" : "#10b981",
                          }}
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="text-xs uppercase tracking-widest text-muted-foreground">Match Context</h3>
              <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                <Meta label="Home FIFA rank" value={`#${match.fifaRankHome}`} />
                <Meta label="Away FIFA rank" value={`#${match.fifaRankAway}`} />
                <Meta label="Squad value (H)" value={`€${match.squadValueHomeM}M`} />
                <Meta label="Squad value (A)" value={`€${match.squadValueAwayM}M`} />
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="text-xs uppercase tracking-widest text-muted-foreground">SHAP Feature Attribution</h3>
              <div className="h-56 mt-3">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={match.shap} layout="vertical">
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis type="number" stroke="#94a3b8" fontSize={10} />
                    <YAxis type="category" dataKey="feature" stroke="#94a3b8" fontSize={10} width={110} />
                    <Tooltip contentStyle={darkTooltip} />
                    <Bar dataKey="value">
                      {match.shap.map((s, i) => (
                        <Cell key={i} fill={s.value >= 0 ? "#ef4444" : "#10b981"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          </div>
        </div>

        {/* Odds panel */}
        <GlassCard className="mt-6">
          <button className="flex w-full items-center justify-between" onClick={() => setOddsOpen(!oddsOpen)}>
            <h3 className="font-display text-lg font-bold">Odds Trajectory</h3>
            <span className="text-xs text-muted-foreground">{oddsOpen ? "Collapse" : "Expand"}</span>
          </button>
          {oddsOpen && (
            match.odds ? (
              <div className="h-64 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={match.odds}>
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis dataKey="minute" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 1]} tickFormatter={(v) => `${(v*100).toFixed(0)}%`} />
                    <Tooltip contentStyle={darkTooltip} formatter={(v) => `${(Number(v)*100).toFixed(1)}%`} />
                    <ReferenceArea x1={65} x2={80} fill="#3b82f6" fillOpacity={0.1} />
                    <Line type="monotone" dataKey="groupBProb" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="mt-6 rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                No in-play data available for this match.
              </div>
            )
          )}
        </GlassCard>
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
