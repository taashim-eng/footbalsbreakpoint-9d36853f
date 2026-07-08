"""
Central configuration for The Break Point – FIFA World Cup anomaly detection.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load environment variables ───────────────────────────────────────────────
load_dotenv()

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ── Directory layout ─────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure critical directories exist at import time
for _d in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── API keys (loaded from .env or OS environment) ────────────────────────────
BETFAIR_APP_KEY = os.getenv("BETFAIR_APP_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")

# ── Era / tournament definitions ─────────────────────────────────────────────
ERA_A = (2002, 2006, 2010)          # Early-modern era
ERA_B = (2014, 2018, 2022)          # Recent era (cooling breaks introduced)
ERA_C = (2026,)                      # Current tournament

ALL_TOURNAMENTS = ERA_A + ERA_B + ERA_C

# ── Analysis window (minutes) ────────────────────────────────────────────────
BREAK_WINDOW_START = 65              # Start of the "break-point" window
BREAK_WINDOW_END = 80               # End of the "break-point" window

# ── ROPE (Region of Practical Equivalence) ───────────────────────────────────
ROPE_DEFAULT = 0.10
ROPE_SENSITIVITY = [0.05, 0.10, 0.15, 0.20]

# ── Hypothesis testing ───────────────────────────────────────────────────────
N_PRIMARY_HYPOTHESES = 4

# ── Persistence ──────────────────────────────────────────────────────────────
DB_PATH = os.path.join(str(PROCESSED_DIR), "worldcup.db")

# ── Competition weighting for composite metrics ─────────────────────────────
COMPETITION_WEIGHTS = {
    "World Cup": 1.0,
    "Euro": 0.8,
    "Copa America": 0.8,
    "AFCON": 0.6,
    "Asian Cup": 0.6,
    "Gold Cup": 0.5,
}

# ── Venue coordinates (lat, lon) for key World Cup stadiums 2002–2026 ────────
VENUE_COORDS = {
    # ── 2002 (Korea / Japan) ──────────────────────────────────────────────
    "Seoul World Cup Stadium":          (37.5683, 126.8972),
    "Suwon World Cup Stadium":          (37.2844, 127.0368),
    "Busan Asiad Main Stadium":         (35.1906, 129.0584),
    "Daegu World Cup Stadium":          (35.8346, 128.5833),
    "Incheon Munhak Stadium":           (37.4369, 126.6978),
    "International Stadium Yokohama":   (35.5100, 139.6064),
    "Saitama Stadium":                  (35.8627, 139.7139),
    "Osaka Nagai Stadium":              (34.6159, 135.5190),
    "Miyagi Stadium":                   (38.3285, 140.9506),
    "Oita Stadium":                     (33.2100, 131.6100),

    # ── 2006 (Germany) ────────────────────────────────────────────────────
    "Olympiastadion Berlin":            (52.5147, 13.2395),
    "Allianz Arena":                    (48.2188, 11.6247),
    "Signal Iduna Park":                (51.4925, 7.4518),
    "FIFA World Cup Stadium Hamburg":   (53.5872, 9.8986),
    "RheinEnergieStadion":              (50.9335, 6.8748),
    "Commerzbank-Arena":                (50.0686, 8.6454),
    "Fritz-Walter-Stadion":             (49.4338, 7.7764),

    # ── 2010 (South Africa) ──────────────────────────────────────────────
    "Soccer City":                      (-26.2328, 27.9832),
    "Cape Town Stadium":                (-33.9035, 18.4114),
    "Moses Mabhida Stadium":            (-29.8283, 31.0283),
    "Nelson Mandela Bay Stadium":       (-33.9376, 25.5972),
    "Ellis Park Stadium":               (-26.2000, 28.0600),
    "Loftus Versfeld Stadium":          (-25.7519, 28.2231),
    "Free State Stadium":               (-29.1152, 26.2223),

    # ── 2014 (Brazil) ────────────────────────────────────────────────────
    "Maracanã":                         (-22.9121, -43.2302),
    "Arena Corinthians":                (-23.5453, -46.4741),
    "Estádio Castelão":                 (-3.8073, -38.5224),
    "Estádio Mineirão":                 (-19.8659, -43.9711),
    "Estádio Nacional Mané Garrincha":  (-15.7835, -47.8994),
    "Arena Fonte Nova":                 (-12.9785, -38.5042),

    # ── 2018 (Russia) ────────────────────────────────────────────────────
    "Luzhniki Stadium":                 (55.7155, 37.5537),
    "Krestovsky Stadium":              (59.9725, 30.2200),
    "Fisht Olympic Stadium":           (43.4023, 39.9558),
    "Kazan Arena":                      (55.8207, 49.1608),
    "Rostov Arena":                     (47.2091, 39.7389),
    "Ekaterinburg Arena":               (56.8328, 60.5727),

    # ── 2022 (Qatar) ─────────────────────────────────────────────────────
    "Lusail Stadium":                   (25.4195, 51.4907),
    "Al Bayt Stadium":                  (25.6527, 51.4875),
    "Stadium 974":                      (25.2939, 51.5472),
    "Education City Stadium":           (25.3107, 51.4246),
    "Al Thumama Stadium":               (25.2353, 51.5327),
    "Khalifa International Stadium":    (25.2633, 51.4483),
    "Ahmad Bin Ali Stadium":            (25.2505, 51.2675),
    "Al Janoub Stadium":                (25.1591, 51.5378),

    # ── 2026 (USA / Canada / Mexico) ─────────────────────────────────────
    "MetLife Stadium":                  (40.8135, -74.0745),
    "AT&T Stadium":                     (32.7473, -97.0945),
    "SoFi Stadium":                     (33.9535, -118.3392),
    "Hard Rock Stadium":                (25.9580, -80.2389),
    "NRG Stadium":                      (29.6847, -95.4107),
    "Mercedes-Benz Stadium":            (33.7553, -84.4006),
    "Lincoln Financial Field":          (39.9008, -75.1675),
    "Lumen Field":                      (47.5952, -122.3316),
    "Arrowhead Stadium":                (39.0489, -94.4839),
    "Gillette Stadium":                 (42.0909, -71.2643),
    "Levi's Stadium":                   (37.4033, -121.9694),
    "BMO Field":                        (43.6332, -79.4186),
    "BC Place":                         (49.2768, -123.1118),
    "Estadio Azteca":                   (19.3029, -99.1505),
    "Estadio BBVA":                     (25.6700, -100.2456),
    "Estadio Akron":                    (20.6810, -103.4625),
}
