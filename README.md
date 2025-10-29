# Intelligent Traffic Light Control System

DQN-based traffic light control with emergency vehicle preemption.

## Setup

1. **Install SUMO**: Download from https://sumo.dlr.de/docs/Installing/index.html
2. **Set environment variable**: `export SUMO_HOME="/usr/share/sumo"` (Linux/Mac) or set in Windows
3. **Install Python packages**: `pip install -r requirements.txt`

## Quick Start

### One Command - Full Pipeline
```bash
python run_simulation.py full --episodes 100
```
This runs: setup → train → test → compare → analyze

### Individual Commands

**Setup Environment**
```bash
python run_simulation.py setup
```

**Train Model**
```bash
python run_simulation.py train --episodes 100
```
Logs in `logs/` folder: waiting times, queue lengths, phase changes, vehicle counts

**Test Model**
```bash
python run_simulation.py test --episodes 5
```

**Compare with Fixed-Time**
```bash
python run_simulation.py compare
```

**Analyze Results**
```bash
python run_simulation.py analyze
```

**Generate Traffic Patterns**
```bash
python run_simulation.py traffic --pattern rush_hour
```

## Features

- **Dynamic phase control** based on queue lengths
- **Emergency vehicle preemption** with rule-based override
- **Comprehensive logging** during training and testing
- **Multiple traffic patterns** (rush hour, random, uniform, incident)
- **Data analysis tools** with visualizations

## Additional Tools

### Generate Dynamic Traffic
```bash
# Rush hour pattern
python dynamic_traffic_gen.py rush_hour

# Random pattern
python dynamic_traffic_gen.py random

# Incident scenario with emergency vehicles
python dynamic_traffic_gen.py incident
```

### Analyze Training Data
```bash
python data_analyzer.py
```
Generates:
- training_analysis.png (performance graphs)
- vehicle_distribution.png (pie chart)
- training_summary.csv (exportable data)

## Project Structure
```
├── traffic_dqn_main.py          # Main training script
├── sumo_network_gen.py          # Network generation
├── test_model.py                # Testing and comparison
├── dynamic_traffic_gen.py       # Dynamic traffic patterns
├── data_analyzer.py             # Analysis and visualization
├── models/                      # Saved DQN models
├── logs/                        # Training episode logs
└── test_logs/                   # Test results
```



All Commands
Quick Start (Recommended)
bash# Run everything: setup → train → test → compare → analyze
python run_simulation.py full --episodes 100
Individual Commands
1. Setup Environment
bashpython run_simulation.py setup
Creates network files and directories
2. Train Model
bash# Train with default 100 episodes
python run_simulation.py train

# Train with custom episodes
python run_simulation.py train --episodes 200
Saves model to models/traffic_dqn.pth, logs to logs/
3. Test Model
bash# Test with GUI (5 episodes)
python run_simulation.py test

# Test without GUI
python run_simulation.py test --no-gui

# Test with more episodes
python run_simulation.py test --episodes 10
4. Compare Performance
bash# Compare DQN vs Fixed-Time control
python run_simulation.py compare
5. Analyze Results
bash# Generate graphs and CSV
python run_simulation.py analyze
Creates training_analysis.png, vehicle_distribution.png, training_summary.csv
6. Generate Traffic Patterns
bash# Rush hour pattern (default)
python run_simulation.py traffic --pattern rush_hour

# Random traffic
python run_simulation.py traffic --pattern random

# Uniform traffic
python run_simulation.py traffic --pattern uniform

# Emergency incident scenario
python run_simulation.py traffic --pattern incident
Direct Python Scripts (Alternative)
bash# Generate network
python sumo_network_gen.py

# Train model
python traffic_dqn_main.py

# Test model
python test_model.py

# Compare models
python test_model.py --compare

# Analyze data
python data_analyzer.py

# Generate dynamic traffic
python dynamic_traffic_gen.py rush_hour
Common Workflows
First Time Setup:
bashpython run_simulation.py setup
python run_simulation.py train --episodes 100
Quick Test:
bashpython run_simulation.py test --episodes 3 --no-gui
Full Experiment:
bashpython run_simulation.py full --episodes 200