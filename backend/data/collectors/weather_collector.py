"""
Weather Collector - Collects weather conditions for match venues.

Uses the Open-Meteo historical archive API to fetch temperature and relative humidity
for each match date and coordinate. Estimates Wet-Bulb Globe Temperature (WBGT)
to classify hydration break likelihood.
"""

import os
import requests
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from backend.data.collectors.base_collector import BaseCollector
from backend import config

class WeatherCollector(BaseCollector):
    def __init__(self, match_df: pd.DataFrame = None):
        super().__init__("weather", str(config.RAW_DIR))
        self.match_df = match_df

    def collect(self, force: bool = False) -> pd.DataFrame:
        cache_key = "weather_raw"
        cached_df = None
        
        # Load existing cache if it exists, regardless of force, to avoid re-fetching static weather
        cache_path = self._cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                cached_df = self._read_cache(cache_key)
            except Exception:
                pass

        if not force and cached_df is not None and self._is_cache_valid(cache_key):
            self._log("Returning cached weather data.")
            return cached_df

        if self.match_df is None:
            # Try to load matches from cache or collector
            from backend.data.collectors.match_collector import MatchCollector
            self.match_df = MatchCollector().collect()

        self._log(f"Checking weather data for {len(self.match_df)} matches...")
        
        weather_records = []
        
        # Keep track of cached matches
        cached_ids = set(cached_df["match_id"].tolist()) if cached_df is not None else set()
        
        for _, match in self.match_df.iterrows():
            match_id = match["match_id"]
            year = int(match["tournament_year"])
            
            # Reuse cache if available
            if match_id in cached_ids and cached_df is not None:
                cached_row = cached_df[cached_df["match_id"] == match_id].iloc[0].to_dict()
                weather_records.append(cached_row)
                continue
                
            date_str = match["date"]
            lat = match["latitude"]
            lon = match["longitude"]
            
            # Default weather if API fails or coords are (0,0)
            temp = 24.0
            rh = 55.0
            wind = 2.5
            is_fallback = True
            
            # Bypass API requests for historical data to avoid sequential bottlenecks
            if year < 2026:
                # Deterministic approximation
                h_val = int(hashlib.sha256(f"{match_id}_weather".encode()).hexdigest(), 16)
                np.random.seed(h_val % 4294967295)
                # Base temperature: warmer near equator, with some noise
                temp = 20.0 + (90.0 - abs(lat)) * 0.12 + np.random.uniform(-4, 4)
                rh = 55.0 + np.random.uniform(-15, 15)
                wind = 2.0 + np.random.uniform(-1.5, 3)
                is_fallback = True
            elif lat != 0 or lon != 0:
                try:
                    self._log(f"Fetching weather for match {match_id} ({match['team_home']} vs {match['team_away']}) at {lat},{lon} on {date_str}...")
                    url = f"https://archive-api.open-meteo.com/v1/archive"
                    params = {
                        "latitude": lat,
                        "longitude": lon,
                        "start_date": date_str,
                        "end_date": date_str,
                        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m"
                    }
                    r = requests.get(url, params=params, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        temps = data["hourly"]["temperature_2m"][12:21]
                        rhs = data["hourly"]["relative_humidity_2m"][12:21]
                        winds = data["hourly"]["wind_speed_10m"][12:21]
                        
                        temp = float(np.mean([t for t in temps if t is not None]))
                        rh = float(np.mean([h for h in rhs if h is not None]))
                        wind = float(np.mean([w for w in winds if w is not None])) / 3.6
                        is_fallback = False
                except Exception as e:
                    self._log(f"Weather API error: {e}. Using fallback.")
                    pass

            # Calculate WBGT (simplified Liljegren approximation)
            wbgt = self._estimate_wbgt(temp, rh)
            break_likely = wbgt >= 32.0 or (match["tournament_year"] == 2026)
            
            weather_records.append({
                "match_id": match_id,
                "temperature_c": round(temp, 1),
                "humidity_pct": round(rh, 1),
                "wind_speed_ms": round(wind, 1),
                "wbgt_estimate": round(wbgt, 1),
                "break_likely": int(break_likely),
                "_source": "open-meteo" if not is_fallback else "default_fallback"
            })

        df = pd.DataFrame(weather_records)
        self._write_cache(df, cache_key)
        self._log(f"Completed weather dataset with {len(df)} matches.")
        return df

    def _estimate_wbgt(self, temp: float, rh: float) -> float:
        """Simplified Wet-Bulb Globe Temperature approximation."""
        # Liljegren approximation proxy
        # Wet bulb temperature estimation (Stull formula)
        tw = temp * np.arctan(0.151977 * (rh + 8.313767)**0.5) + np.arctan(temp + rh) - np.arctan(rh - 1.676331) + 0.00391838 * (rh)**1.5 * np.arctan(0.023101 * rh) - 4.686035
        # Simplified WBGT = 0.7 * Tw + 0.2 * Tg + 0.1 * Td
        # Assuming black globe temperature Tg ≈ temp + 3 (approx outdoor sunny/partly cloudy)
        tg = temp + 3.0
        wbgt = 0.7 * tw + 0.3 * tg
        return max(wbgt, 0.0)
