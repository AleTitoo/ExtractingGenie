const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { validateRequest, launchUpdate } = require('../desktop/updater');

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pt189-updater-'));
  fs.mkdirSync(path.join(root, 'updates'));
  fs.mkdirSync(path.join(root, 'resources'));
  fs.writeFileSync(path.join(root, 'resources', 'install-update.ps1'), 'trusted helper');
  const installer = path.join(root, 'updates', 'Platinum-189-Setup-9.0.0.exe');
  fs.writeFileSync(installer, 'installer');
  return {
    request: { installer, desktop_pid:1234, sha256:crypto.createHash('sha256').update('installer').digest('hex') },
    context: { dataRoot:root, resourcesPath:path.join(root, 'resources'), desktopPid:1234, backendPid:5678, appPath:path.join(root, 'app.exe') },
    cleanup:()=>fs.rmSync(root,{recursive:true,force:true})
  };
}

test('refuses a modified installer, an outside path, and a stale request before launching', () => {
  const f = fixture();
  try {
    assert.equal(validateRequest(f.request,f.context),f.request.installer);
    assert.throws(()=>validateRequest({...f.request,desktop_pid:1},f.context),/Expired/);
    assert.throws(()=>validateRequest({...f.request,installer:path.join(f.context.dataRoot,'outside.exe')},f.context),/path/);
    fs.writeFileSync(f.request.installer,'changed');
    assert.throws(()=>validateRequest(f.request,f.context),/changed/);
  } finally { f.cleanup(); }
});

test('does not complete handoff until the independent helper acknowledges startup', async () => {
  const f = fixture();
  try {
    let stopped = false;
    await launchUpdate(f.request,f.context,(exe,args)=>{
      assert.equal(args[args.indexOf('-DataRoot')+1],f.context.dataRoot);
      const ready=args[args.indexOf('-ReadyFile')+1];
      setTimeout(()=>fs.writeFileSync(ready,JSON.stringify({pid:9999})),30);
      return {pid:9999,kill:()=>{stopped=true}};
    },1000);
    assert.equal(stopped,false);
    assert.equal(fs.existsSync(path.join(f.context.dataRoot,'update-helper-1234.json')),false);
  } finally { f.cleanup(); }
});

test('failed helper startup rejects handoff so the caller keeps the app open', async () => {
  const f = fixture();
  try {
    let stopped=false;
    await assert.rejects(launchUpdate(f.request,f.context,()=>({pid:9999,kill:()=>{stopped=true}}),20),/did not confirm/);
    assert.equal(stopped,true);
  } finally { f.cleanup(); }
});
