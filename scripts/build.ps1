$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$python = if (Test-Path '.build-venv\Scripts\python.exe') { '.build-venv\Scripts\python.exe' } else { 'python' }
$version = (Get-Content -LiteralPath 'version.txt' -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw "Invalid version: $version" }
if ($env:GITHUB_REF_TYPE -eq 'tag' -and $env:GITHUB_REF_NAME -ne "v$version") { throw "Tag $($env:GITHUB_REF_NAME) does not match version v$version." }
$env:PYTHONPATH = (Join-Path $root 'app')
& $python scripts\sync_version.py
if ($LASTEXITCODE -ne 0) { throw 'Version synchronization failed.' }
& $python scripts\make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }
& $python -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $python -m PyInstaller --clean --noconfirm GENIE-Report-Studio.spec --distpath backend-dist
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
node --check desktop/main.js
if ($LASTEXITCODE -ne 0) { throw 'Desktop shell syntax check failed.' }
$env:CSC_IDENTITY_AUTO_DISCOVERY = 'false'
node node_modules/electron-builder/cli.js --win --dir --publish never
if ($LASTEXITCODE -ne 0) { throw 'Native desktop packaging failed.' }
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
    if (Test-Path $cache) {
        $makensis = (Get-ChildItem -LiteralPath $cache -Recurse -Filter makensis.exe -File -ErrorAction SilentlyContinue |
            Select-Object -First 1).FullName
    }
}
if (-not $makensis) { throw 'makensis.exe is required to build the installer.' }
New-Item -ItemType Directory -Force -Path 'dist' | Out-Null
& $makensis "/DAPP_VERSION=$version" installer.nsi
if ($LASTEXITCODE -ne 0) { throw 'NSIS installer build failed.' }
$installerName = "GENIE-Report-Studio-Setup-$version.exe"
$installer = Join-Path 'dist' $installerName
$hash = (Get-FileHash -Algorithm SHA256 $installer).Hash.ToLowerInvariant()
Set-Content -LiteralPath ($installer + '.sha256') -Value "$hash  $installerName" -Encoding ascii
Copy-Item -LiteralPath $installer -Destination 'dist\GENIE-Report-Studio-Setup-latest.exe' -Force
Set-Content -LiteralPath 'dist\GENIE-Report-Studio-Setup-latest.exe.sha256' -Value "$hash  GENIE-Report-Studio-Setup-latest.exe" -Encoding ascii
