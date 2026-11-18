@echo off
title UrbanTwin Traffic Collector Daemon
cd /d "%~dp0\.."
echo ========================================================
echo UrbanTwin Continuous Traffic Collection Daemon
echo Polling TomTom Flow Segment API every 15 minutes...
echo ========================================================
python -u scripts\traffic_collector_daemon.py
pause
