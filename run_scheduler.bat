@echo off
echo Starting DiamondVault Auction Scheduler...
echo This will automatically check and update auction statuses
echo Press Ctrl+C to stop
echo.

cd /d "C:\Users\Administrator\Desktop\DiamondVault"
python manage.py scheduler --interval 60

pause
