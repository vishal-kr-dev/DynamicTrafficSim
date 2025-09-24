# rl_agent/config.py

# --- Controller Timing Parameters (in seconds) ---
MIN_GREEN_TIME = 10
MAX_GREEN_TIME = 60
YELLOW_TIME = 4

# --- State Normalization Parameters ---
# The estimated maximum number of cars that can be in a single queue lane
MAX_QUEUE_PER_LANE = 7

# The number of incoming lanes for each approach
LANE_COUNTS = {
    "North": 2,
    "East": 2,
    "South": 2,
    "West": 2
}