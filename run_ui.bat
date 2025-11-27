@echo off
REM --- Este script lanca a UI sem erros de parsing. ---

set PYTHON_EXE="C:/Users/duart/AppData/Local/Programs/Python/Python313/python.exe"
set APP_FILE="app_ui.py"

echo. ^>^>^> Iniciando a aplicacao Streamlit...
%PYTHON_EXE% -m streamlit run %APP_FILE%

echo. Aplicacao lancada. Use Ctrl+C para parar no terminal.