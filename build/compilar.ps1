# Compila o PingPilot para Windows e monta o pacote de lançamento em compilado\
#   powershell -ExecutionPolicy Bypass -File build\compilar.ps1
#   (opção -SkipWindowTest pula o teste que abre a janela por ~20 s)
#
# Ordem: bateria de segurança -> teste da janela real -> PyInstaller -> pacote -> conferência do pacote.
# Se qualquer etapa falhar, nada é publicado.
param([switch]$SkipWindowTest)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$src = Join-Path $root 'pingpilot'
$out = Join-Path $root 'compilado'
$version = (Select-String -Path (Join-Path $src 'app.py') -Pattern '^VERSION = "(.+)"').Matches[0].Groups[1].Value

Write-Host "== PingPilot ${version}: bateria de seguranca"
python (Join-Path $root 'security\check.py')
if ($LASTEXITCODE) { throw 'A bateria de seguranca falhou. Corrija antes de compilar.' }

if (-not $SkipWindowTest) {
    Write-Host '== Teste da janela real (abre por ~20 s)'
    python (Join-Path $PSScriptRoot 'test_window.py')
    if ($LASTEXITCODE) { throw 'O teste da janela falhou.' }
}

Write-Host '== Compilando (janela, pede administrador)'
$common = @('--noconfirm', '--clean', '--onefile',
    '--icon', (Join-Path $PSScriptRoot 'pingpilot.ico'),
    '--version-file', (Join-Path $PSScriptRoot 'version_info.txt'),
    '--add-data', "$src\ui;ui", '--add-data', "$src\upstream.json;.", '--paths', $src, '--hidden-import', 'pystray._win32',
    # o Pillow (usado só para o ícone da bandeja) puxa o numpy e outros pacotes grandes sem precisar
    '--exclude-module', 'numpy', '--exclude-module', 'tkinter', '--exclude-module', 'PIL.ImageQt',
    '--exclude-module', 'PIL.ImageTk', '--exclude-module', 'matplotlib', '--exclude-module', 'IPython',
    '--workpath', (Join-Path $PSScriptRoot 'work'), '--specpath', $PSScriptRoot)
Remove-Item (Join-Path $out 'windows') -Recurse -Force -ErrorAction SilentlyContinue
python -m PyInstaller @common --windowed --uac-admin --name PingPilot --distpath (Join-Path $out 'windows') (Join-Path $src 'app.py')
if ($LASTEXITCODE) { throw 'PyInstaller falhou' }

Write-Host '== Montando o pacote'
Copy-Item (Join-Path $PSScriptRoot 'README-release.txt') (Join-Path $out 'windows\README.txt') -Force
Copy-Item (Join-Path $root 'LICENSE') (Join-Path $out 'windows\LICENSE.txt') -Force
Copy-Item (Join-Path $root 'CREDITS.md') (Join-Path $out 'windows\CREDITS.md') -Force
$zip = Join-Path $out "PingPilot-$version-windows.zip"
Compress-Archive -Path (Join-Path $out 'windows\*') -DestinationPath $zip -Force
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
"$hash  PingPilot-$version-windows.zip" | Set-Content -Encoding ascii (Join-Path $out "PingPilot-$version-windows.zip.sha256")

Write-Host '== Conferindo o pacote'
python (Join-Path $root 'security\check.py') --only package
if ($LASTEXITCODE) { throw 'O pacote contem arquivos que nao deveria.' }

Get-ChildItem $out -File | Select-Object Name, @{n='Tamanho'; e={'{0:N1} MB' -f ($_.Length / 1MB)}} | Format-Table -AutoSize
Write-Host "SHA-256: $hash"
