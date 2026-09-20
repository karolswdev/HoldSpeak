const { app, BrowserWindow, session } = require('electron');
const { mkdirSync, writeFileSync } = require('node:fs');
const { resolve, join } = require('node:path');
const out = process.env.PHILO_PROBE_OUT;
if (!out || !require('node:path').isAbsolute(out)) throw new Error('PHILO_PROBE_OUT must be an absolute temporary directory');
mkdirSync(out, { recursive: true });
app.setPath('userData', join(out, 'profile'));
app.setPath('sessionData', join(out, 'session'));
const origin = 'http://127.0.0.1:18789';
app.whenReady().then(async () => {
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
    const url = new URL(details.url);
    callback({ cancel: !['data:', 'blob:'].includes(url.protocol) && url.origin !== origin });
  });
  const started = performance.now();
  const win = new BrowserWindow({ show: false, width: 1440, height: 900,
    webPreferences: { preload: join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true } });
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, url) => { if (new URL(url).origin !== origin) event.preventDefault(); });
  await win.loadURL(origin);
  await new Promise(r => setTimeout(r, 2500));
  const evidence = await win.webContents.executeJavaScript(`({title:document.title, text:document.body.innerText.slice(0,1000),nodeAvailable:typeof process!=='undefined'||typeof require!=='undefined',host:window.desktopHost})`);
  evidence.loadAndSettleMs = performance.now() - started;
  evidence.versions = process.versions;
  evidence.scope = 'Static production bundle; no hub or user data; timing includes 2500ms settle, not startup benchmark';
  for (const width of [1440,393]) {
    win.setContentSize(width, 900);
    await new Promise(r=>setTimeout(r,300));
    writeFileSync(join(out, `electron-${width}.png`),(await win.webContents.capturePage()).toPNG());
  }
  writeFileSync(join(out,'electron-probe.json'),JSON.stringify(evidence,null,2));
  console.log(JSON.stringify(evidence));
  if(evidence.nodeAvailable) throw new Error('Renderer has Node globals');
  win.destroy(); app.quit();
}).catch(error => {console.error(error); app.exit(1);});
