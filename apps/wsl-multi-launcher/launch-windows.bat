@echo off
REM wsl-multi-launcher - Launch script for Windows
REM Place this file on your desktop and double-click to run
REM Uses default WSL distribution (Ubuntu-24.04)

set PROJECT_PATH=/home/ken/workspace/wsl-claude-commander/apps/wsl-multi-launcher

echo Starting wsl-multi-launcher...
wsl --cd %PROJECT_PATH% -- ./target/release/wsl-multi-launcher launch

pause
