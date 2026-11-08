#!/usr/bin/env bash
# Double-click in Finder: starts Detour LIVE and records every Nemotron response to replays/ (venue backup).
cd "$(dirname "$0")"
mkdir -p results
DETOUR_RECORD=1 ./run.sh 2>&1 | tee results/record_server.log
