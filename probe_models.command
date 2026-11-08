#!/usr/bin/env bash
# Double-click: checks which optional NVIDIA models your key can use. Log: results/probe_models.log
cd "$(dirname "$0")"
mkdir -p results
source .venv/bin/activate 2>/dev/null || { python3 -m venv .venv && source .venv/bin/activate && pip install -q -r requirements.txt; }
python3 probe_models.py 2>&1 | tee results/probe_models.log
echo "PROBE_FINISHED" | tee -a results/probe_models.log
