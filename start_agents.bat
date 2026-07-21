@echo off
REM start_agents.bat - Windows launcher for the agentic AI system
REM This opens 3 separate terminal windows for each service.
REM Make sure Ollama is running first: ollama serve

echo ============================================
echo  Starting Agentic AI System (Windows)
echo ============================================
echo.
echo Prerequisites:
echo   - Ollama must be running (ollama serve)
echo   - Virtual environment at .venv\
echo.

SET VENV=%~dp0.venv\Scripts\python.exe
SET SRC=%~dp0src

echo [1/3] Starting MCP Server (port 8000)...
start "MCP Server" cmd /k "%VENV% %SRC%\mcp_server.py"

echo Waiting 5 seconds for MCP server to start...
timeout /t 5 /nobreak >nul

echo [2/3] Starting Agent Server (port 9991)...
start "Agent Server" cmd /k "%VENV% %SRC%\a2a_1_starlette.py"

echo Waiting 5 seconds for Agent server to start...
timeout /t 5 /nobreak >nul

echo [3/3] Starting Orchestrator Server (port 9990)...
start "Orchestrator Server" cmd /k "%VENV% %SRC%\orchestrator\o1_server.py"

echo Waiting 5 seconds for Orchestrator to start...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo  All services started!
echo ============================================
echo.
echo  MCP Server:          http://localhost:8000
echo  Research Agent:       http://localhost:9991
echo  Orchestrator Agent:   http://localhost:9990
echo.
echo  To interact, run:
echo    .venv\Scripts\python.exe src\client.py
echo.
echo  To stop: close each terminal window.
echo ============================================
pause
