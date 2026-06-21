# Electron 桌面应用集成指南

将 my-ai-daily-news 包装为 Electron 桌面应用（AI 桌面学习助手）的完整参考。

## 架构模式

```
Electron 主进程 (main.js)
  ├── IPC Handlers (15+ channels)
  ├── Python 子进程 (spawn → skill scripts)
  └── net.fetch (原文抓取, Chromium 网络栈)

preload.js (contextBridge)
  └── 暴露 window.api.* 安全接口

渲染进程 (renderer/)
  ├── index.html        ← 4 Tab 视图
  ├── styles.css        ← 暗色主题
  └── renderer.js       ← 所有交互逻辑
```

## 关键路径关系

项目约定 skill 目录在 Electron 项目的父级同层：

```
workspace/
├── ai-desktop-helper/       # Electron 项目
└── my-ai-daily-news/        # skill 目录（同级）
```

main.js 通过 `path.resolve(__dirname, '..', '..', 'my-ai-daily-news')` 定位。

## 核心部署模式

### Python 子进程（流式日志回传）

```javascript
function runPython(scriptName, args = []) {
  const py = resolvePython();      // 优先项目内 venv
  const child = spawn(py, [scriptPath, ...args], {
    cwd: SKILL_DIR,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONHOME: undefined }
  });
  child.stdout.on('data', (d) => {
    mainWindow.webContents.send('news:log', d.toString());
  });
}
```

### 智能本地搜索（tokenize + 评分）

从所有 data/*.json 文件中读取数据，URL 去重后按关键词评分排序：

```javascript
function tokenize(q) { /* 中文/英文分词 */ }
function loadAllLocalItems() { /* 遍历 data 目录 */ }
function scoreItem(it, tokens) { /* 标题/摘要/分类各加权重 */ }
```

### 在线抓取（fetch_by_keyword.py）

Python 脚本最后一行输出 JSON → Electron 从 stdout 末尾反找解析：

```javascript
const lines = stdoutBuf.trim().split('\n');
for (let i = lines.length - 1; i >= 0; i--) {
  if (ln.startsWith('{') && ln.endsWith('}')) {
    parsed = JSON.parse(ln); break;
  }
}
```

### AI 解读（interpret.py）

通过 stdin 传 JSON 到 Python 脚本，脚本返回 `{"markdown": "..."}`：

```python
info = json.loads(sys.stdin.read())
# 调用 OpenAI/Anthropic API
print(json.dumps({'markdown': content}, ensure_ascii=False))
```

### 原文抓取（net.fetch）

使用 Electron 的 Chromium 网络栈绕过 CORS：

```javascript
const resp = await net.fetch(url, {
  headers: { 'User-Agent': 'Mozilla/5.0 ... ai-desktop-helper/0.1' }
});
```

## 已知踩坑 (Pitfalls)

### 1. Electron 版本选择
- 最新稳定版 v42+ 有 ESM 兼容问题（@electron/get）
- 推荐 v37.x（如 v37.10.3）
- 验证：`npm install electron@37.10.3 --save-dev`

### 2. Windows 上 skill 目录链接
- `mklink /J`（junction link）在 Git Bash 中路径解析会错乱
- **改用 cp -r** 复制整个 skill 目录到 workspace 下
- 或保持原路径，main.js 中直接指向 `.hermes/skills/news/my-ai-daily-news`

### 3. 弹窗 hidden 属性被 CSS 覆盖
```css
/* 必须加 !important 覆盖 display:flex */
.modal-mask[hidden] { display: none !important; }
```

### 4. querySelectorAll 误用
```javascript
// ❌ 错误：querySelector 返回单个元素，没有 forEach
$('#stats .stat-btn').forEach(...)
// ✅ 正确
document.querySelectorAll('#stats .stat-btn').forEach(...)
```

### 5. escape 函数防自动格式化
```javascript
// 用字符串拼接防 IDE 将 & 自动转义为 &amp;
function escape(s) {
  return String(s).replace(/&/g, '&' + 'amp;');
}
```

### 6. APP_DIR 声明顺序
```javascript
// ❌ 先使用后定义
const APP_CONFIG_FILE = path.join(APP_DIR, ...)  // APP_DIR 尚未声明
// ✅ APP_DIR 必须在所有引用它的常量之前
const APP_DIR = path.resolve(__dirname, '..');
const APP_CONFIG_FILE = path.join(APP_DIR, 'src', 'config.json');
```

### 7. Python venv 路径跨平台
| 平台 | venv Python 路径 |
|------|-----------------|
| macOS/Linux | `python-runtime/bin/python` |
| Windows | `python-runtime/Scripts/python.exe` |

resolvePython() 需优先检测项目内 venv，回退到系统 Python。

### 8. 渲染层滚动
- `.main` 必须有 `height: 100vh; overflow: hidden`
- 引入中间层 `.view-scroll { flex: 1; min-height: 0; overflow-y: auto; }`

## IPC 通道清单

| 通道 | 方向 | 功能 |
|------|------|------|
| `news:read-local` | R→M→R | 读取 daily_news.json |
| `news:list-reports` | R→M→R | 列出 reports/ 目录 |
| `news:read-report` | R→M→R | 读取单个报告 |
| `news:collect` | R→M→R | 全量采集 |
| `news:quick-fetch` | R→M→R | 快速采集 |
| `news:generate-report` | R→M→R | 生成报告 |
| `news:search-local` | R→M→R | 本地搜索 |
| `news:fetch-by-keyword` | R→M→R | 在线抓取 arXiv |
| `card:context-menu` | R→M→R | 右键菜单 |
| `card:fetch-original` | R→M→R | 原文抓取 |
| `card:interpret` | R→M→R | AI 解读 |
| `config:read/write` | R→M→R | LLM 配置持久化 |
| `app:open-external` | R→M→R | 打开外链 |
| `app:show-in-folder` | R→M→R | 文件管理器显示 |
| `app:get-info` | R→M→R | 系统信息 |
| `news:log` | M→R | 日志流推送 |

## 数据格式

每条新闻统一格式（与 skill 兼容）：

```json
{
  "type": "论文|产品|视频|资讯|开源项目",
  "tag": "[论文·cs.CL]",
  "title": "...",
  "summary": "...",
  "url": "https://...",
  "published": "2026-05-12",
  "source": "arxiv|youtube|github",
  "category": "大模型|Agent|融资/商业|安全/治理|应用/产品|开源",
  "title_zh": "...",
  "summary_zh": "..."
}
```
