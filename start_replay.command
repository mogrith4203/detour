#!/usr/bin/env bash
# Double-click: start Detour from the recorded run (REPLAY badge) for bad Wi-Fi. Close this window to stop.
cd "$(dirname "$0")"
DETOUR_REPLAY=1 ./run.sh
