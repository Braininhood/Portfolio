@echo off
cd /d "D:\Poker AI\poker_ai"
"D:\Poker AI\poker_ai\.venv\Scripts\python.exe" -m poker_ai features build >> "D:\Poker AI\poker_ai\data\schedule\logs\features_build.log" 2>&1
