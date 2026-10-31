@echo off
REM Full pipeline: PyInstaller build -> Inno Setup installer.
REM Requires Inno Setup 6 (https://jrsoftware.org/isdl.php)
call ".\scripts\build.bat" || exit /b 1

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo Inno Setup 6 not found. Install it from https://jrsoftware.org/isdl.php
  exit /b 1
)
%ISCC% installer\twinsight.iss || exit /b 1
echo.
echo Installer ready: installer_output\Twinsight-Setup-1.0.0.exe
