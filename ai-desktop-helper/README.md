# AI Desktop Helper

一个基于 Electron + Python 的 AI 桌面学习助手，用来采集、浏览、搜索并解读最新 AI 资讯。

An AI desktop learning assistant built with Electron and Python for collecting, browsing, searching, and interpreting the latest AI content.

## 项目简介

`ai-desktop-helper` 是一个本地桌面应用，聚合了多种 AI 信息源，并提供可视化浏览、历史报告、关键词检索与 AI 解读能力。

它将 Electron 桌面界面与内置的 `my-ai-daily-news` 采集脚本整合在一起，适合用于：

- 跟踪 AI 论文、产品、视频、新闻和开源项目
- 一键采集当日内容
- 生成日报与历史报告
- 对单条资讯进行 AI 解读
- 在本地数据中做全文搜索，必要时按关键词在线补抓

## 主要功能

- `快速采集`：快速获取一批最新 AI 内容
- `全量采集`：从多个数据源完整抓取当日内容
- `历史报告`：浏览已生成的 Markdown 报告
- `本地搜索`：按关键词搜索本地资讯
- `联网补抓`：本地无结果时，按关键词在线抓取
- `AI 解读`：对单条内容进行总结、解释与延展分析
- `采集控制台`：实时查看 Python 采集脚本输出日志

## 当前覆盖的数据源

- arXiv
- Product Hunt
- Hugging Face
- YouTube
- The Verge AI
- GitHub Trending
- Reddit AI
- Hacker News AI

说明：

- 不同数据源的可用性受网络环境、反爬策略和第三方站点稳定性影响。
- 项目对部分源提供了 fallback 逻辑，但并不保证任意时间都 100% 可抓取。

## 技术架构

- 桌面端：Electron
- 前端界面：原生 HTML / CSS / JavaScript
- 主进程：`src/main.js`
- IPC 桥接：`src/preload.js`
- Python 脚本：`my-ai-daily-news/scripts/`
- 本地数据：`my-ai-daily-news/data/`
- 历史报告：`my-ai-daily-news/reports/`
- AI 解读：`src/interpret.py`

整体流程大致如下：

1. 用户在 Electron 界面点击采集、搜索或解读操作
2. Renderer 通过 `preload.js` 调用 IPC
3. `main.js` 调起对应 Python 脚本
4. Python 脚本抓取、整理、保存数据
5. 前端读取本地 JSON 或 Markdown 并展示结果

## 目录结构

```text
ai-desktop-helper/
├─ src/
│  ├─ main.js
│  ├─ preload.js
│  ├─ interpret.py
│  ├─ fetch_by_keyword.py
│  └─ renderer/
├─ my-ai-daily-news/
│  ├─ scripts/
│  ├─ data/
│  ├─ reports/
│  ├─ references/
│  ├─ config.json
│  └─ SKILL.md
├─ package.json
├─ start.bat
└─ README.md
```

## 环境要求

- Node.js 18+
- npm 9+
- Python 3.9+

建议：

- Windows 用户可直接使用 `start.bat`
- macOS / Linux 用户建议手动安装依赖并启动

## 启动方式

### 方式一：Windows 一键启动

在项目根目录双击：

```bat
start.bat
```

该脚本会自动：

- 检查 Node.js / npm / Python
- 创建 `python-runtime` 虚拟环境
- 安装 Python 依赖
- 安装 Node.js 依赖
- 尝试安装 Playwright Chromium
- 启动 Electron 应用

### 方式二：手动启动

#### 1. 安装 Node.js 依赖

```bash
npm install
```

#### 2. 创建 Python 虚拟环境

macOS / Linux:

```bash
python3 -m venv python-runtime
source python-runtime/bin/activate
pip install -r my-ai-daily-news/references/requirements.txt
```

Windows:

```bat
python -m venv python-runtime
python-runtime\Scripts\activate
pip install -r my-ai-daily-news\references\requirements.txt
```

#### 3. 可选：安装 Playwright 浏览器

macOS / Linux:

```bash
python-runtime/bin/playwright install chromium
```

Windows:

```bat
python-runtime\Scripts\playwright install chromium
```

#### 4. 启动 Electron

```bash
npm start
```

## 配置说明

### AI 解读配置

编辑文件：

`src/config.json`

示例：

```json
{
  "baseUrl": "https://your-llm-endpoint/v1",
  "apiKey": "your_api_key",
  "modelName": "your_model_name"
}
```

说明：

- `baseUrl`：模型服务地址，支持 OpenAI 兼容接口或兼容 Anthropic 的中转接口
- `apiKey`：你的模型服务密钥
- `modelName`：要调用的模型名称

### 采集源配置

编辑文件：

`my-ai-daily-news/config.json`

你可以在这里控制：

- 各数据源是否启用
- 每个源的抓取条数
- 输出文件位置
- 分类与摘要相关设置

## 数据与输出文件

- 当日新闻数据：`my-ai-daily-news/data/daily_news.json`
- 历史数据：`my-ai-daily-news/data/`
- Markdown 报告：`my-ai-daily-news/reports/`
- 运行日志：`my-ai-daily-news/logs/`

## 隐私与发布建议

项目已经尽量将用户敏感配置与运行时文件隔离。

发布到 GitHub 前，建议确认以下内容不要提交：

- `src/config.json`
- `my-ai-daily-news/config.json`
- `python-runtime/`
- `node_modules/`
- `my-ai-daily-news/data/`
- `my-ai-daily-news/reports/`
- `my-ai-daily-news/logs/`

如果你使用自己的 API Key、中转地址、Webhook 或 Bot Token，请务必只保留在本地配置文件中。

## 常见问题

### 1. 为什么有些源抓不到内容？

可能原因包括：

- 当前网络环境不稳定
- 第三方站点接口变更
- 目标站点开启反爬限制
- Playwright 浏览器未安装

### 2. 为什么 AI 解读失败？

优先检查：

- `src/config.json` 是否填写了有效的 `baseUrl`
- `apiKey` 是否可用
- `modelName` 是否正确
- 所使用的中转服务是否支持当前模型

### 3. 为什么 Windows 上首次启动较慢？

因为首次运行通常会自动完成：

- Python 虚拟环境创建
- 依赖安装
- Playwright 浏览器安装

## License

MIT

## 一句话总结

中文：这是一个把 AI 资讯采集、历史归档、本地搜索和模型解读整合到一起的桌面学习助手。

English: This project is a desktop learning assistant that combines AI news collection, archiving, local search, and model-based interpretation in one app.
