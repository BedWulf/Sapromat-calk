@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   СОПРОМАТ ОмГТУ: сборка ОДНОГО EXE (Win64)
echo ================================================
where python >nul 2>&1
if errorlevel 1 (
 echo Не найден Python. Установите Python 3.12 x64 и добавьте в PATH.
 pause
 exit /b 1
)
python -m venv .venv
if errorlevel 1 goto fail
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto fail
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python -m unittest discover -s tests -v
if errorlevel 1 goto fail
set PYTHONPATH=%CD%\tension
python -m unittest discover -s tension -p "test_*.py" -v
if errorlevel 1 goto fail
set PYTHONPATH=%CD%\torsion
python -m unittest discover -s torsion\tests -p "test_*.py" -v
if errorlevel 1 goto fail
set PYTHONPATH=

python -m PyInstaller --clean --noconfirm --onefile --windowed --name Sopromat_OMGTU ^
 --paths "%CD%\tension" --paths "%CD%\torsion" ^
 --add-data "teacher_templates;teacher_templates" ^
 --add-data "torsion\assets;torsion\assets" ^
 --add-data "tension\export\assets;tension\export\assets" ^
 --hidden-import "gui.main_window" ^
 --hidden-import "torsion_gui" ^
 --collect-submodules "core" ^
 --collect-submodules "gui" ^
 main.py
if errorlevel 1 goto fail
if not exist "dist\Sopromat_OMGTU.exe" goto fail
echo Выполняется проверка собранного приложения...
"dist\Sopromat_OMGTU.exe" --self-check
if errorlevel 1 goto fail
echo ================================================
echo SUCCESS: dist\Sopromat_OMGTU.exe
echo Переносить на рабочий ПК нужно ТОЛЬКО этот EXE.
echo ================================================
pause
exit /b 0
:fail
echo.
echo ОШИБКА СБОРКИ. Смотрите текст выше.
pause
exit /b 1
