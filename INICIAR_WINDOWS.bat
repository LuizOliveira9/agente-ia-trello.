@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Erro: instale Python 3.10 ou superior e tente novamente.
    pause
    exit /b 1
  )
)
echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha na instalacao. Confira sua conexao com a internet.
  pause
  exit /b 1
)
if not exist "agenttaskmanager\.env" (
  copy "agenttaskmanager\.env.exemplo" "agenttaskmanager\.env" >nul
  echo Configure suas chaves no bloco de notas. NUNCA envie esse arquivo ao GitHub.
  notepad "agenttaskmanager\.env"
)
echo Iniciando Google ADK Web...
".venv\Scripts\adk.exe" web
pause
