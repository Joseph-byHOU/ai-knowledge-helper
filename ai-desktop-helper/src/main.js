const { app, BrowserWindow, ipcMain, shell, dialog, Menu, net } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

// ====== 常量 ======
const APP_DIR = path.resolve(__dirname, '..');
const SKILL_DIR = path.join(APP_DIR, 'my-ai-daily-news');
const SCRIPTS_DIR = path.join(SKILL_DIR, 'scripts');
const DATA_DIR = path.join(SKILL_DIR, 'data');
const REPORTS_DIR = path.join(SKILL_DIR, 'reports');
const DATA_FILE = path.join(DATA_DIR, 'daily_news.json');
const APP_CONFIG_FILE = path.join(__dirname, 'config.json');

const VENV_PY_UNIX = path.join(APP_DIR, 'python-runtime', 'bin', 'python');
const VENV_PY_WIN = path.join(APP_DIR, 'python-runtime', 'Scripts', 'python.exe');

// ====== 工具函数 ======

function resolvePython() {
  if (process.platform === 'win32' && fs.existsSync(VENV_PY_WIN)) return VENV_PY_WIN;
  if (fs.existsSync(VENV_PY_UNIX)) return VENV_PY_UNIX;
  return process.platform === 'win32' ? 'python' : 'python3';
}

function ensureSkillConfig() {
  try {
    const cfg = path.join(SKILL_DIR, 'config.json');
    if (fs.existsSync(cfg)) return;
    const example = path.join(SKILL_DIR, 'references', 'config.example.json');
    if (fs.existsSync(example)) {
      fs.copyFileSync(example, cfg);
      console.log('[bootstrap] config.json created from example');
    }
  } catch (e) {
    console.warn('[bootstrap] ensureSkillConfig 失败:', e.message);
  }
}

function ensureDataDirs() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.mkdirSync(REPORTS_DIR, { recursive: true });
}

// ====== 流式子进程 ======
function runPython(scriptName, args = []) {
  return new Promise((resolve) => {
    const scriptPath = path.join(SCRIPTS_DIR, scriptName);
    if (!fs.existsSync(scriptPath)) {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('news:log', `[!] 脚本不存在: ${scriptPath}\n`);
      }
      return resolve({ ok: false, code: -1, error: 'script-not-found' });
    }
    ensureDataDirs();

    const py = resolvePython();
    const child = spawn(py, [scriptPath, ...args], {
      cwd: SKILL_DIR,
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8',
        PYTHONHOME: undefined
      },
      windowsHide: true
    });

    let stdoutBuf = '';
    let stderrBuf = '';

    child.stdout.on('data', (d) => {
      const text = d.toString();
      stdoutBuf += text;
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('news:log', text);
      }
    });
    child.stderr.on('data', (d) => {
      const text = d.toString();
      stderrBuf += text;
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('news:log', text);
      }
    });
    child.on('error', (err) => {
      const msg = `[!] 进程错误: ${err.message}\n`;
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('news:log', msg);
      }
      resolve({ ok: false, code: -1, error: err.message, stdout: stdoutBuf, stderr: stderrBuf });
    });
    child.on('close', (code) => {
      const msg = `\n[exit ${code}]\n`;
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('news:log', msg);
      }
      resolve({ ok: code === 0, code, stdout: stdoutBuf, stderr: stderrBuf });
    });
  });
}

