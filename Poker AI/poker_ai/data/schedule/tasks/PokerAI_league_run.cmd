@echo off
cd /d "D:\Poker AI\poker_ai"
"D:\Poker AI\poker_ai\.venv\Scripts\python.exe" -m poker_ai league run >> "D:\Poker AI\poker_ai\data\schedule\logs\league_run.log" 2>&1
