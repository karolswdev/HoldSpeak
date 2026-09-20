const { contextBridge } = require('electron');
// A read-only capability probe; no generic IPC, filesystem, shell or secrets.
contextBridge.exposeInMainWorld('desktopHost', Object.freeze({
  kind: 'electron',
  capabilities: Object.freeze({ files: false, shortcuts: false, tray: false, notifications: false }),
}));