// ====== 智能搜索 ======
function tokenize(q) {
  return String(q || '')
    .toLowerCase()
    .split(/[\s,，。;；、.\?\!\/\\()\[\]{}"'`]+/)
    .filter(t => t.length > 0);
}

function loadAllLocalItems() {
  const items = [];
  const seen = new Set();
  const dataDir = DATA_DIR;
  if (!fs.existsSync(dataDir)) return items;
  const files = fs.readdirSync(dataDir).filter(f => f.endsWith('.json') && !f.endsWith('.tmp.json'));
  for (const f of files) {
    try {
      const raw = fs.readFileSync(path.join(dataDir, f), 'utf-8');
      const data = JSON.parse(raw);
      let arr = [];
      if (Array.isArray(data)) {
        arr = data;
      } else if (data.items && Array.isArray(data.items)) {
        arr = data.items;
      } else if (data.news && Array.isArray(data.news)) {
        arr = data.news;
      }
      for (const it of arr) {
        const key = it.url || (it.title || '') + '|' + (it.published || '');
        if (seen.has(key)) continue;
        seen.add(key);
        items.push(it);
      }
    } catch (e) {
      // skip corrupt files
    }
  }
  return items;
}

function scoreItem(it, tokens) {
  const hay = (
    (it.title || '') + ' ' + (it.title_zh || '') + ' ' +
    (it.summary || '') + ' ' + (it.summary_zh || '') + ' ' +
    (it.tag || '') + ' ' + (it.category || '') + ' ' + (it.type || '')
  ).toLowerCase();
  let score = 0;
  for (const t of tokens) {
    if (!t) continue;
    if (hay.includes(t)) score += 2;
    if ((it.title || '').toLowerCase().includes(t)) score += 4;
    if ((it.title_zh || '').toLowerCase().includes(t)) score += 4;
  }
  return score;
}

// ====== 本地配置读写 ======
function readAppConfig() {
  try {
    if (!fs.existsSync(APP_CONFIG_FILE)) return { baseUrl: '', apiKey: '', modelName: '' };
    return { ...JSON.parse(fs.readFileSync(APP_CONFIG_FILE, 'utf-8')) };
  } catch {
    return { baseUrl: '', apiKey: '', modelName: '' };
  }
}

function writeAppConfig(cfg) {
  const safe = { baseUrl: String(cfg.baseUrl || ''), apiKey: String(cfg.apiKey || ''), modelName: String(cfg.modelName || '') };
  fs.writeFileSync(APP_CONFIG_FILE, JSON.stringify(safe, null, 2), 'utf-8');
}

// ====== Window ======
let mainWindow;
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 780,
    minWidth: 900,
    minHeight: 600,
    title: 'AI 桌面学习助手',
    backgroundColor: '#0f1115',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }
}

