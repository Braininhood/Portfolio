@echo off
cd /d "D:\Poker AI\poker_ai"
"D:\Poker AI\poker_ai\.venv\Scripts\python.exe" -m poker_ai train hhformer >> "D:\Poker AI\poker_ai\data\schedule\logs\train_hhformer.log" 2>&1
