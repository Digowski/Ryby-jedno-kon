@echo off
:: Przejdź do folderu, w którym znajduje się ten plik .bat
cd /d "%~dp0"

:: Uruchom bota
python main.py

pause