@echo off
setlocal
if not "%~1"=="" set GIT_HOME=%~f1
if "%GIT_HOME%"=="" call :FindGitHome "git.cmd"

if exist "%GIT_HOME%" goto :GitHomeOK

echo MsysGit installation directory not found.>&2
echo Try to give the directory name on the command line:>&2
echo   %0 "%ProgramFiles%\Git"
endlocal
exit /B 1

:GitHomeOK
set ERR=0

set GETOPT_STATUS=Found
call :ChkGetopt getopt.exe || set GETOPT_STATUS=Not Found
echo getopt.exe... %GETOPT_STATUS%

if not exist "%GIT_HOME%\bin\git-flow" goto :Install
echo Uninstalling gitflow from "%GIT_HOME%"...>&2
set /p mychoice="Do you want to uninstall it [y/n]"
if "%mychoice%"=="y" goto :Uninstall
goto :Abort

:Uninstall
setlocal
echo Deleting old files...
::This is done in 2 for loops because I could not figure out how to get it to work with 1
::when there are spaces in the names
for /F "delims=" %%i in ('dir /b "%GIT_HOME%\bin\git-flow*"') do (
    call :UninstallFile %%i
)

for /F "delims=" %%i in ('dir /b "%GIT_HOME%\bin\gitflow-*"') do (
    call :UninstallFile %%i
)

call :UninstallFile getopt.exe || set ERR=1
call :UninstallFile libintl3.dll || set ERR=1
goto :End
:Install
echo Installing gitflow into "%GIT_HOME%"...>&2
echo Copying files...
::goto :EOF
if errorlevel 4 if not errorlevel 5 goto :AccessDenied
if errorlevel 1 set ERR=1
for /F "delims=" %%i in ('dir /b "..\git-flow*"') do (
    call :InstallFile ..\%%i || set ERR=1
)

for /F "delims=" %%i in ('dir /b "..\gitflow-*"') do (
    call :InstallFile ..\%%i || set ERR=1
)
call :InstallFile ..\shFlags\src\shflags gitflow-shflags || set ERR=1
if "%GETOPT_STATUS%" == "Not Found" (
  call :InstallFile ..\getopt.exe || set ERR=1
  call :InstallFile ..\libintl3.dll || set ERR=1
)

if %ERR%==1 choice /T 30 /C Y /D Y /M "Some unexpected errors happened. Sorry, you'll have to fix them by yourself."

:End
endlocal & exit /B %ERR%
goto :EOF

:AccessDenied
set ERR=1
echo.
echo You should run this script with "Full Administrator" rights:>&2
echo - Right-click with Shift on the script from the Explorer>&2
echo - Select "Run as administrator">&2
choice /T 30 /C YN /D Y /N >nul
goto :End

:Abort
echo Installation canceled.>&2
set ERR=1
goto :End

:ChkGetopt
:: %1 is getopt.exe
if exist "%GIT_HOME%\bin\%1" goto :EOF
if exist "%USERPROFILE%\bin\%1" goto :EOF
if exist "%~f$PATH:1" goto :EOF
exit /B 1

:InstallFile
::%1 is the input filename
::%2 is the output filename (if blank the input name is used)
for /F %%i in ("%~f1") do set OUTPUT_NAME=%%~ni%%~xi
if not "%2" == "" set OUTPUT_NAME=%2

::Create the file so we are not prompted if it is a file or dir
echo tmp > "%GIT_HOME%\bin\%OUTPUT_NAME%"
xcopy "%~dp0%1" "%GIT_HOME%\bin\%OUTPUT_NAME%" /Y /R /F || set ERR=1
exit /B %ERR%

:UninstallFile
::%1 is the filename
  if exist "%GIT_HOME%\bin\%1" (
    echo Removing "%GIT_HOME%\bin\%1"...
    del /F /Q "%GIT_HOME%\bin\%1" || set ERR=1
  )
exit /B %ERR%
:FindGitHome
setlocal
set GIT_CMD_DIR=%~dp$PATH:1
if "%GIT_CMD_DIR%"=="" endlocal & goto :EOF
endlocal & set GIT_HOME=%GIT_CMD_DIR:~0,-5%
goto :EOF