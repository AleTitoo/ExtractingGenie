param(
    [Parameter(Mandatory=$true)][int]$ProcessId,
    [Parameter(Mandatory=$true)][int]$DesktopProcessId,
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$App,
    [Parameter(Mandatory=$true)][string]$DataRoot,
    [Parameter(Mandatory=$true)][string]$ReadyFile,
    [Parameter(Mandatory=$true)][string]$ExpectedHash
)
$ErrorActionPreference = 'Stop'
$log = Join-Path $DataRoot 'update-install.log'
$resultFile = Join-Path $DataRoot 'update-install-result.json'
function Write-Outcome($value) {
    $json = $value | ConvertTo-Json -Compress
    [IO.File]::WriteAllText($resultFile + '.tmp', $json)
    Move-Item -LiteralPath ($resultFile + '.tmp') -Destination $resultFile -Force
}
try {
    if ((Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash -ne $ExpectedHash) {
        throw 'Installer checksum changed. Download the update again.'
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) Helper ready; waiting for app shutdown."
    [IO.File]::WriteAllText($ReadyFile + '.tmp', (@{pid=$PID} | ConvertTo-Json -Compress))
    Move-Item -LiteralPath ($ReadyFile + '.tmp') -Destination $ReadyFile -Force
    Wait-Process -Id $DesktopProcessId -Timeout 120 -ErrorAction SilentlyContinue
    if (Get-Process -Id $DesktopProcessId -ErrorAction SilentlyContinue) { throw 'The app did not close.' }
    Wait-Process -Id $ProcessId -Timeout 30 -ErrorAction SilentlyContinue
    if (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) { throw 'The report service did not close.' }
    $setup = Start-Process -FilePath $Installer -ArgumentList '/S' -WindowStyle Hidden -PassThru -Wait
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) Installer exit: $($setup.ExitCode)"
    if ($setup.ExitCode -ne 0) { throw "Installer failed (exit $($setup.ExitCode))." }
    # The new app must use its own fresh backend and window, not inherited test/update state.
    Get-ChildItem Env:GENIE_* -ErrorAction SilentlyContinue | Remove-Item
    Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
    Start-Process -FilePath $App -WindowStyle Normal
    Write-Outcome @{installed=$true;error=$null}
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) Application relaunched."
} catch {
    $message = $_.Exception.Message
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) Update error: $message"
    Write-Outcome @{installed=$false;error=$message}
    # On failure after shutdown, restore the existing app when its files are intact.
    if (!(Get-Process -Id $DesktopProcessId -ErrorAction SilentlyContinue) -and
        (Test-Path -LiteralPath $App) -and
        !(Test-Path -LiteralPath (Join-Path (Split-Path $App) '.installing'))) {
        Get-ChildItem Env:GENIE_* -ErrorAction SilentlyContinue | Remove-Item
        Start-Process -FilePath $App -WindowStyle Normal
    }
    exit 1
}
