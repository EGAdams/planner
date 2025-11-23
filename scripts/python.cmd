@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."

rem Resolve preferred Python interpreter
if exist "%REPO_ROOT%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
) else if defined PYTHON_FOR_PLANNER (
    set "PYTHON_EXE=%PYTHON_FOR_PLANNER%"
) else (
    for %%P in (python.exe python3.exe) do (
        for /f "delims=" %%I in ('where %%P 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
        if defined PYTHON_EXE goto :after_python_search
    )
    for /f "delims=" %%I in ('where py.exe 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
)

:after_python_search
if not defined PYTHON_EXE (
    echo [scripts/python] Unable to locate a Python interpreter. 1>&2
    echo Install Python or point PYTHON_FOR_PLANNER at the interpreter you want to use. 1>&2
    exit /b 1
)

set "SCRIPT_PATH=%~1"
if "%SCRIPT_PATH%"=="" (
    "%PYTHON_EXE%"
    exit /b %errorlevel%
)

shift

if not exist "%SCRIPT_PATH%" (
    if exist "%SCRIPT_DIR%%SCRIPT_PATH%" (
        set "SCRIPT_PATH=%SCRIPT_DIR%%SCRIPT_PATH%"
    ) else if exist "%REPO_ROOT%\%SCRIPT_PATH%" (
        set "SCRIPT_PATH=%REPO_ROOT%\%SCRIPT_PATH%"
    )
)

if not exist "%SCRIPT_PATH%" (
    echo [scripts/python] Unable to find "%~1" or "%SCRIPT_PATH%". 1>&2
    exit /b 1
)

set "FORWARDED_ARGS="
:collect_args
if "%~1"=="" goto run_python
if defined FORWARDED_ARGS (
    set "FORWARDED_ARGS=%FORWARDED_ARGS% ""%~1"""
) else (
    set "FORWARDED_ARGS=""%~1"""
)
shift
goto collect_args

:run_python
if defined FORWARDED_ARGS (
    call "%PYTHON_EXE%" "%SCRIPT_PATH%" %FORWARDED_ARGS%
) else (
    "%PYTHON_EXE%" "%SCRIPT_PATH%"
)
exit /b %errorlevel%
