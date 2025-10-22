@echo off
REM SSLTriage Installation Script for Windows
REM Version: 1.0.0

echo ============================================
echo SSLTriage Installation Script
echo ============================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges
) else (
    echo WARNING: Not running as administrator
    echo Some package installations may fail
    echo.
)

REM Detect architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set ARCH=x64
) else if "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set ARCH=arm64
) else (
    set ARCH=x86
)
echo Detected architecture: %ARCH%
echo.

REM Check if Python is installed
echo Checking for Python...
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python found:
    python --version
) else (
    echo [ERROR] Python not found
    echo.
    echo Please install Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo Or using winget:
    echo   winget install Python.Python.3.11
    echo.
    pause
    exit /b 1
)
echo.

REM Check if pip is installed
echo Checking for pip...
pip --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] pip found:
    pip --version
) else (
    echo [ERROR] pip not found
    echo.
    echo Installing pip...
    python -m ensurepip --upgrade
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install pip
        pause
        exit /b 1
    )
)
echo.

REM Check if winget is available
echo Checking for winget...
winget --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] winget found:
    winget --version
    set HAS_WINGET=1
) else (
    echo [WARN] winget not found
    echo winget is recommended for easier package management
    set HAS_WINGET=0
)
echo.

REM Install SSLyze
echo Installing SSLyze...
sslyze --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] SSLyze already installed:
    sslyze --version 2>&1 | findstr /r "SSLyze"
) else (
    echo Installing SSLyze via pip...
    pip install sslyze
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install SSLyze
        pause
        exit /b 1
    )
    echo [OK] SSLyze installed successfully
)
echo.

REM Verify SSLyze installation
echo Verifying SSLyze installation...
where sslyze >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] SSLyze found in PATH:
    where sslyze
) else (
    echo [WARN] SSLyze not found in PATH
    echo.
    echo Checking Python Scripts directory...
    set PYTHON_SCRIPTS=%APPDATA%\Python\Python311\Scripts
    if exist "%PYTHON_SCRIPTS%\sslyze.exe" (
        echo [OK] SSLyze found at: %PYTHON_SCRIPTS%\sslyze.exe
        echo.
        echo Adding to PATH...
        setx PATH "%PATH%;%PYTHON_SCRIPTS%"
        echo [OK] Added to PATH. Please restart your terminal.
    ) else (
        echo [ERROR] SSLyze executable not found
        echo Try running: pip install --user sslyze
    )
)
echo.

REM Create config directory
echo Setting up configuration directory...
set CONFIG_DIR=%USERPROFILE%\.config\ssltriage
if not exist "%CONFIG_DIR%" (
    mkdir "%CONFIG_DIR%"
    echo [OK] Created config directory: %CONFIG_DIR%
) else (
    echo [OK] Config directory exists: %CONFIG_DIR%
)
echo.

REM Test SSLyze
echo Testing SSLyze...
sslyze --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] SSLyze is working correctly
    sslyze --version 2>&1
) else (
    echo [WARN] SSLyze test failed
    echo You may need to restart your terminal for PATH changes to take effect
)
echo.

REM Print summary
echo ============================================
echo Installation Summary
echo ============================================
echo.
echo Extension file: SSLTriage.py
echo Config directory: %CONFIG_DIR%
echo.
echo Next steps:
echo   1. Open Burp Suite
echo   2. Go to Extensions ^> Extension Settings
echo   3. Set Python environment to Jython JAR
echo   4. Go to Extensions ^> Installed
echo   5. Click 'Add'
echo   6. Select 'Python' as extension type
echo   7. Select SSLTriage.py
echo   8. Click 'Next'
echo.
echo For detailed instructions, see README.md
echo.
echo Installation complete!
echo.
pause
