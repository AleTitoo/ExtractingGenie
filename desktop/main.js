const { app, BrowserWindow, dialog, shell } = require('electron');
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { migrateLibrary } = require('./migration');

let backend;
let logFile;
let mainWindow;
const APP_ID = 'com.aletitoo.platinum189';
app.setAppUserModelId(APP_ID);
app.setName('Platinum-189');
const dataRoot = process.env.PLATINUM_DATA_DIR || process.env.GENIE_DATA_DIR || path.join(process.env.LOCALAPPDATA || os.homedir(), 'Platinum-189');
app.setPath('userData', dataRoot);
if (!app.requestSingleInstanceLock()) app.quit();
app.on('second-instance', () => {
  if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.focus(); }
});

app.disableHardwareAcceleration();

function log(message) {
  try {
    if (logFile) fs.appendFileSync(logFile, `${new Date().toISOString()} ${message}\n`);
  } catch {}
}

function stopBackend() {
  if (backend && !backend.killed && backend.exitCode === null) {
    if (process.platform === 'win32') spawnSync('taskkill', ['/PID', String(backend.pid), '/T', '/F'], { windowsHide: true });
    else backend.kill();
  }
  backend = null;
}

app.whenReady().then(() => {
  if (!process.env.PLATINUM_DATA_DIR && !process.env.GENIE_DATA_DIR) {
    migrateLibrary(path.join(process.env.LOCALAPPDATA || os.homedir(), 'GENIE Report Studio'), dataRoot);
  }
  fs.mkdirSync(dataRoot, { recursive: true });
  logFile = path.join(app.getPath('userData'), 'app.log');
  // Refresh legacy shortcut metadata once, preserving the shortcut paths used by pins.
  const marker = path.join(dataRoot, 'native-shortcuts-v2.json');
  if (app.isPackaged && !process.env.GENIE_SKIP_SHORTCUT_MIGRATION && !fs.existsSync(marker)) {
    const shortcuts = [
      path.join(app.getPath('appData'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Platinum-189', 'Platinum-189.lnk'),
      path.join(app.getPath('desktop'), 'Platinum-189.lnk')
    ];
    let migrated = true;
    for (const shortcut of shortcuts) {
      if (!fs.existsSync(shortcut)) continue;
      migrated = shell.writeShortcutLink(shortcut, 'update', {
        target: process.execPath, cwd: path.dirname(process.execPath),
        icon: path.join(process.resourcesPath, 'platinum-189-v2.ico'), iconIndex: 0,
        appUserModelId: APP_ID, description: 'Platinum-189'
      }) && migrated;
    }
    if (migrated) fs.writeFileSync(marker, JSON.stringify({ appId: APP_ID, version: app.getVersion() }));
  }
  const executable = path.join(process.resourcesPath, 'backend', 'Platinum-189.exe');
  log(`Starting backend: ${executable}`);
  const portFile = path.join(os.tmpdir(), `platinum-189-${process.pid}.txt`);
  try { fs.rmSync(portFile, { force: true }); } catch {}
  backend = spawn(executable, [], {
    windowsHide: true,
    env: {
      ...process.env,
      GENIE_EMBEDDED: '1',
      GENIE_DATA_DIR: app.getPath('userData'),
      GENIE_DESKTOP_EXE: process.execPath,
      GENIE_DESKTOP_PID: String(process.pid),
      GENIE_PORT_FILE: portFile
    }
  });

  let opened = false;
  const openWindow = url => {
    if (opened) return;
    opened = true;
    const window = new BrowserWindow({
      title: 'Platinum-189',
      icon: path.join(process.resourcesPath, 'platinum-189-v2.ico'),
      width: 1240,
      height: 820,
      minWidth: 900,
      minHeight: 620,
      backgroundColor: '#f4f7fb',
      autoHideMenuBar: true,
      webPreferences: { contextIsolation: true, sandbox: true, nodeIntegration: false }
    });
    mainWindow = window;
    window.setAppDetails({ appId: APP_ID, appIconPath: path.join(process.resourcesPath, 'platinum-189-v2.ico'), appIconIndex: 0, relaunchCommand: `"${process.execPath}"`, relaunchDisplayName: 'Platinum-189' });
    window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    window.webContents.on('will-navigate', (event, destination) => { if (!destination.startsWith(url + '/')) event.preventDefault(); });
    window.webContents.on('did-finish-load', async () => {
      if (!process.env.GENIE_SMOKE_FILE) return;
      try {
        const result = await window.webContents.executeJavaScript(`(async()=>{await reload();const info=await(await api('info')).json();$('version').textContent='Version '+info.version;return {version:info.version,reports:reports.length,title:document.title}})()`);
        await new Promise(resolve => setTimeout(resolve, 250));
        const screenshot = await window.webContents.capturePage();
        fs.writeFileSync(process.env.GENIE_SMOKE_FILE + '.png', screenshot.toPNG());
        const shortcut = path.join(app.getPath('appData'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Platinum-189', 'Platinum-189.lnk');
        const shortcutDetails = !process.env.GENIE_SKIP_SHORTCUT_MIGRATION && fs.existsSync(shortcut) ? shell.readShortcutLink(shortcut) : null;
        fs.writeFileSync(process.env.GENIE_SMOKE_FILE, JSON.stringify({ ...result, appId: APP_ID, executable: process.execPath, dataRoot, backend: executable, shortcutDetails }));
        app.quit();
      } catch (error) { log(error.stack); app.exit(1); }
    });
    window.loadURL(url);
  };

  const deadline = Date.now() + 30000;
  const poll = setInterval(() => {
    if (opened) return clearInterval(poll);
    if (Date.now() > deadline) {
      clearInterval(poll);
      dialog.showErrorBox('Platinum-189', 'The local report service did not start in time.');
      return app.quit();
    }
    try {
      const url = fs.readFileSync(portFile, 'utf8').trim();
      if (/^http:\/\/127\.0\.0\.1:\d+$/.test(url)) {
        fs.rmSync(portFile, { force: true });
        openWindow(url);
      }
    } catch {}
  }, 100);

  backend.on('error', error => {
    log(`Backend error: ${error.stack || error.message}`);
    dialog.showErrorBox('Platinum-189', `The local report service could not start.\n\n${error.message}`);
    app.quit();
  });

  backend.on('exit', code => {
    log(`Backend exited with code ${code}`);
    if (!app.isQuitting && code !== 0) {
      dialog.showErrorBox('Platinum-189', 'The local report service stopped unexpectedly.');
    }
    app.quit();
  });
}).catch(error => {
  log(`Startup error: ${error.stack || error.message}`);
  dialog.showErrorBox('Platinum-189', `The application could not start.\n\n${error.message}`);
  app.quit();
});

app.on('before-quit', () => {
  app.isQuitting = true;
  stopBackend();
});

app.on('window-all-closed', () => app.quit());
