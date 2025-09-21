# --- Visual Display Switch ---
ENABLE_GUI_DISPLAY = True

# --- Controller Timing Parameters (in seconds) ---
MIN_GREEN_TIME = 10
MAX_GREEN_TIME = 60
YELLOW_TIME = 4
TIME_PER_CAR = 2

# --- Phase Definitions (One-Side-at-a-Time) ---
PHASES = {
    "North Green":  "GGgggrrrrrrrrrrrrrrr",
    "North Yellow": "yyyyyrrrrrrrrrrrrrrr",
    "East Green":   "rrrrrGGgggrrrrrrrrrr",
    "East Yellow":  "rrrrryyyyyrrrrrrrrrr",
    "South Green":  "rrrrrrrrrrGGgggrrrrr",
    "South Yellow": "rrrrrrrrrryyyyyrrrrr",
    "West Green":   "rrrrrrrrrrrrrrrGGggg",
    "West Yellow":  "rrrrrrrrrrrrrrryyyyy"
}