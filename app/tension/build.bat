@echo off
chcp 65001 >nul
echo ============================================
echo Компиляция приложения в exe
echo ============================================
echo.

echo [1/3] Проверка зависимостей...
pip install PyQt6 matplotlib numpy python-docx pyinstaller --quiet

echo [2/3] Компиляция...
pyinstaller --onefile --windowed --name "Raschet_Sterzhnya" --clean --add-data "export\assets\teacher_title_template.docx;export\assets" main.py

echo.
echo [3/3] Готово!
echo exe файл находится в папке: dist\Raschet_Sterzhnya.exe
echo.
pause