import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo } from "react";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { LevelDot } from "@/components/dashboard/StatBadge";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea, ReferenceLine, BarChart, Bar, Legend,
} from "recharts";

export const Route = createFileRoute("/betting")({
  head: () => ({
    meta: [
      { title: "Betting Intelligence — The Break Point" },
      { name: "description", content: "Two-stage residual analysis of in-play odds movements during hydration break windows across 604 real matches." },
      { property: "og:title", content: "Betting Intelligence — The Break Point" },
      { property: "og:description", content: "Do markets anticipate match anomalies?" },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("betting")),
  component: Page,
});

const darkTooltip = { background: "#0f172a", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, fontSize: 12 };

function Page() {
  const { data } = useData("betting");

  const records = useMemo(
    () => data.scatter.map((s, i) => ({
      ...s,
      id: `${i}-${s.match.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")}`,
      composite: Math.abs(s.residual) * 100 + Math.abs(s.oddsMove),
    })),
    [data.scatter],
  );

  const scatterHigh = records.filter((s) => s.anomalyLevel === "high");
  const scatterMod = records.filter((s) => s.anomalyLevel === "moderate");
  const scatterNormal = records.filter((s) => s.anomalyLevel === "normal");
  const topMovers = useMemo(() => [...records].sort((a, b) => b.composite - a.composite).slice(0, 10), [records]);

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Betting Intelligence</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">Do markets anticipate anomalies?</h1>

        <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm">
          <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5" />
          <p className="text-amber-100">
            Betting analysis derived from the 604 historical matches in the model output — residuals and closing-line movements only. No forward-looking projections.
          </p>
        </div>

        <GlassCard className="mt-6">
          <div className="flex items-baseline justify-between flex-wrap gap-2">
            <h3 className="font-display text-lg font-bold">Odds movement vs match-model residual</h3>
            <div className="flex gap-6 text-sm">
              <span><span className="text-muted-foreground">r =</span> <span className="font-mono-num font-semibold text-primary">{data.correlation}</span></span>
              <span><span className="text-muted-foreground">p =</span> <span className="font-mono-num font-semibold">{data.pValue}</span></span>
              <span><span className="text-muted-foreground">N =</span> <span className="font-mono-num font-semibold">{records.length}</span></span>
            </div>
          </div>
          <div className="h-80 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                <XAxis type="number" dataKey="residual" name="Residual" stroke="#94a3b8" fontSize={11} label={{ value: "Match-model residual", position: "insideBottom", offset: -4, fill: "#64748b", fontSize: 11 }} />
                <YAxis type="number" dataKey="oddsMove" name="Odds move" stroke="#94a3b8" fontSize={11} label={{ value: "Odds movement (break window)", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11 }} />
                <Tooltip contentStyle={darkTooltip} cursor={{ strokeDasharray: "3 3" }} />
                <ReferenceLine y={0} stroke="#475569" />
                <ReferenceLine x={0} stroke="#475569" />
                <Scatter data={scatterNormal} fill="#10b981" name="Normal" />
                <Scatter data={scatterMod} fill="#f59e0b" name="Moderate" />
                <Scatter data={scatterHigh} fill="#ef4444" name="High" />
                <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="mt-6">
          <h3 className="font-display text-lg font-bold">Top 10 signal matches</h3>
          <p className="mt-1 text-xs text-muted-foreground">Ranked by |residual| × 100 + |odds move|. Click through for the full explorer view.</p>
          <div className="mt-4 divide-y divide-border">
            {topMovers.map((m, i) => (
              <Link
                key={m.id}
                to="/explorer"
                search={{ matchId: m.id }}
                className="flex items-center gap-4 py-2 text-sm hover:bg-primary/5 transition-colors rounded-md px-2"
              >
                <span className="font-mono-num text-xs text-muted-foreground w-6">{i + 1}</span>
                <LevelDot level={m.anomalyLevel} />
                <span className="flex-1 truncate">{m.match}</span>
                <span className={cn("font-mono-num text-xs w-24 text-right", m.residual >= 0 ? "text-red-300" : "text-emerald-300")}>
                  {m.residual >= 0 ? "+" : ""}{m.residual.toFixed(4)}
                </span>
                <span className={cn("font-mono-num text-xs w-20 text-right", m.oddsMove >= 0 ? "text-amber-300" : "text-blue-300")}>
                  {m.oddsMove >= 0 ? "+" : ""}{(m.oddsMove * 100).toFixed(1)}%
                </span>
                <span className="font-mono-num text-xs w-16 text-right font-semibold text-primary">{m.composite.toFixed(1)}</span>
              </Link>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="mt-6">
          <h3 className="font-display text-lg font-bold">Average volume by minute · leading-group split</h3>
          <div className="h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.volumeByMinute}>
                <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                <XAxis dataKey="minute" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={darkTooltip} />
                <ReferenceArea x1={65} x2={80} fill="#3b82f6" fillOpacity={0.1} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
                <Bar dataKey="bLeading" stackId="a" fill="#f59e0b" name="B-leading" opacity={0.8} />
                <Bar dataKey="aLeading" stackId="a" fill="#3b82f6" name="A-leading" opacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Volume systematically spikes in the 65-80 window for Group B-leading matches, roughly 3× the baseline.
          </p>
        </GlassCard>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {data.findings.map((f) => (
            <GlassCard key={f.title}>
              <div className="text-xs uppercase tracking-widest text-muted-foreground">{f.title}</div>
              <div className="mt-2 font-display text-2xl font-bold text-primary font-mono-num">{f.stat}</div>
              <p className="mt-2 text-sm text-muted-foreground">{f.detail}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </PageTransition>
  );
}
