@echo off
REM Script untuk menjalankan Python dan save output ke file
REM Windows Batch File

echo ============================================
echo Starting IoT ASCON System with Logging
echo ============================================
echo.

REM Create logs directory
if not exist logs mkdir logs

REM Get timestamp
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%

echo Starting MQTT Publisher...
start "Publisher" cmd /k "python mqtt_publisher.py 2>&1 | tee logs/publisher_%timestamp%.log"

timeout /t 3

echo Starting MQTT Subscriber...
start "Subscriber" cmd /k "python mqtt_subscriber.py 2>&1 | tee logs/subscriber_%timestamp%.log"

echo.
echo ============================================
echo All processes started!
echo Logs saved to: logs/
echo Press any key to stop all processes...
echo ============================================
pause

REM Stop all Python processes
taskkill /F /IM python.exe /T

echo.
echo ============================================
echo All processes stopped
echo ============================================
pause