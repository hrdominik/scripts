@echo off
set javaVersionArg=%1
set "params=%*"
cd /d "%~dp0" && ( if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs" ) && fsutil dirty query %systemdrive% 1>nul 2>nul || (  echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && exit /B )

echo ### Switching OpenJDK System-wide ###
set java8=C:\Program Files\RedHat\java-1.8.0-openjdk-1.8.0.352-2
set java17=C:\Program Files\RedHat\java-17-openjdk-17.0.5.0.8-2
set java9=C:\Program Files\RedHat\java-1.8.0-openjdk-1.8.0.352-2

echo ### before:
echo %JAVA_HOME%
java -version
echo.
REM set JAVA_HOME "%java8%" && 
IF "%javaVersionArg%" == "" setx JAVA_HOME "%java8%" /m && echo ### changed to: && echo %java8%
if "%javaVersionArg%"=="java8" setx JAVA_HOME "%java8%" /m && echo ### changed to: && echo %java8%
if "%javaVersionArg%"=="java17" setx JAVA_HOME "%java17%" /m && echo ### changed to: && echo %java17%
if "%javaVersionArg%"=="java9" setx JAVA_HOME "%java9%" /m && echo ### changed to: && echo %java9%
::set Path=%JAVA_HOME%\bin;%Path%

timeout 3 >nul