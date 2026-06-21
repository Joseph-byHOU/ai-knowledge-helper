const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // 数据
  readLocal: () => ipcRenderer.invoke('news:read-local'),
  listReports: () => ipcRenderer.invoke('news:list-reports'),
  readReport: (name) => ipcRenderer.invoke('news:read-report', name),

  // 采集 / 生成
  collect: () => ipcRenderer.invoke('news:collect'),
  quickFetch: () => ipcRenderer.invoke('news:quick-fetch'),
  generateReport: (dateStr) => ipcRenderer.invoke('news:generate-report', dateStr),

  // 智能搜索
  searchLocal: (q) => ipcRenderer.invoke('news:search-local', q),
  fetchByKeyword: (q) => ipcRenderer.invoke('news:fetch-by-keyword', q),

  // 右键菜单 + 原文 + 解读
  cardContextMenu: (info) => ipcRenderer.invoke('card:context-menu', info),
  cardFetchOriginal: (url) => ipcRenderer.invoke('card:fetch-original', url),
  cardInterpret: (info) => ipcRenderer.invoke('card:interpret', info),

  // 系统
  openExternal: (url) => ipcRenderer.invoke('app:open-external', url),
  showInFolder: (fp) => ipcRenderer.invoke('app:show-in-folder', fp),
  getInfo: () => ipcRenderer.invoke('app:get-info'),

  // 配置
  readConfig: () => ipcRenderer.invoke('config:read'),
  writeConfig: (cfg) => ipcRenderer.invoke('config:write', cfg),

  // 日志订阅
  onLog: (cb) => ipcRenderer.on('news:log', (_e, chunk) => cb(chunk)),
  offLog: () => ipcRenderer.removeAllListeners('news:log')
});
