import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import overviewJson from "@/data/overview.json";
import historicalJson from "@/data/historical.json";
import bettingJson from "@/data/betting.json";
import methodologyJson from "@/data/methodology.json";
import matches2026Json from "@/data/matches2026.json";
import type {
  OverviewData,
  HistoricalData,
  BettingData,
  MethodologyData,
  Matches2026Data,
} from "@/types";

type DataMap = {
  overview: OverviewData;
  historical: HistoricalData;
  betting: BettingData;
  methodology: MethodologyData;
  matches2026: Matches2026Data;
};

const DATA: DataMap = {
  overview: overviewJson as unknown as OverviewData,
  historical: historicalJson as unknown as HistoricalData,
  betting: bettingJson as unknown as BettingData,
  methodology: methodologyJson as unknown as MethodologyData,
  matches2026: matches2026Json as unknown as Matches2026Data,
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
