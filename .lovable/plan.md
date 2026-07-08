# The Break Point — Build Plan

A dark, investigative analytics dashboard investigating whether FIFA World Cup hydration breaks disproportionately affect lower-GDP nations. Six pages, mock data, premium Bloomberg-terminal aesthetic.

## Stack & conventions

- TanStack Start (already scaffolded) with file-based routing under `src/routes/` — using this instead of React Router since it's the project's router. All nav uses `<Link to=...>`.
- Tailwind v4 tokens in `src/styles.css`, shadcn/ui components, Recharts for charts, Framer Motion for transitions/counters.
- Fonts (Inter, JetBrains Mono, Outfit) loaded via `<link>` in `__root.tsx` head.
- Mock JSON in `public/data/`, typed in `src/types/`, fetched via `src/hooks/useData.ts` (React Query wrapper).

## Design system (src/styles.css)

Add dark-first tokens (oklch equivalents of the requested hex):
- `--background` #0a0e1a, `--card` #111827, `--elevated` #1e293b
- `--primary` #3b82f6, `--danger` #ef4444, `--warning` #f59e0b, `--success` #10b981
- `--foreground` #f8fafc, `--muted-foreground` #94a3b8, `--muted` #64748b
- `--border` rgba(255,255,255,0.08)
- `--gradient-hero` linear-gradient(#0f172a, #1e1b4b, #0f172a)
- `--font-sans` Inter, `--font-mono` JetBrains Mono, `--font-display` Outfit
- Custom scrollbar, `.glass` utility (backdrop-blur + border), `pulse-red` / `pulse-amber` keyframes for anomaly glow.
- Dark mode default (add `dark` class on `<html>`); light mode toggle inverts.

## Routes

```
src/routes/
  __root.tsx           # font links, header, disclaimer banner, footer, dark class
  index.tsx            # Overview (redirect target)
  historical.tsx       # Historical Analysis
  monitor.tsx          # 2026 Monitor
  betting.tsx          # Betting Intelligence
  explorer.tsx         # Match Explorer (?matchId=... search param)
  methodology.tsx      # Methodology
```

Each leaf sets its own `head()` (title, description, og:title/description).

## Shared components (src/components/)

- `SiteHeader.tsx` — logo (⚽ with fracture SVG), nav tabs with active blue glow, "Last updated" badge, theme toggle.
- `DisclaimerBanner.tsx` — amber alert, dismissible via `sessionStorage`.
- `SiteFooter.tsx` — data sources, methodology link, version.
- `GlassCard.tsx`, `StatBadge.tsx` (Significant / Not Significant), `AnomalyGauge.tsx` (SVG circular gauge, color by score), `AnimatedCounter.tsx` (Framer Motion `useInView` + `animate`), `LoadingSkeleton.tsx`, `PageTransition.tsx` (fade/slide wrapper).
- Chart primitives: `HeatmapChart`, `ForestPlot`, `SurvivalCurve`, `RadarBreak`, `OddsTimeline`, `ScatterResiduals` — all Recharts-based with dark theme.

## Data layer

`public/data/`:
- `overview.json` — headline stats, findings, era summary, GDP group flags.
- `historical.json` — per era: heatmap bins by group, DiD forest point + HDI, KM survival series, winprob distribution, power analysis.
- `matches2026.json` — ~48 realistic 2026 matches (Mexico/USA/Canada hosts + real qualifiers), each with teams, flags, gdpGroup, score, breakScore, anomalyIndex, winProbSwing, events, radarPreVsPost, componentBreakdown, shap, odds series (some null).
- `betting.json` — scatter (residual vs odds move), volume heatmap, findings.
- `methodology.json` — hypotheses, sources, versions.

`src/types/` — one interface file per JSON.
`src/hooks/useData.ts` — `useData<T>(key)` = `useSuspenseQuery` fetching `/data/{key}.json`.

## Page details

**Overview (`/`)**: hero with gradient + animated dot particles (CSS), 3 counter cards, 4 findings cards (2×2 on tablet), 2 overview cards (era timeline SVG, GDP flag grid), CTA to `/historical`.

**Historical (`/historical`)**: era selector (3 cards, state via `useSearch` with `era` param, default `C`); sections render based on era — heatmap always, DiD forest only for C, survival curves, winprob distribution, collapsible power analysis.

**2026 Monitor (`/monitor`)**: filter bar (stage, group, anomaly level) + sort — all in URL search params via `validateSearch`. Grid of match cards + leaderboard sidebar. Card click → `/explorer?matchId=...`.

**Betting (`/betting`)**: caveat banner, scatter, per-match odds trajectory (match dropdown), volume heatmap split by leading group, 3 findings cards.

**Match Explorer (`/explorer`)**: `validateSearch` for `matchId`; defaults to highest-anomaly match. Two-column layout: timeline + score trajectory + radar on left; gauge + component bars + context + SHAP waterfall on right; collapsible odds panel below.

**Methodology (`/methodology`)**: long-form, max-w-3xl, shadcn `Accordion` for method sections, comparison boxes (green/red border), data source table with badges.

## Animations & polish

- `PageTransition` wraps each page's root — Framer Motion `initial/animate/exit` fade+slide.
- Counters use `useInView` + `animate` from `framer-motion`.
- Anomaly indicators with `animate-pulse` on red/amber; custom keyframes for softer glow.
- All cards: `transition-all hover:border-primary/40 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)]`.
- Loading skeletons via shadcn `Skeleton` for each data-bound section.
- Responsive: grids collapse 3→2→1; sidebar becomes stacked on mobile; header nav collapses to sheet on `<md`.

## Dependencies to add

`framer-motion`, `recharts` (verify), `@fontsource-variable/inter` `@fontsource-variable/jetbrains-mono` `@fontsource/outfit` (or just `<link>` to Google Fonts — will use `<link>` per stack rules).

## Out of scope (mock only)

No backend/Cloud, no real data pipelines. All numbers are plausible fixtures generated in the JSON files. Betting/odds data is illustrative.

## Deliverable

Fully navigable dashboard with all 6 pages populated, responsive, dark theme by default with light toggle, mock data driving every chart and card, page transitions and micro-animations throughout.