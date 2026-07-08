export type GdpGroup = "A" | "B";
export type AnomalyLevel = "high" | "moderate" | "normal";
export type Stage = "Group" | "R16" | "QF" | "SF" | "Final";

export interface Finding {
  id: string;
  icon: string;
  title: string;
  stat: string;
  interpretation: string;
  significant: boolean;
}

export interface OverviewData {
  matchesAnalyzed: number;
  anomaliesDetected: number;
  statisticalConfidence: string;
  lastUpdated: string;
  findings: Finding[];
  eras: { id: "A" | "B" | "C"; years: string; label: string; icon: string }[];
  groupA: { name: string; flag: string }[];
  groupB: { name: string; flag: string }[];
}

export interface HeatmapBin {
  bin: string;
  groupA: number;
  groupB: number;
  highlight?: boolean;
}

export interface EraData {
  id: "A" | "B" | "C";
  label: string;
  years: string;
  sampleSize: number;
  heatmap: HeatmapBin[];
  did?: { estimate: number; lower: number; upper: number; ropeLow: number; ropeHigh: number };
  survival: { minute: number; groupA: number; groupB: number; groupAUpper: number; groupALower: number; groupBUpper: number; groupBLower: number }[];
  logRankP: number;
  winProb: { bucket: string; groupA: number; groupB: number }[];
  mannWhitneyP: number;
  power: { n: number; detectableEffect: number };
  caption: string;
}

export interface HistoricalData {
  eras: EraData[];
}

export interface MatchEvent {
  minute: number;
  type: "goal" | "card" | "sub";
  team: "home" | "away";
  label: string;
}

export interface OddsPoint {
  minute: number;
  groupBProb: number;
  volume: number;
}

export interface Match2026 {
  id: string;
  date: string;
  stage: Stage;
  group?: string;
  home: { name: string; flag: string; gdp: GdpGroup; score: number };
  away: { name: string; flag: string; gdp: GdpGroup; score: number };
  breakScore: string;
  anomalyIndex: number;
  anomalyLevel: AnomalyLevel;
  winProbSwing: number;
  venue: string;
  temperatureC: number;
  events: MatchEvent[];
  scoreTrajectory: { minute: number; diff: number }[];
  radar: { metric: string; pre: number; post: number }[];
  componentBreakdown: { label: string; weight: number; score: number | null }[];
  shap: { feature: string; value: number }[];
  odds: OddsPoint[] | null;
  fifaRankHome: number;
  fifaRankAway: number;
  squadValueHomeM: number;
  squadValueAwayM: number;
}

export interface BettingData {
  scatter: { residual: number; oddsMove: number; anomalyLevel: AnomalyLevel; match: string }[];
  volumeByMinute: { minute: number; bLeading: number; aLeading: number }[];
  findings: { title: string; stat: string; detail: string }[];
  correlation: number;
  pValue: number;
}

export interface MethodologyData {
  hypotheses: { id: string; text: string; formal: string }[];
  sources: { name: string; coverage: string; license: string; link: string; compliant: boolean }[];
  version: string;
  seed: number;
}
