$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$python = if (Test-Path '.build-venv\Scripts\python.exe') { '.build-venv\Scripts\python.exe' } else { 'python' }
$version = (Get-Content version.txt -Raw).Trim()
New-Item -ItemType Directory -Force -Path build | Out-Null
Set-Content -LiteralPath 'build/offline-edition.json' -Value '{"edition":"offline"}' -Encoding ascii
& $python -m PyInstaller --clean --noconfirm Platinum-189-offline.spec --distpath backend-offline
if ($LASTEXITCODE -ne 0) { throw 'Offline backend build failed.' }
node scripts/offline-config.js
if ($LASTEXITCODE -ne 0) { throw 'Offline packaging configuration failed.' }
$env:CSC_IDENTITY_AUTO_DISCOVERY = 'false'
node node_modules/electron-builder/cli.js --config build/offline-package.json --win --dir --publish never
if ($LASTEXITCODE -ne 0) { throw 'Offline desktop packaging failed.' }
$makensis = (Get-Command makensis.exe -ErrorAction SilentlyContinue).Source
if (-not $makensis) {
    $candidates = @()
    if (${env:ProgramFiles(x86)}) { $candidates += Join-Path ${env:ProgramFiles(x86)} 'NSIS\makensis.exe' }
    if ($env:ProgramFiles) { $candidates += Join-Path $env:ProgramFiles 'NSIS\makensis.exe' }
    if ($env:ChocolateyInstall) { $candidates += Join-Path $env:ChocolateyInstall 'bin\makensis.exe' }
    $makensis = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $makensis) {
    $cache = Join-Path $env:LOCALAPPDATA 'electron-builder\Cache'
    if (Test-Path $cache) { $makensis = (Get-ChildItem -LiteralPath $cache -Recurse -Filter makensis.exe -File | Select-Object -First 1).FullName }
}
if (-not $makensis) { throw 'NSIS compiler unavailable.' }
& $makensis "/DAPP_VERSION=$version" installer-offline.nsi
if ($LASTEXITCODE -ne 0) { throw 'Offline installer build failed.' }
$name = "Platinum-189-Offline-Setup-$version.exe"
$file = Join-Path dist $name
$hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath ($file + '.sha256') -Value "$hash  $name" -Encoding ascii
Copy-Item -LiteralPath $file -Destination 'dist/Platinum-189-Offline-Setup-latest.exe' -Force
Set-Content -LiteralPath 'dist/Platinum-189-Offline-Setup-latest.exe.sha256' -Value "$hash  Platinum-189-Offline-Setup-latest.exe" -Encoding ascii
