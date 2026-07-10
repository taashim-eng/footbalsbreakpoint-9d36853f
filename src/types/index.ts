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
  eras: { id: "A" | "B" | "C"; years: string; label: string; icon: string; startDate: string; endDate: string }[];
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
  startDate: string;
  endDate: string;
  sampleSize: number;
  heatmap: HeatmapBin[];
  did?: { estimate: number; lower: number; upper: number; ropeLow: number; ropeHigh: number };
  survival: { minute: number; groupA: number; groupB: number; groupAUpper: number; groupALower: number; groupBUpper: number; groupBLower: number }[];
  logRankP: number;
  winProb: { bucket: string; groupA: number; groupB: number }[];
  mannWhitneyP: number;
  power: { n: number; detectableEffect: number };
  caption: string;
  source?: string;
}

export interface HistoricalData {
  eras: EraData[];
}


export interface ScatterPoint {
  matchId: string;
  date: string | null;
  competition: string;
  stage: string;
  match: string;
  residual: number;
  oddsMove: number;
  anomalyLevel: AnomalyLevel;
  source: string;
}

export interface BettingData {
  scatter: ScatterPoint[];
  oddsMoveSource: string;
  findings: { title: string; stat: string; detail: string }[];
  correlation: number;
  pValue: number;
}

export interface Match2026 {
  matchId: string;
  date: string;
  competition: string;
  stage: string;
  homeTeam: string;
  awayTeam: string;
  homeFlag: string;
  awayFlag: string;
  venue: string;
  city: string;
  finalScore: { home: number; away: number };
  penalties?: { home: number; away: number };
  source: string;
}

export interface Matches2026Data {
  competition: string;
  lastUpdated: string;
  source: string;
  note: string;
  matches: Match2026[];
}

export interface MethodologyData {
  hypotheses: { id: string; text: string; formal: string }[];
  sources: { name: string; coverage: string; license: string; link: string; compliant: boolean; startDate?: string; endDate?: string }[];
  version: string;
  seed: number;
  lastUpdated?: string;
}
