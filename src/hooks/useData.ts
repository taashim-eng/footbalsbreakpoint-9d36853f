import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import overviewJson from "@/data/overview.json";
import historicalJson from "@/data/historical.json";
import matches2026Json from "@/data/matches2026.json";
import bettingJson from "@/data/betting.json";
import methodologyJson from "@/data/methodology.json";
import type {
  OverviewData,
  HistoricalData,
  Match2026,
  BettingData,
  MethodologyData,
} from "@/types";

type DataMap = {
  overview: OverviewData;
  historical: HistoricalData;
  matches2026: Match2026[];
  betting: BettingData;
  methodology: MethodologyData;
};

// Nudge: Force Vite to invalidate module cache and re-bundle updated static JSON data
const DATA: DataMap = {
  overview: overviewJson as unknown as OverviewData,
  historical: historicalJson as unknown as HistoricalData,
  matches2026: matches2026Json as unknown as Match2026[],
  betting: bettingJson as unknown as BettingData,
  methodology: methodologyJson as unknown as MethodologyData,
};

export const dataQueryOptions = <K extends keyof DataMap>(key: K) =>
  queryOptions({
    queryKey: ["data", key],
    queryFn: async (): Promise<DataMap[K]> => DATA[key],
    staleTime: Infinity,
  });

export function useData<K extends keyof DataMap>(key: K) {
  return useSuspenseQuery(dataQueryOptions(key));
}
