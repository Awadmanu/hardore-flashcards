@echo off
echo.
echo =============================================
echo   Flashcard Reviewer — Build para Windows
echo =============================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python desde https://python.org
    pause
    exit /b 1
)

:: Instalar dependencias
echo [1/3] Instalando dependencias...
pip install pyinstaller pillow --quiet
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

:: Buscar el script en la misma carpeta que este .bat
set SCRIPT=%~dp0claude_image_flashcards.py
if not exist "%SCRIPT%" (
    echo [ERROR] No se encontro claude_flashcards_v2.py en la misma carpeta.
    echo         Pon build_windows.bat y claude_flashcards_v2.py juntos.
    pause
    exit /b 1
)

:: Buscar icono (icon.ico en la misma carpeta, opcional)
set ICON_FLAG=
if exist "%~dp0icon.ico" (
    set ICON_FLAG=--icon "%~dp0icon.ico"
    echo    Icono encontrado: icon.ico
) else (
    echo    Sin icono personalizado ^(opcional^).
    echo    Para usar uno: python make_icon.py tu_imagen.png -o icon.ico
)

:: Compilar
echo [2/3] Compilando .exe (puede tardar un minuto)...
pyinstaller --onefile --windowed --name "Flashcard Reviewer" %ICON_FLAG% --distpath "%~dp0dist" --workpath "%~dp0build" --specpath "%~dp0build" "%SCRIPT%"
if errorlevel 1 (
    echo [ERROR] Fallo al compilar.
    pause
    exit /b 1
)

:: Limpiar archivos temporales
echo [3/3] Limpiando archivos temporales...
rmdir /s /q "%~dp0build" >nul 2>&1

echo.
echo =============================================
echo   Listo! El ejecutable esta en:
echo   %~dp0dist\Flashcard Reviewer.exe
echo =============================================
echo.
echo Puedes copiar ese .exe donde quieras y ejecutarlo con doble clic.
echo Recuerda mantener la carpeta _media/ junto a tus CSVs.
echo.
pause