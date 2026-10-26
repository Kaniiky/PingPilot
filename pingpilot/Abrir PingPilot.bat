@echo off
cd /d "%~dp0"
python -c "import webview" 2>nul || (
  echo Instalando a dependencia pywebview...
  python -m pip install --disable-pip-version-check -q pywebview
)
start "" pythonw "%~dp0app.py"
