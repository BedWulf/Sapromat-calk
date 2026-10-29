@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul
set "VENV=.torsion_build_env"
set "EXENAME=Raschet_Krucheniya"
echo =========================================
echo  КРУЧЕНИЕ: СБОРКА ОДНОГО EXE ДЛЯ WINDOWS
 echo =========================================
echo.
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  py -3.12 -m venv "%VENV%" 2>nul
)
if not exist "%VENV%\Scripts\python.exe" (
  python -m venv "%VENV%"
)
if not exist "%VENV%\Scripts\python.exe" (
  echo ERROR: Python 3.12 64-bit is required on the build computer.
  pause
  exit /b 1
)
set "PY=%VENV%\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto fail
"%PY%" -m pip install -r requirements.txt "pyinstaller>=6.10,<7"
if errorlevel 1 goto fail
"%PY%" -m unittest discover -s tests -v
if errorlevel 1 goto fail
"%PY%" -m PyInstaller --clean --noconfirm --onefile --windowed --name "%EXENAME%" --hidden-import=matplotlib.backends.backend_agg --hidden-import=PIL.ImageTk --add-data "assets;assets" main.py
if errorlevel 1 goto fail
if not exist "dist\%EXENAME%.exe" goto fail
echo.
echo Running packaged EXE self-check...
start "" /wait "dist\%EXENAME%.exe" --self-check "%CD%\dist\selfcheck.txt"
if errorlevel 1 goto fail
findstr /c:"SUCCESS:" "dist\selfcheck.txt" >nul
if errorlevel 1 goto fail
echo.
echo ===================== SUCCESS =====================
echo COPY ONLY THIS FILE TO THE OFFLINE WORK COMPUTER:
echo %CD%\dist\%EXENAME%.exe
echo Windows 10/11 x64. No Python/Internet required there.
echo ===================================================
pause
exit /b 0
:fail
echo.
echo !!! FAILED. DO NOT TRANSFER A NON-VERIFIED EXE !!!
if exist "dist\selfcheck.txt" type "dist\selfcheck.txt"
pause
exit /b 1
