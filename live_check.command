#!/usr/bin/env bash
# Double-click in Finder to run the live check. Output is also saved to results/live_check.log
cd "$(dirname "$0")"
mkdir -p results
./live_check.sh 2>&1 | tee results/live_check.log
echo "LIVE_CHECK_FINISHED exit=${PIPESTATUS[0]}" | tee -a results/live_check.log
