@echo off
REM Build script for Docker on Windows
REM Disables BuildKit to avoid pthread_create errors on WSL2

echo Building Docker image with legacy builder (BuildKit disabled)...
echo.

set DOCKER_BUILDKIT=0
docker build -t binance-dcr-bot .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful! Run with: docker run -d --name binance-bot binance-dcr-bot
) else (
    echo.
    echo Build failed. Try these steps:
    echo   1. Restart Docker Desktop
    echo   2. Increase WSL2 memory in %%USERPROFILE%%\.wslconfig
    echo   3. Run: wsl --shutdown   then restart Docker Desktop
)
