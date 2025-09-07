@echo off
REM Save the current directory
set SCRIPT_DIR=%~dp0

REM Create a temporary VBS script to run with admin rights without showing a console
echo Set UAC = CreateObject^("Shell.Application"^) > "%TEMP%\elevate.vbs"
echo UAC.ShellExecute "pythonw.exe", "%SCRIPT_DIR%GUI_Network_Monitor.py", "", "runas", 0 >> "%TEMP%\elevate.vbs"

REM Execute the VBS script
echo Starting Network Monitoring Tool with administrator privileges...
echo If you see a UAC prompt, please click "Yes" to continue.
echo The GUI will appear shortly, please wait...
cscript //nologo "%TEMP%\elevate.vbs"

REM Clean up
del "%TEMP%\elevate.vbs"

REM Keep the window open briefly
timeout /t 2 > nul
exit 