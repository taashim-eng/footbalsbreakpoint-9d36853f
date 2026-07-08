import { createFileRoute } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useState } from "react";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { Clock, Thermometer, Zap, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Area, AreaChart, ReferenceLine, ReferenceArea, BarChart, Bar, Legend,
} from "recharts";

const searchSchema = z.object({
  era: fallback(z.string(), "C").default("C"),
});

export const Route = createFileRoute("/historical")({
  head: () => ({
    meta: [
      { title: "Historical Analysis — The Break Point" },
      { name: "description", content: "Era A, B, and C comparative analysis of goal timing, survival curves, and win probability during hydration breaks." },
      { property: "og:title", content: "Historical Analysis — The Break Point" },
      { property: "og:description", content: "A three-era natural experiment on hydration breaks." },
    ],
  }),
  validateSearch: zodValidator(searchSchema),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("historical")),
  component: Page,
});

const ICONS = { A: Clock, B: Thermometer, C: Zap };

function Page() {
  const { data } = useData("historical");
  const { era: eraId } = Route.useSearch();
  const navigate = Route.useNavigate();
  const era = data.eras.find((e) => e.id === eraId) ?? data.eras[2];

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Historical Analysis</div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold">Three eras. One question.</h1>
        <p className="mt-2 text-muted-foreground max-w-2xl">
          Compare goal distribution, survival hazard, and win-probability swings across three regulatory regimes.
        </p>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {data.eras.map((e) => {
            const Icon = ICONS[e.id];
            const active = e.id === era.id;
            return (
              <button
                key={e.id}
                onClick={() => navigate({ search: { era: e.id } })}
                className={cn(
                  "text-left glass rounded-2xl p-5 transition-all",
                  active
                    ? "border-primary shadow-[0_0_30px_-8px_var(--primary)]"
                    : "hover:border-primary/40"
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="rounded-lg bg-primary/15 p-2 text-primary"><Icon className="h-5 w-5" /></div>
                  <span className="font-mono-num text-xs text-muted-foreground">{e.years}</span>
                </div>
                <div className="mt-3 font-display text-xl font-bold">Era {e.id}</div>
                <div className="text-sm text-muted-foreground">{e.label}</div>
                <div className="mt-3 text-xs text-muted-foreground">N = <span className="font-mono-num text-foreground">{e.sampleSize}</span> matches</div>
              </button>
            );
          })}
        </div>

        {/* Heatmap */}
        <SectionCard title="Goal Distribution by Minute Window" caption={era.caption}>
          <div className="overflow-x-auto">
            <table className="w-full border-separate border-spacing-1 min-w-[600px]">
              <thead>
                <tr>
                  <th className="text-left text-xs font-normal text-muted-foreground p-2">GDP Group</th>
                  {era.heatmap.map((b) => (
                    <th key={b.bin} className={cn(
                      "text-xs font-mono-num text-muted-foreground p-2 text-center",
                      b.highlight && "border border-dashed border-primary/60 rounded"
                    )}>{b.bin}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(["groupA","groupB"] as const).map((g) => (
                  <tr key={g}>
                    <td className="text-xs p-2 font-semibold">{g === "groupA" ? "Group A" : "Group B"}</td>
                    {era.heatmap.map((b) => {
                      const v = b[g];
                      const intensity = Math.min(1, v / 0.35);
                      return (
                        <td key={b.bin} className={cn(
                          "text-center p-3 rounded font-mono-num text-xs",
                          b.highlight && "ring-1 ring-primary/60"
                        )} style={{
                          background: `rgba(59,130,246,${intensity * 0.7})`,
                          color: intensity > 0.5 ? "white" : "var(--muted-foreground)",
                        }}>
                          {v.toFixed(2)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-xs text-muted-foreground">Dashed column marks the 65-80 hydration break window. Values are goals conceded per match.</p>
        </SectionCard>

        {/* DiD */}
        {era.did && (
          <SectionCard title="Difference-in-Differences · Three-way interaction" caption="The coefficient represents the additional goal burden on Group B teams after the mandatory break.">
            <ForestPlot did={era.did} />
          </SectionCard>
        )}

        {/* Survival */}
        <SectionCard title="Kaplan-Meier Survival · Time to First Concession After Break" caption={`Log-rank p = ${era.logRankP.toFixed(3)}`}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={era.survival} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="ga" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gb" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                <XAxis dataKey="minute" stroke="#94a3b8" fontSize={11} label={{ value: "Minutes after break", position: "insideBottom", offset: -4, fill: "#64748b", fontSize: 11 }} />
                <YAxis stroke="#94a3b8" fontSize={11} domain={[0.7, 1]} tickFormatter={(v) => v.toFixed(2)} />
                <Tooltip contentStyle={darkTooltip} />
                <ReferenceLine x={15} stroke="#94a3b8" strokeDasharray="3 3" label={{ value: "Window", fill: "#94a3b8", fontSize: 10 }} />
                <Area type="monotone" dataKey="groupA" stroke="#3b82f6" fill="url(#ga)" name="Group A" strokeWidth={2} />
                <Area type="monotone" dataKey="groupB" stroke="#f59e0b" fill="url(#gb)" name="Group B" strokeWidth={2} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        {/* Win prob */}
        <SectionCard title="Win Probability Swing · Δ WP (65 → 80)" caption={`Mann-Whitney U · p = ${era.mannWhitneyP.toFixed(3)}`}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={era.winProb}>
                <CartesianGrid stroke="rgba(148,163,184,0.1)" />
                <XAxis dataKey="bucket" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={darkTooltip} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
                <Bar dataKey="groupA" fill="#3b82f6" name="Group A-leading" opacity={0.7} />
                <Bar dataKey="groupB" fill="#f59e0b" name="Group B-leading" opacity={0.7} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        {/* Power */}
        <PowerAnalysis n={era.power.n} d={era.power.detectableEffect} />
      </div>
    </PageTransition>
  );
}

const darkTooltip = { background: "#0f172a", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, fontSize: 12 };

function SectionCard({ title, caption, children }: { title: string; caption?: string; children: React.ReactNode }) {
  return (
    <GlassCard className="mt-6">
      <div className="mb-4">
        <h3 className="font-display text-lg font-bold">{title}</h3>
        {caption && <p className="text-xs text-muted-foreground mt-1">{caption}</p>}
      </div>
      {children}
    </GlassCard>
  );
}

function ForestPlot({ did }: { did: { estimate: number; lower: number; upper: number; ropeLow: number; ropeHigh: number } }) {
  const min = -0.1, max = 0.35;
  const pct = (v: number) => ((v - min) / (max - min)) * 100;
  return (
    <div className="pt-4">
      <div className="relative h-24">
        <div className="absolute inset-0 flex items-center">
          <div className="relative w-full h-px bg-border" />
        </div>
        {/* ROPE */}
        <div
          className="absolute top-1/2 -translate-y-1/2 h-16 bg-muted/40 border border-border rounded"
          style={{ left: `${pct(did.ropeLow)}%`, width: `${pct(did.ropeHigh) - pct(did.ropeLow)}%` }}
        >
          <div className="text-[9px] text-muted-foreground p-1 uppercase tracking-widest">ROPE</div>
        </div>
        {/* Zero line */}
        <div className="absolute inset-y-0 border-l border-dashed border-muted-foreground" style={{ left: `${pct(0)}%` }} />
        {/* CI */}
        <div
          className="absolute top-1/2 -translate-y-1/2 h-1 bg-primary rounded"
          style={{ left: `${pct(did.lower)}%`, width: `${pct(did.upper) - pct(did.lower)}%` }}
        />
        {/* Point */}
        <div
          className="absolute top-1/2 -translate-y-1/2 h-4 w-4 rounded-full bg-primary border-2 border-background shadow-[0_0_12px_var(--primary)] -translate-x-2"
          style={{ left: `${pct(did.estimate)}%` }}
        />
      </div>
      <div className="mt-4 flex justify-between text-xs font-mono-num text-muted-foreground">
        <span>-0.10</span><span>0</span><span>+0.35</span>
      </div>
      <div className="mt-4 flex gap-6 text-sm">
        <div><span className="text-muted-foreground text-xs">Estimate:</span> <span className="font-mono-num text-primary font-semibold">+{did.estimate.toFixed(3)}</span></div>
        <div><span className="text-muted-foreground text-xs">95% HDI:</span> <span className="font-mono-num">[{did.lower.toFixed(3)}, {did.upper.toFixed(3)}]</span></div>
      </div>
    </div>
  );
}

function PowerAnalysis({ n, d }: { n: number; d: number }) {
  const [open, setOpen] = useState(false);
  return (
    <GlassCard className="mt-6">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center justify-between">
        <div className="text-left">
          <div className="text-xs uppercase tracking-widest text-muted-foreground">Power Analysis</div>
          <div className="mt-1 font-display font-semibold">
            With N=<span className="font-mono-num text-primary">{n}</span> matches, detect effects d ≥ <span className="font-mono-num text-primary">{d}</span> at 80% power
          </div>
        </div>
        <ChevronDown className={cn("h-5 w-5 text-muted-foreground transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="mt-4 pt-4 border-t border-border text-sm text-muted-foreground space-y-2">
          <p>Power analysis assumes α = 0.05, two-sided test, and equal group sizes. Smaller effects require substantially more matches.</p>
          <p>Era C's sample size (N={n}) is the primary constraint on our ability to detect subtle interaction effects. Post-tournament data will roughly double statistical power.</p>
        </div>
      )}
    </GlassCard>
  );
}
