import { createFileRoute } from "@tanstack/react-router";
import { useData, dataQueryOptions } from "@/hooks/useData";
import { GlassCard } from "@/components/dashboard/GlassCard";
import { PageTransition } from "@/components/dashboard/PageTransition";
import { Check, X } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export const Route = createFileRoute("/methodology")({
  head: () => ({
    meta: [
      { title: "Methodology — The Break Point" },
      { name: "description", content: "How to read the dashboard, statistical methods, pre-registered hypotheses, limitations, and data sources." },
      { property: "og:title", content: "Methodology — The Break Point" },
      { property: "og:description", content: "Statistical methods, hypotheses, and data provenance." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(dataQueryOptions("methodology")),
  component: Page,
});

function Page() {
  const { data } = useData("methodology");
  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl px-4 py-12 md:px-6">
        <div className="text-xs uppercase tracking-[0.3em] text-primary">Methodology</div>
        <h1 className="mt-2 font-display text-4xl font-bold">How the analysis works</h1>

        <Section title="How to Read This Dashboard">
          <p>Group A = higher-GDP nations. Group B = lower-GDP nations. The <em>Anomaly Index</em> summarizes statistical deviation from expected match patterns during the 65-80 minute hydration break window. Colors: <span className="text-emerald-400">green</span> normal, <span className="text-amber-400">amber</span> moderate, <span className="text-red-400">red</span> high.</p>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/5 p-4">
              <div className="text-sm font-semibold text-emerald-400 mb-2">What this CAN tell you</div>
              <ul className="text-xs space-y-1 text-muted-foreground list-disc pl-4">
                <li>Whether outcomes systematically differ by GDP group in the break window</li>
                <li>How much markets moved relative to match state</li>
                <li>Whether Era C differs from Era A/B</li>
              </ul>
            </div>
            <div className="rounded-xl border border-red-500/40 bg-red-500/5 p-4">
              <div className="text-sm font-semibold text-red-400 mb-2">What this CANNOT tell you</div>
              <ul className="text-xs space-y-1 text-muted-foreground list-disc pl-4">
                <li>That any specific match was manipulated</li>
                <li>Causal explanations for individual outcomes</li>
                <li>The intent of any actor, official, or organization</li>
              </ul>
            </div>
          </div>
        </Section>

        <Section title="Three Eras of Analysis">
          <div className="mt-2 space-y-3 text-sm">
            <div className="flex gap-3"><span className="font-mono-num text-primary w-24 shrink-0">Era A</span><span>2002–2010 · No breaks · N ≈ 380 matches (baseline)</span></div>
            <div className="flex gap-3"><span className="font-mono-num text-primary w-24 shrink-0">Era B</span><span>2014–2022 · Conditional breaks · N ≈ 512 matches</span></div>
            <div className="flex gap-3"><span className="font-mono-num text-primary w-24 shrink-0">Era C</span><span>2026 · Mandatory breaks · N ≈ 104 matches (natural experiment)</span></div>
          </div>
        </Section>

        <GlassCard className="mt-8">
          <h2 className="font-display text-xl font-bold">Statistical Methods</h2>
          <Accordion type="single" collapsible className="mt-4">
            {METHODS.map((m) => (
              <AccordionItem key={m.title} value={m.title}>
                <AccordionTrigger className="text-sm font-semibold">{m.title}</AccordionTrigger>
                <AccordionContent className="text-sm text-muted-foreground">{m.body}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </GlassCard>

        <Section title="Pre-Registered Hypotheses">
          <div className="mt-2 space-y-4">
            {data.hypotheses.map((h) => (
              <div key={h.id} className="rounded-xl border border-border p-4">
                <div className="flex items-baseline gap-3">
                  <span className="font-mono-num text-primary font-semibold">{h.id}</span>
                  <span className="text-sm">{h.text}</span>
                </div>
                <pre className="mt-2 overflow-x-auto rounded bg-background/60 p-3 text-[11px] font-mono-num text-muted-foreground whitespace-pre-wrap">{h.formal}</pre>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            Pre-registration constrains researcher degrees of freedom. All four hypotheses were logged before Era C data collection.
            Multiple comparisons are corrected via Benjamini-Hochberg FDR at q = 0.10.
          </p>
        </Section>

        <Section title="Limitations & Caveats">
          <ul className="mt-2 space-y-2 text-sm text-muted-foreground list-disc pl-5">
            <li>Era C sample size (N=104) limits detectable effect sizes; d ≥ 0.35 required for 80% power.</li>
            <li>2026 predictions are out-of-time: model was frozen prior to tournament start.</li>
            <li>Controls include FIFA ranking, squad value, temperature, and stage. Unobserved confounders (referee assignment, travel fatigue) are not fully captured.</li>
            <li>Statistical association is not causal evidence.</li>
          </ul>
        </Section>

        <Section title="Data Sources">
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-2 pr-2">Name</th><th className="py-2 pr-2">Coverage</th><th className="py-2 pr-2">License</th><th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.sources.map((s) => (
                  <tr key={s.name} className="border-b border-border/50">
                    <td className="py-2 pr-2"><a href={s.link} target="_blank" rel="noreferrer" className="text-primary hover:underline">{s.name}</a></td>
                    <td className="py-2 pr-2 text-muted-foreground">{s.coverage}</td>
                    <td className="py-2 pr-2 font-mono-num text-muted-foreground">{s.license}</td>
                    <td className="py-2">
                      {s.compliant ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400"><Check className="h-3 w-3" /> Compliant</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-amber-400"><X className="h-3 w-3" /> Restricted</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section title="Reproducibility">
          <div className="mt-2 grid gap-3 md:grid-cols-3 text-xs">
            <div><div className="text-muted-foreground uppercase tracking-widest">Version</div><div className="font-mono-num mt-1">v{data.version}</div></div>
            <div><div className="text-muted-foreground uppercase tracking-widest">Random seed</div><div className="font-mono-num mt-1">{data.seed}</div></div>
            <div><div className="text-muted-foreground uppercase tracking-widest">Repo</div><div className="mt-1"><a href="#" className="text-primary hover:underline">github.com/breakpoint</a></div></div>
          </div>
        </Section>
      </div>
    </PageTransition>
  );
}

const METHODS = [
  { title: "Bayesian DiD with 3-way interaction", body: "We fit a Bayesian regression with GDP-group × break-window × era interaction. Priors are weakly informative; posterior HDIs are reported at 95%. Convergence is monitored via R̂ < 1.01." },
  { title: "Cox Proportional Hazards survival", body: "Time-to-first-concession is modeled with a Cox PH regression stratified by tournament, with baseline hazards estimated non-parametrically. Proportional hazards is checked via Schoenfeld residuals." },
  { title: "Win probability gradient boosting", body: "XGBoost model trained on Fjelstul + StatsBomb events predicts win probability at each minute. Features include score, time, red cards, xG, and rankings. Calibration is verified on a held-out era." },
  { title: "XGBoost + SHAP (Stage 1)", body: "Stage 1 predicts match outcome from pre-match features to compute match-model residuals. SHAP values decompose each anomaly score into interpretable feature contributions." },
  { title: "Two-stage betting analysis", body: "Stage 2 regresses in-play odds movements on Stage-1 residuals. Robust standard errors are clustered by tournament. Publication-quality checks include Granger causality and stationarity (ADF)." },
  { title: "Statistical Anomaly Index", body: "Weighted composite of five components: goal-timing deviation (0.30), odds movement (0.25), win-prob swing (0.20), xG differential (0.15), and substitution timing (0.10). Missing components are re-weighted proportionally." },
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-10">
      <h2 className="font-display text-2xl font-bold">{title}</h2>
      <div className="mt-3 text-sm leading-relaxed text-foreground/90">{children}</div>
    </section>
  );
}
