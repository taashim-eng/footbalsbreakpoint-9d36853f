import { createFileRoute, Link } from "@tanstack/react-router";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { AnimatedCounter } from "@/components/dashboard/AnimatedCounter";
import { StatBadge } from "@/components/dashboard/StatBadge";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { ArrowRight, Clock, Thermometer, Zap } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Overview — The Break Point" },
      { name: "description", content: "Statistical anomaly detection across 2,800+ FIFA World Cup matches. Key findings at a glance." },
      { property: "og:title", content: "Overview — The Break Point" },
      { property: "og:description", content: "Statistical anomaly detection across 2,800+ FIFA World Cup matches. Key findings at a glance." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("overview")),
  component: Index,
});

const ERA_ICONS = { A: Clock, B: Thermometer, C: Zap };

function Index() {
  const { data } = useData("overview");

  return (
    <PageTransition>
      {/* Hero */}
      <section className="relative overflow-hidden hero-gradient border-b border-border/60">
        <div className="absolute inset-0 grid-dots opacity-40" />
        <Particles />
        <div className="relative mx-auto max-w-7xl px-4 py-20 md:px-6 md:py-28 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-mono-num text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            MODEL OUTPUT · 2026 FIFA WORLD CUP
          </div>
          <h1 className="mt-6 font-display text-5xl md:text-7xl font-extrabold tracking-tight">
            THE BREAK <span className="text-gradient">POINT</span>
          </h1>
          <p className="mt-4 text-lg md:text-xl text-slate-300 max-w-2xl mx-auto">
            Investigating statistical anomalies during FIFA World Cup hydration breaks.
          </p>
          <p className="mt-2 text-sm text-slate-400 font-mono-num">
            Following the data. Following the money.
          </p>
          <p className="mt-6 text-xs text-slate-500 max-w-xl mx-auto">
            Analyzing 604 historical match records with pre-computed statistical and betting-market signals.
          </p>

          <div className="mt-12 grid gap-4 md:grid-cols-3 max-w-4xl mx-auto">
            <CounterCard label="Matches Analyzed" value={data.matchesAnalyzed} tone="primary" />
            <CounterCard label="Anomalies Detected" value={data.anomaliesDetected} tone="warning" />
            <CounterCard label="Statistical Confidence" value={parseFloat(data.statisticalConfidence)} decimals={1} suffix="%" tone="primary" />
          </div>
        </div>
      </section>

      {/* Findings */}
      <section className="mx-auto max-w-7xl px-4 py-16 md:px-6">
        <SectionHeading eyebrow="KEY FINDINGS" title="Four hypotheses. All significant." />
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {data.findings.map((f) => (
            <GlassCard key={f.id} className="flex flex-col gap-3">
              <div className="text-3xl">{f.icon}</div>
              <div className="flex items-center justify-between gap-2">
                <div className="text-xs uppercase tracking-widest text-muted-foreground">{f.title}</div>
                <StatBadge significant={f.significant} />
              </div>
              <div className="font-display text-lg font-semibold leading-snug">{f.stat}</div>
              <div className="text-xs text-muted-foreground mt-auto">{f.interpretation}</div>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* Overview cards */}
      <section className="mx-auto max-w-7xl px-4 pb-16 md:px-6 grid gap-6 lg:grid-cols-2">
        <GlassCard>
          <div className="text-xs uppercase tracking-widest text-muted-foreground">Three Eras of Hydration Breaks</div>
          <h3 className="mt-2 font-display text-2xl font-bold">A natural experiment across three regimes</h3>
          <div className="mt-6 relative">
            <div className="absolute left-4 right-4 top-1/2 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
            <div className="relative grid grid-cols-3 gap-4">
              {data.eras.map((era) => {
                const Icon = ERA_ICONS[era.id];
                return (
                  <div key={era.id} className="flex flex-col items-center text-center">
                    <div className="relative h-12 w-12 rounded-full border border-border bg-card grid place-items-center text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="mt-3 font-mono-num text-xs text-muted-foreground">{era.years}</div>
                    <div className="mt-1 text-sm font-semibold">Era {era.id}</div>
                    <div className="text-xs text-muted-foreground">{era.label}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="text-xs uppercase tracking-widest text-muted-foreground">GDP Classification · 2026</div>
          <h3 className="mt-2 font-display text-2xl font-bold">Group A vs Group B nations</h3>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <FlagGrid title="Group A (higher GDP)" nations={data.groupA} tone="primary" />
            <FlagGrid title="Group B (lower GDP)" nations={data.groupB} tone="warning" />
          </div>
        </GlassCard>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-24 md:px-6 text-center">
        <Link
          to="/historical"
          className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-all hover:shadow-[0_0_30px_var(--primary)]"
        >
          Explore the full analysis <ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </PageTransition>
  );
}

function CounterCard({ label, value, decimals, suffix, tone }: { label: string; value: number; decimals?: number; suffix?: string; tone: "primary" | "warning" }) {
  const color = tone === "warning" ? "text-amber-400" : "text-primary";
  return (
    <div className="glass rounded-2xl p-6 text-left">
      <div className="text-xs uppercase tracking-widest text-slate-400">{label}</div>
      <div className={`mt-2 font-display font-extrabold text-5xl font-mono-num ${color}`}>
        <AnimatedCounter value={value} decimals={decimals} suffix={suffix} />
      </div>
    </div>
  );
}

function SectionHeading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-[0.3em] text-primary">{eyebrow}</div>
      <h2 className="mt-2 font-display text-3xl md:text-4xl font-bold">{title}</h2>
    </div>
  );
}

function FlagGrid({ title, nations, tone }: { title: string; nations: { name: string; flag: string }[]; tone: "primary" | "warning" }) {
  const border = tone === "warning" ? "border-amber-500/30" : "border-primary/30";
  return (
    <div className={`rounded-xl border ${border} bg-card/40 p-4`}>
      <div className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{title}</div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {nations.map((n) => (
          <div key={n.name} className="flex items-center gap-1.5 rounded-md bg-background/60 px-2 py-1 text-xs">
            <span>{n.flag}</span>
            <span className="text-muted-foreground">{n.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Particles() {
  const dots = Array.from({ length: 24 });
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {dots.map((_, i) => (
        <span
          key={i}
          className="absolute h-1 w-1 rounded-full bg-primary/40"
          style={{
            top: `${(i * 37) % 100}%`,
            left: `${(i * 53) % 100}%`,
            animation: `float-particle ${4 + (i % 5)}s ease-in-out ${i * 0.3}s infinite`,
          }}
        />
      ))}
    </div>
  );
}
