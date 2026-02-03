@echo off
REM Build script for Docker on Windows
REM Disables BuildKit to avoid pthread_create errors on WSL2
REM Uses platform specification to avoid OCI runtime issues

echo ============================================================
echo  Docker Build Script for Windows
echo ============================================================
echo.

REM Disable BuildKit to use legacy builder (more stable on Windows)
set DOCKER_BUILDKIT=0

REM Clear any cached failed layers first
echo Cleaning up any failed Docker layers...
docker builder prune -f >nul 2>&1

echo Building Docker image with legacy builder...
echo (This may take a few minutes on first build)
echo.

docker build --platform linux/amd64 --no-cache -t binance-dcr-bot .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  BUILD SUCCESSFUL!
    echo ============================================================
    echo.
    echo Run your container with:
    echo   docker run -d --name binance-bot binance-dcr-bot
    echo.
    echo Or run interactively:
    echo   docker run -it --rm binance-dcr-bot
    echo.
) else (
    echo.
    echo ============================================================
    echo  BUILD FAILED - OCI Runtime Error Recovery
    echo ============================================================
    echo.
    echo This error typically occurs due to Docker Desktop/WSL2 issues.
    echo.
    echo Try these steps IN ORDER:
    echo.
    echo   1. Close Docker Desktop completely
    echo   2. Open PowerShell as Administrator and run:
    echo      wsl --shutdown
    echo   3. Wait 10 seconds
    echo   4. Restart Docker Desktop
    echo   5. Wait for Docker Desktop to fully start
    echo   6. Run this script again
    echo.
    echo If the error persists:
    echo   - Create file: %%USERPROFILE%%\.wslconfig
    echo   - Add these lines:
    echo       [wsl2]
    echo       memory=4GB
    echo       processors=2
    echo   - Then repeat steps 1-6 above
    echo.
    echo Alternative: Try building with BuildKit enabled:
    echo   set DOCKER_BUILDKIT=1
    echo   docker build -t binance-dcr-bot .
    echo.
)
