param([Parameter(Mandatory=$true)][string]$InstallDir)
$ErrorActionPreference = 'Stop'
$resolvedInstall = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
$expectedInstall = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\Platinum-189')).TrimEnd('\')
if ($resolvedInstall -ne $expectedInstall) { throw 'Unexpected application installation directory.' }
$mainExe = Join-Path $resolvedInstall 'Platinum-189.exe'
$backendExe = Join-Path $resolvedInstall 'resources\backend\Platinum-189.exe'
function Get-InstalledProcesses {
    # NSIS is 32-bit; CIM can identify 64-bit executable paths reliably.
    Get-CimInstance Win32_Process -Filter "Name='Platinum-189.exe'" | Where-Object { $_.ExecutablePath -eq $mainExe -or $_.ExecutablePath -eq $backendExe }
}
Get-InstalledProcesses | Where-Object { $_.ExecutablePath -eq $mainExe } | ForEach-Object {
    $application = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
    if ($application -and $application.MainWindowHandle -ne 0) { [void]$application.CloseMainWindow() }
}
$deadline = (Get-Date).AddSeconds(8)
while ((Get-InstalledProcesses) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 200 }
Get-InstalledProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
$deadline = (Get-Date).AddSeconds(4)
while ((Get-InstalledProcesses) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 200 }
if (Get-InstalledProcesses) { throw 'Platinum-189 could not close. Close it and run the installer again.' }
