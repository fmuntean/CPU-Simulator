@echo off

echo Select Board:
echo 1. Sample
echo 2. MC6802
set /p option=Selection?

if %option% == 1 python simulator-sample.py
if %option% == 2 python simulator-6802.py

pause