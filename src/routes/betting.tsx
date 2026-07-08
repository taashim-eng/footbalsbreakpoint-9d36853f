import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { AlertTriangle } from "lucide-react";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea, ReferenceLine, LineChart, Line, BarChart, Bar, Legend,
} from "recharts";

export const Route = createFileRoute("/betting")({
  head: () => ({
    meta: [
      { title: "Betting Intelligence — The Break Point" },
      { name: "description", content: "Two-stage residual analysis of in-play odds movements during hydration break windows." },
      { property: "og:title", content: "Betting Intelligence — The Break Point" },
      { property: "og:description", content: "Do markets anticipate match anomalies?" },
    ],
  }),
  loader: async ({ context }) => {
    await Promise.all([
      context.queryClient.ensureQueryData(dataQueryOptions("betting")),
      context.queryClient.ensureQueryData(dataQueryOptions("matches2026")),
    ]);
  },
  component: Page,
});

const darkTooltip = { background: "#0f172a", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, fontSize: 12 };

function Page() {
  const { data } = useData("betting");
  const { data: matches } = useData("matches2026");
  const matchesWithOdds = matches.filter((m) => m.odds);
  const [selectedId, setSelectedId] = useState(matchesWithOdds[0]?.id ?? "");
  const selected = matchesWithOdds.find((m) => m.id === selectedId);

  const scatterHigh = data.scatter.filter((s) => s.anomalyLevel === "high");
  const scatterMod = data.scatter.filter((s) => s.anomalyLevel === "moderate");
  const scatterNormal = data.scatter.filter((s) => s.anomalyLevel === "normal");

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Betting Intelligence</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">Do markets anticipate anomalies?</h1>

        <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm">
          <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5" />
          <p className="text-amber-100">
            Betting analysis based on publicly available data. In-play data available for 2018, 2022, and 2026 tournaments only.
          </p>
        </div>

        {/* Scatter */}
        <GlassCard className="mt-6">
          <div className="flex items-baseline justify-between flex-wrap gap-2">
            <h3 className="font-display text-lg font-bold">Odds movement vs match-model residual</h3>
            <div className="flex gap-6 text-sm">
              <span><span className="text-muted-foreground">r =</span> <span className="font-mono-num font-semibold text-primary">{data.correlation}</span></span>
              <span><span className="text-muted-foreground">p =</span> <span className="font-mono-num font-semibold">{data.pValue}</span></span>
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

        {/* Odds trajectory */}
        <GlassCard className="mt-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <h3 className="font-display text-lg font-bold">In-play odds trajectory</h3>
            <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}
              className="rounded-lg border border-border bg-background/60 px-3 py-2 text-sm focus:border-primary focus:outline-none">
              {matchesWithOdds.map((m) => (
                <option key={m.id} value={m.id}>{m.date} · {m.home.name} v {m.away.name}</option>
              ))}
            </select>
          </div>
          {selected?.odds && (
            <>
              <div className="h-64 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={selected.odds}>
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis dataKey="minute" stroke="#94a3b8" fontSize={11} label={{ value: "Match minute", position: "insideBottom", offset: -4, fill: "#64748b", fontSize: 11 }} />
                    <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 1]} tickFormatter={(v) => `${(v*100).toFixed(0)}%`} />
                    <Tooltip contentStyle={darkTooltip} formatter={(v) => `${(Number(v)*100).toFixed(1)}%`} />
                    <ReferenceArea x1={65} x2={80} fill="#3b82f6" fillOpacity={0.1} label={{ value: "Break window", fill: "#94a3b8", fontSize: 10 }} />
                    <Line type="monotone" dataKey="groupBProb" stroke="#f59e0b" strokeWidth={2} dot={false} name="Group B implied win prob" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="h-32 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={selected.odds}>
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis dataKey="minute" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip contentStyle={darkTooltip} />
                    <ReferenceArea x1={65} x2={80} fill="#3b82f6" fillOpacity={0.1} />
                    <Bar dataKey="volume" fill="#3b82f6" opacity={0.6} name="Volume" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </GlassCard>

        {/* Volume */}
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

        {/* Findings */}
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
