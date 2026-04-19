#!/bin/sh
# prox-loader — start the Prox Loader GUI session.
# Run this after logging in on the physical console (tty1).
# Stops any previous instance first to avoid deadlock, then starts fresh.
systemctl stop prox-loader 2>/dev/null; sleep 0.5
exec systemctl start prox-loader
