import { createFileRoute } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useMemo } from "react";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { cn } from "@/lib/utils";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
  BarChart,
  Bar,
  Cell,
} from "recharts";

const searchSchema = z.object({
  matchId: fallback(z.string(), "").default(""),
});

export const Route = createFileRoute("/explorer")({
  head: () => ({
    meta: [
      { title: "Match Explorer — The Break Point" },
      { name: "description", content: "Explore the 604 real historical match records used by the anomaly and betting-signal models." },
      { property: "og:title", content: "Match Explorer — The Break Point" },
      { property: "og:description", content: "604-match residual and odds-movement explorer." },
    ],
  }),
  validateSearch: zodValidator(searchSchema),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("betting")),
  component: Page,
});

const darkTooltip = { background: "#0f172a", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, fontSize: 12 };

function Page() {
  const { data } = useData("betting");
  const { matchId } = Route.useSearch();
  const navigate = Route.useNavigate();

  const records = useMemo(() => {
    return data.scatter.map((point, index) => {
      const [home = point.match, away = "Opponent"] = point.match.split(" vs ");

      return {
        ...point,
        id: `${index}-${point.match.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")}`,
        index,
        home,
        away,
        absResidual: Math.abs(point.residual),
        absOddsMove: Math.abs(point.oddsMove),
        composite: Math.abs(point.residual) * 100 + Math.abs(point.oddsMove),
      };
    });
  }, [data.scatter]);

  const ranked = useMemo(() => [...records].sort((a, b) => b.composite - a.composite), [records]);
  const record = records.find((m) => m.id === matchId) ?? ranked[0];

  if (!record) {
    return (
      <PageTransition>
        <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
          <div className="text-xs uppercase tracking-[0.3em] text-primary">Match Explorer</div>
          <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">No match records available</h1>
        </div>
      </PageTransition>
    );
  }

  const selectedRank = ranked.findIndex((m) => m.id === record.id) + 1;
  const normalRecords = records.filter((s) => s.anomalyLevel === "normal");
  const moderateRecords = records.filter((s) => s.anomalyLevel === "moderate");
  const highRecords = records.filter((s) => s.anomalyLevel === "high");
  const signalBars = [
    { signal: "Residual", value: record.residual, fill: record.residual >= 0 ? "#ef4444" : "#10b981" },
    { signal: "Odds move", value: record.oddsMove, fill: record.oddsMove >= 0 ? "#f59e0b" : "#3b82f6" },
  ];

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Match Explorer</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">604-match model output</h1>

        <div className="mt-4">
          <select
            value={record.id}
            onChange={(e) => navigate({ search: { matchId: e.target.value } })}
            className="w-full max-w-2xl rounded-lg border border-border bg-background/60 px-3 py-2 text-sm focus:border-primary focus:outline-none"
          >
            {records.map((m) => (
              <option key={m.id} value={m.id}>
                #{m.index + 1} · {m.match} · {m.anomalyLevel} · residual {m.residual.toFixed(4)}
              </option>
            ))}
          </select>
        </div>

        <GlassCard className="mt-6">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <div className="text-xs uppercase tracking-widest text-muted-foreground">Selected historical record</div>
              <div className="mt-2 flex flex-wrap items-center gap-3 font-display text-3xl font-bold">
                <span>{record.home}</span>
                <span className="font-mono-num text-muted-foreground">vs</span>
                <span>{record.away}</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
              <Meta label="Observation" value={`#${record.index + 1}`} />
              <Meta label="Signal rank" value={`#${selectedRank}`} />
              <Meta label="Residual" value={record.residual.toFixed(4)} />
              <Meta label="Odds move" value={`${(record.oddsMove * 100).toFixed(1)}%`} />
            </div>
          </div>
        </GlassCard>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="space-y-6">
            <GlassCard>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="font-display text-lg font-bold">Residual vs odds movement</h3>
                <div className="text-xs uppercase tracking-widest text-muted-foreground">N = {records.length}</div>
              </div>
              <div className="mt-4 h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis type="number" dataKey="residual" name="Residual" stroke="#94a3b8" fontSize={11} />
                    <YAxis type="number" dataKey="oddsMove" name="Odds move" stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`} />
                    <Tooltip contentStyle={darkTooltip} formatter={(v) => typeof v === "number" ? v.toFixed(4) : v} cursor={{ strokeDasharray: "3 3" }} />
                    <ReferenceArea x1={-0.01} x2={0.01} fill="#3b82f6" fillOpacity={0.05} />
                    <ReferenceLine y={0} stroke="#475569" />
                    <ReferenceLine x={0} stroke="#475569" />
                    <ReferenceLine x={record.residual} stroke="#eab308" strokeDasharray="4 4" />
                    <ReferenceLine y={record.oddsMove} stroke="#eab308" strokeDasharray="4 4" />
                    <Scatter data={normalRecords} fill="#10b981" name="Normal" opacity={0.35} />
                    <Scatter data={moderateRecords} fill="#f59e0b" name="Moderate" opacity={0.55} />
                    <Scatter data={highRecords} fill="#ef4444" name="High" opacity={0.7} />
                    <Scatter data={[record]} fill="#eab308" name="Selected" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="font-display text-lg font-bold">Selected match signals</h3>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={signalBars} layout="vertical">
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                    <YAxis type="category" dataKey="signal" stroke="#94a3b8" fontSize={11} width={90} />
                    <Tooltip contentStyle={darkTooltip} formatter={(v) => Number(v).toFixed(4)} />
                    <ReferenceLine x={0} stroke="#475569" />
                    <Bar dataKey="value">
                      {signalBars.map((signal) => (
                        <Cell key={signal.signal} fill={signal.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="font-display text-lg font-bold">Break-window exchange volume</h3>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.volumeByMinute}>
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                    <XAxis dataKey="minute" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip contentStyle={darkTooltip} />
                    <ReferenceArea x1={65} x2={80} fill="#3b82f6" fillOpacity={0.1} />
                    <Bar dataKey="bLeading" fill="#f59e0b" name="B-leading" opacity={0.8} />
                    <Bar dataKey="aLeading" fill="#3b82f6" name="A-leading" opacity={0.6} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          </div>

          <div className="space-y-6">
            <GlassCard>
              <div className="text-xs uppercase tracking-widest text-muted-foreground">Classification</div>
              <div
                className={cn(
                  "mt-3 inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold uppercase",
                  record.anomalyLevel === "high" && "border-red-500/40 bg-red-500/10 text-red-300",
                  record.anomalyLevel === "moderate" && "border-amber-500/40 bg-amber-500/10 text-amber-200",
                  record.anomalyLevel === "normal" && "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
                )}
              >
                {record.anomalyLevel}
              </div>
              <div className="mt-6 grid grid-cols-2 gap-3 text-xs">
                <Meta label="Abs residual" value={record.absResidual.toFixed(4)} />
                <Meta label="Abs odds move" value={`${(record.absOddsMove * 100).toFixed(1)}%`} />
                <Meta label="Correlation" value={data.correlation.toFixed(4)} />
                <Meta label="p-value" value={data.pValue.toFixed(4)} />
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="text-xs uppercase tracking-widest text-muted-foreground">Top ranked signals</h3>
              <div className="mt-4 space-y-1">
                {ranked.slice(0, 12).map((m, i) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => navigate({ search: { matchId: m.id } })}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg p-2 text-left text-xs transition-colors hover:bg-primary/10",
                      m.id === record.id && "bg-primary/10",
                    )}
                  >
                    <span className="w-5 font-mono-num text-muted-foreground">{i + 1}</span>
                    <span className="flex-1 truncate">{m.match}</span>
                    <span className="font-mono-num text-muted-foreground">{m.residual.toFixed(3)}</span>
                  </button>
                ))}
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="text-xs uppercase tracking-widest text-muted-foreground">Model findings</h3>
              <div className="mt-4 space-y-4">
                {data.findings.map((finding) => (
                  <div key={finding.title} className="border-b border-border pb-4 last:border-0 last:pb-0">
                    <div className="font-display font-mono-num text-xl font-bold text-primary">{finding.stat}</div>
                    <div className="mt-1 text-sm font-semibold">{finding.title}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{finding.detail}</div>
                  </div>
                ))}
              </div>
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
