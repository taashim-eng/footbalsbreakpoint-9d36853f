import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
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

export const dataQueryOptions = <K extends keyof DataMap>(key: K) =>
  queryOptions({
    queryKey: ["data", key],
    queryFn: async (): Promise<DataMap[K]> => {
      const res = await fetch(`/data/${key}.json`);
      if (!res.ok) throw new Error(`Failed to load ${key}`);
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });

export function useData<K extends keyof DataMap>(key: K) {
  return useSuspenseQuery(dataQueryOptions(key));
}
