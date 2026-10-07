const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

function validateRequest(request, context) {
  const installer = path.resolve(request.installer);
  if (request.desktop_pid !== context.desktopPid) throw Error('Expired update request.');
  if (path.dirname(installer).toLowerCase() !== path.join(context.dataRoot, 'updates').toLowerCase() ||
      !/^Platinum-189-Setup-\d+\.\d+\.\d+\.exe$/.test(path.basename(installer))) {
    throw Error('Invalid update installer path.');
  }
  const hash = crypto.createHash('sha256').update(fs.readFileSync(installer)).digest('hex');
  if (!/^[a-f0-9]{64}$/.test(request.sha256) || hash !== request.sha256) {
    throw Error('Installer changed after verification. Download it again.');
  }
  return installer;
}

function createIndependentHelper(executable, args) {
  const command = [executable, ...args].map(value => '"' + String(value).replace(/"/g, '') + '"').join(' ');
  const escaped = command.replace(/'/g, "''");
  const powershell = "$startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0};" +
    "$created=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='" + escaped + "';ProcessStartupInformation=$startup};" +
    "$created|ConvertTo-Json -Compress;if($created.ReturnValue -ne 0){exit 1}";
  const result = spawnSync(executable, ['-NoProfile', '-NonInteractive', '-Command', powershell], { windowsHide:true, encoding:'utf8', timeout:15000 });
  if (result.error || result.status !== 0) throw Error(result.error?.message || result.stderr || 'Windows could not launch the updater.');
  const created = JSON.parse(result.stdout.trim());
  if (created.ReturnValue !== 0 || !Number.isInteger(created.ProcessId) || created.ProcessId <= 0) throw Error('Windows rejected the updater process.');
  return { pid:created.ProcessId, kill:()=>spawnSync('taskkill', ['/PID', String(created.ProcessId), '/F'], {windowsHide:true}) };
}

async function launchUpdate(request, context, createHelper = createIndependentHelper, timeoutMs = 10000) {
  const installer = validateRequest(request, context);
  const helper = path.join(context.dataRoot, 'install-update.ps1');
  // Keep the running helper outside the installation that it will replace.
  fs.copyFileSync(path.join(context.resourcesPath, 'install-update.ps1'), helper);
  const ready = path.join(context.dataRoot, `update-helper-${context.desktopPid}.json`);
  fs.rmSync(ready, { force: true });
  const child = createHelper(path.join(process.env.SystemRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'), [
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', helper,
    '-ProcessId', String(context.backendPid), '-DesktopProcessId', String(context.desktopPid),
    '-Installer', installer, '-App', context.appPath, '-DataRoot', context.dataRoot,
    '-ReadyFile', ready, '-ExpectedHash', request.sha256
  ]);
  try {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (fs.existsSync(ready)) {
        const ack = JSON.parse(fs.readFileSync(ready, 'utf8').replace(/^\uFEFF/, ''));
        if (ack.pid !== child.pid) throw Error('Invalid update helper acknowledgement.');
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw Error('Update helper did not confirm startup.');
  } catch (error) {
    child.kill();
    throw error;
  } finally {
    fs.rmSync(ready, { force: true });
  }
}

module.exports = { validateRequest, launchUpdate };
