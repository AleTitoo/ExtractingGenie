// Run with Electron to rasterize the approved vector without losing transparency.
const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('force-device-scale-factor', '1');
app.whenReady().then(async () => {
  const root = path.resolve(__dirname, '..');
  const name = process.argv.includes('--offline') ? 'platinum-189-offline' : 'platinum-189';
  const svg = fs.readFileSync(path.join(root, 'assets', name + '.svg'), 'utf8');
  const win = new BrowserWindow({width:1024,height:1024,useContentSize:true,show:false,transparent:true,backgroundColor:'#00000000',webPreferences:{offscreen:true,contextIsolation:true,nodeIntegration:false}});
  await win.loadURL('data:text/html;charset=utf-8,'+encodeURIComponent('<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}svg{display:block;width:100%;height:100%}</style>'+svg));
  await win.webContents.executeJavaScript('document.fonts.ready.then(()=>true)');
  await new Promise(resolve=>setTimeout(resolve,150));
  const image = await win.webContents.capturePage();
  fs.writeFileSync(path.join(root,'assets',name + '-source.png'), image.resize({width:1024,height:1024}).toPNG());
  app.quit();
}).catch(error=>{process.stderr.write(error.stack);app.exit(1);});