// ====== IPC 处理器 ======
function setupIPC() {

  // --- 数据读取 ---
  ipcMain.handle('news:read-local', async () => {
    try {
      if (!fs.existsSync(DATA_FILE)) return { ok: true, items: [] };
      const raw = fs.readFileSync(DATA_FILE, 'utf-8');
      const data = JSON.parse(raw);
      let items = [];
      if (Array.isArray(data)) items = data;
      else if (data.items) items = data.items;
      return { ok: true, items, meta: { total: data.total_count, date: data.date, updated: data.updated_at } };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });

  ipcMain.handle('news:list-reports', async () => {
    try {
      if (!fs.existsSync(REPORTS_DIR)) return { ok: true, files: [] };
      const files = fs.readdirSync(REPORTS_DIR)
        .filter(f => f.endsWith('.md'))
        .map(f => ({ name: f, path: path.join(REPORTS_DIR, f), mtime: fs.statSync(path.join(REPORTS_DIR, f)).mtimeMs }))
        .sort((a, b) => b.mtime - a.mtime);
      return { ok: true, files };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });

  ipcMain.handle('news:read-report', async (_e, name) => {
    try {
      const safe = path.basename(name);
      const fp = path.join(REPORTS_DIR, safe);
      if (!fs.existsSync(fp)) return { ok: false, error: 'report not found' };
      const content = fs.readFileSync(fp, 'utf-8');
      return { ok: true, content, name: safe };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });

  // --- 采集 / 生成 ---
  ipcMain.handle('news:collect', async () => {
    return await runPython('collect_ai_news.py');
  });

  ipcMain.handle('news:quick-fetch', async () => {
    return await runPython('quick_fetch.py');
  });

  ipcMain.handle('news:generate-report', async (_e, dateStr) => {
    const args = [];
    if (dateStr) args.push('--date', dateStr);
    return await runPython('generate_report.py', args);
  });

  // --- 智能搜索 ---
  ipcMain.handle('news:search-local', async (_e, query) => {
    try {
      if (!query || !query.trim()) return { ok: true, items: [] };
      const tokens = tokenize(query);
      const all = loadAllLocalItems();
      const scored = all
        .map(it => ({ item: it, score: scoreItem(it, tokens) }))
        .filter(x => x.score > 0)
        .sort((a, b) => b.score - a.score);
      return { ok: true, items: scored.map(x => x.item), total: scored.length };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });

  // --- 关键词在线抓取 ---
  ipcMain.handle('news:fetch-by-keyword', async (_e, keyword) => {
    try {
      const scriptPath = path.join(__dirname, 'fetch_by_keyword.py');
      if (!fs.existsSync(scriptPath)) {
        return { ok: false, error: 'fetch_by_keyword.py not found' };
      }
      ensureDataDirs();
      const py = resolvePython();
      const child = spawn(py, [scriptPath, keyword], {
        cwd: SKILL_DIR,
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
          PYTHONHOME: undefined
        },
        windowsHide: true
      });

      let stdoutBuf = '';
      let stderrBuf = '';

      child.stdout.on('data', (d) => {
        const text = d.toString();
        stdoutBuf += text;
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('news:log', text);
        }
      });
      child.stderr.on('data', (d) => {
        const text = d.toString();
        stderrBuf += text;
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('news:log', text);
        }
      });

      return await new Promise((resolve) => {
        child.on('close', (code) => {
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('news:log', `\n[exit ${code}]\n`);
          }
          // 从 stdout 末尾反找最后一个 JSON 行
          const lines = stdoutBuf.trim().split('\n');
          let result = null;
          for (let i = lines.length - 1; i >= 0; i--) {
            const ln = lines[i].trim();
            if ((ln.startsWith('{') || ln.startsWith('[')) && (ln.endsWith('}') || ln.endsWith(']'))) {
              try { result = JSON.parse(ln); break; } catch (e) { /* continue */ }
            }
          }
          resolve({
            ok: code === 0 && result !== null,
            code,
            result,
            stdout: stdoutBuf,
            stderr: stderrBuf
          });
        });
      });
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });

  // --- 右键菜单 ---
  ipcMain.handle('card:context-menu', async (_e, info) => {
    return new Promise((resolve) => {
      const menu = Menu.buildFromTemplate([
        { label: '📖 原文', click: () => resolve({ action: 'original', info }) },
        { label: '🧠 解读', click: () => resolve({ action: 'interpret', info }) }
      ]);
      menu.popup({ window: mainWindow });
      menu.once('menu-will-close', () => {
        setTimeout(() => resolve({ action: 'close' }), 50);
      });
    });
  });

  // --- 原文抓取 ---
  ipcMain.handle('card:fetch-original', async (_e, url) => {
    try {
      const resp = await net.fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ai-desktop-helper/0.1'
        }
      });
      if (!resp.ok) return { ok: false, error: `HTTP ${resp.status}` };
      const html = await resp.text();
      return { ok: true, html, url };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // --- AI 解读 ---
  ipcMain.handle('card:interpret', async (_e, info) => {
    try {
      const scriptPath = path.join(__dirname, 'interpret.py');
      if (!fs.existsSync(scriptPath)) {
        return { ok: false, error: 'interpret.py not found' };
      }
      const py = resolvePython();
      const inputJSON = JSON.stringify(info);

      const child = spawn(py, [scriptPath], {
        cwd: SKILL_DIR,
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
          PYTHONHOME: undefined
        },
        windowsHide: true
      });

      let stdoutBuf = '';
      let stderrBuf = '';

      child.stdout.on('data', (d) => { stdoutBuf += d.toString(); });
      child.stderr.on('data', (d) => { stderrBuf += d.toString(); });

      // 发送 info JSON 到 stdin
      child.stdin.write(inputJSON);
      child.stdin.end();

      return await new Promise((resolve) => {
        child.on('close', (code) => {
          const lines = stdoutBuf.trim().split('\n');
          let result = null;
          for (let i = lines.length - 1; i >= 0; i--) {
            const ln = lines[i].trim();
            if (ln.startsWith('{') && ln.endsWith('}')) {
              try { result = JSON.parse(ln); break; } catch { /* */ }
            }
          }
          if (result && result.markdown) {
            resolve({ ok: true, markdown: result.markdown });
          } else {
            resolve({ ok: false, error: stderrBuf || 'no result', markdown: stdoutBuf });
          }
        });
        child.on('error', (err) => {
          resolve({ ok: false, error: err.message });
        });
      });
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });

  // --- 配置 ---
  ipcMain.handle('config:read', async () => {
    return readAppConfig();
  });

  ipcMain.handle('config:write', async (_e, cfg) => {
    try {
      writeAppConfig(cfg);
      return { ok: true };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });

  // --- 系统 ---
  ipcMain.handle('app:open-external', async (_e, url) => {
    shell.openExternal(url);
    return { ok: true };
  });

  ipcMain.handle('app:show-in-folder', async (_e, fp) => {
    shell.showItemInFolder(fp);
    return { ok: true };
  });

  ipcMain.handle('app:get-info', async () => {
    return {
      python: resolvePython(),
      platform: process.platform,
      dataDir: DATA_DIR,
      skillDir: SKILL_DIR,
      appDir: APP_DIR,
      electron: process.versions.electron,
      node: process.versions.node,
      chrome: process.versions.chrome
    };
  });
}

// ====== 生命周期 ======
app.whenReady().then(() => {
  ensureSkillConfig();
  ensureDataDirs();
  setupIPC();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
