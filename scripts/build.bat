@echo off
REM Windows build: creates venv, installs deps, builds dist\Twinsight\Twinsight.exe
python -m venv .venv || exit /b 1
call .venv\Scripts\activate.bat
pip install -r requirements-dev.txt || exit /b 1
python tools\make_icon.py
pyinstaller twinsight.spec --noconfirm --clean || exit /b 1
echo.
echo Done: dist\Twinsight\Twinsight.exe
