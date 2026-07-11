import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/review")({
  head: () => ({
    meta: [
      { title: "Statistical Review — The Break Point" },
      { name: "description", content: "The full forensic statistics dossier: an adversarially reviewed analysis of the hydration-break anomaly, with effect sizes, the heat lead, the acclimatisation test, and plain-English explainers." },
      { property: "og:title", content: "Statistical Review — The Break Point" },
      { property: "og:description", content: "Effect sizes, confidence intervals, the heat × economics lead, and ELI5 explainers for every metric." },
    ],
  }),
  component: Page,
});

function Page() {
  // The report is a self-contained document (its own styles, theme toggle and
  // SVG charts), so we embed it in a same-origin iframe rather than re-implement
  // it in React. "Open full screen" pops it out for reading or printing.
  return (
    <div className="flex flex-col" style={{ height: "calc(100dvh - 3.5rem)" }}>
      <div className="flex items-center justify-between gap-3 border-b border-border/60 bg-background/70 px-4 py-2 md:px-6">
        <span className="text-[11px] uppercase tracking-[0.28em] text-primary">
          Statistical Review · Forensic Dossier
        </span>
        <a
          href="/review.html"
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono-num text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Open full screen ↗
        </a>
      </div>
      <iframe
        src="/review.html"
        title="The Break Point — Forensic Statistics Dossier"
        className="w-full flex-1 border-0 bg-background"
        loading="eager"
      />
    </div>
  );
}
