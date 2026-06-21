---
name: my-ai-daily-news
description: |
  最强AI日报系统。自动采集 arXiv 论文、Hugging Face 趋势模型、Product Hunt AI 产品、YouTube AI 博主视频、The Verge AI 新闻、GitHub 热门开源项目、自定义 RSS 源。
  支持：中英文双语输出 | 智能分类（大模型/Agent/融资/安全/应用/开源）| 多渠道推送（飞书/Telegram/Discord）| 浏览器备选抓取
  中文名：我的AI日报

  Use when: (1) 每天定时采集AI资讯推送日报, (2) 手动查询最新AI论文/产品/模型/视频, (3) 生成周报/月报, (4) 监控特定AI领域动态, (5) 设置自动化新闻流水线
tags:
  - ai-news
  - daily-report
  - arxiv
  - huggingface
  - producthunt
  - youtube
  - github-trending
  - rss
  - feishu
---

# 🐱 我的AI日报 — My AI Daily News

自动采集 → 智能分类 → 双语报告 → 多渠道推送

全面覆盖 8 大数据源，支持浏览器备选抓取，中英文双语输出，飞书/Telegram/Discord 多渠道推送。

---

## 桌面应用集成

本 skill 可作为 Electron 桌面应用的数据后端。`references/electron-desktop-app.md` 记录了完整的集成方案：

- Electron 主进程 IPC 通信（15+ 通道）
- Python 子进程流式日志回传
- 智能本地搜索（tokenize + 评分排序）
- arXiv 在线关键词抓取
- 大模型 AI 解读（OpenAI / Anthropic）
- Windows/macOS 跨平台实践
- 完整踩坑记录

**项目结构要求：** Electron 项目与 skill 目录在 workspace 下同级。

## 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r references/requirements.txt
playwright install chromium    # 可选，用于浏览器备选抓取
```

### 2️⃣ 初始化配置

```bash
python scripts/setup_config.py
```

或者手动编辑 `config.json`。

### 3️⃣ 首次运行

```bash
# 采集数据
python scripts/collect_ai_news.py

# 生成并推送日报
python scripts/push_to_feishu.py
```

### 4️⃣ 定时推送（推荐）

通过 Hermes cron 设置每日自动推送：

```bash
# 每天早上 8:00 推送中英文双语日报
hermes cron create \
  --name "my-daily-news" \
  --schedule "0 8 * * *" \
  --skill "my-ai-daily-news" \
  --prompt "按 my-ai-daily-news 技能流程，采集最新 AI 资讯，分别生成中文日报和英文日报并推送。"
```

---

## 数据源一览

| 源 | 类型 | 采集方式 | 备选方案 |
|----|------|---------|---------|
| **arXiv** 📚 | 论文 | RSS API | Playwright 浏览器 |
| **Hugging Face** 🤗 | 趋势模型 | REST API | Playwright 浏览器 |
| **Product Hunt** 🚀 | AI 产品 | RSS Feed | Playwright 浏览器 |
| **YouTube** 📺 | 博主视频 | yt-dlp | RSS / Playwright |
| **The Verge AI** 🌐 | AI 资讯 | RSS + Web | Playwright 浏览器 |
| **GitHub Trending** ⭐ | 开源项目 | GitHub API | Playwright 浏览器 |
| **PaperWeekly** 📖 | 论文解读 | RSS (自定义) | 浏览器备选 |
| **自定义 RSS** 📰 | 任何 RSS | feedparser | 浏览器备选 |

**YouTube AI 博主**（可配置）:
- `andrew_ng` — 吴恩达 / DeepLearning.AI
- `matt_wolfe` — AI 工具和生产力内容
- `ai_explained` — AI 新闻和技术解读
- `ai_with_oliver` — AI 工具教程
- `greg_isenberg` — AI 创业和产品策略
- `fireship` — 科技教程

---

## 配置

### 配置文件 `config.json`

```json
{
  "feishu": {
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    "chat_id": "oc_xxx"
  },
  "telegram": {
    "bot_token": "",
    "chat_id": ""
  },
  "discord": {
    "webhook_url": ""
  },
  "language": "zh",               // "zh" | "en" | "both"
  "schedule": {
    "collect_time": "06:00",
    "push_time": "08:00",
    "timezone": "Asia/Shanghai"
  },
  "sources": {
    "arxiv": {
      "enabled": true,
      "categories": ["cs.CL", "cs.LG", "cs.AI", "cs.CV", "cs.RO"],
      "max_results": 5,
      "days_back": 1
    },
    "huggingface": {
      "enabled": true,
      "max_results": 5,
      "task": ""
    },
    "producthunt": {
      "enabled": true,
      "max_results": 4
    },
    "youtube": {
      "enabled": true,
      "creators": ["andrew_ng", "matt_wolfe", "ai_explained"],
      "days_back": 7,
      "max_per_creator": 2
    },
    "theverge": {
      "enabled": true,
      "max_items": 5,
      "days_back": 1
    },
    "github": {
      "enabled": true,
      "max_results": 3
    },
    "paperweekly": {
      "enabled": false,
      "rss_url": ""
    },
    "rss": {
      "enabled": false,
      "days_back": 7,
      "feeds": []
    }
  },
  "classification": {
    "enabled": true,
    "categories": ["大模型", "Agent", "融资/商业", "安全/治理", "应用/产品", "开源"],
    "translate_to_zh": true
  },
  "output": {
    "max_summary_length": 100,
    "max_total_items": 20,
    "data_file": "data/daily_news.json",
    "report_dir": "reports/"
  },
  "fallback": {
    "enabled": true,
    "timeout": 30,
    "retry_times": 2
  }
}
```

---

## 使用场景

### 🎯 场景一：定时日报（推荐）

设置 cron 每日执行：

```bash
hermes cron create \
  --name "my-daily-news" \
  --schedule "0 8 * * *" \
  --skill "my-ai-daily-news" \
  --prompt "运行 my-ai-daily-news，采集最新AI资讯，生成中文日报并推送。语言: 中文。分类: 大模型/Agent/融资/安全/应用/开源。"
```

### 🎯 场景二：手动查询

告诉 Hermes：

> 帮我查一下今天 arXiv 上最新的大模型论文
> 看看 Product Hunt 今天有什么新的 AI 产品
> GitHub 上今天最火的开源项目是什么

### 🎯 场景三：周报/月报

```bash
python scripts/generate_report.py --sources all --max 10 --days 7 --output weekly_report.md
```

### 🎯 场景四：监控特定领域

修改 `arxiv.categories` 只保留你关注的领域（如 `cs.CV` 计算机视觉），其他源禁用。

---

## 智能分类系统

采集到的每条新闻会自动归类到以下分类：

| 分类 | 标识 | 匹配关键词（中/英） |
|------|------|-------------------|
| 🧠 **大模型** | `llm` | LLM, GPT, Claude, Gemini, 大模型, 语言模型, foundation model |
| 🤖 **Agent** | `agent` | Agent, 代理, autonomous, tool use, function calling |
| 💰 **融资/商业** | `funding` | 融资, funding, acquisition, 收购, IPO, investment |
| 🛡️ **安全/治理** | `safety` | safety, 安全, alignment, regulation, 监管, ethics |
| 🔧 **应用/产品** | `app` | 产品, product, launch, 发布, application, 应用 |
| 🔓 **开源** | `opensource` | open source, 开源, GitHub, Apache, MIT |

日报按分类组织，方便快速浏览。

---

## 多渠道推送

### 飞书 Webhook

配置 `config.json` 中的 `feishu.webhook_url`，然后：

```bash
python scripts/push_to_feishu.py
```

### 在 Hermes 中使用

Hermes 内置交付能力，用 send_message 推送到任何已连接渠道：

```
"@cookie 今天的AI日报好了，帮我推送到飞书和Telegram"
```

### 分批发送（新闻较多时）

```bash
python scripts/batch_sender.py
```

---

## 脚本总览

| 脚本 | 功能 | 来源 |
|------|------|------|
| **collect_ai_news.py** | 主采集器 — 统筹所有源 + fallback | ai-daily-news |
| **push_to_feishu.py** | 生成并推送飞书卡片日报 | ai-daily-news |
| **daily_scheduler.py** | 定时调度器（collect + push） | ai-daily-news |
| **generate_report.py** | 生成 markdown 格式完整报告 | ai-daily-news-search |
| **batch_sender.py** | 大量新闻分批推送 | ai-daily-news |
| **setup_config.py** | 交互式配置初始化 | ai-daily-news |
| **youtube_collector.py** | YouTube 视频采集（yt-dlp + RSS） | ai-daily-news |
| **verge_collector.py** | The Verge AI 新闻采集（RSS + Web） | ai-daily-news |
| **rss_collector.py** | 通用 RSS 采集 | ai-daily-news |
| **github_trending_collector.py** | GitHub 热门项目采集（API + 浏览器） | ai-daily-news |
| **browser_fallback.py** | Playwright 浏览器备选抓取引擎 | ai-daily-news |
| **search_arxiv.py** | arXiv 搜索工具（CLI） | ai-daily-news-search |
| **search_huggingface.py** | HF 模型搜索工具（CLI） | ai-daily-news-search |
| **search_producthunt.py** | Product Hunt 搜索工具（CLI） | ai-daily-news-search |
| **search_youtube.py** | YouTube 搜索工具（CLI） | ai-daily-news-search |
| **search_rss.py** | RSS 搜索工具（CLI） | ai-daily-news-search |
| **classifier.py** | 智能分类引擎（新增） | 新增 |
| **translator.py** | 中英文翻译 & 双语报告（新增） | 新增 |

---

## 数据格式

每条新闻的统一格式：

```python
{
    "type": "论文|产品|视频|资讯|开源项目",      # 类型
    "tag": "[论文·cs.CL]",                       # 带来源的标签
    "title": "Paper Title",                      # 标题
    "summary": "Brief description...",           # 摘要 (<200 chars)
    "url": "https://...",                        # 原文链接
    "published": "2026-05-12",                   # 发布日期
    "source": "arxiv|youtube|github",             # 来源标识
    "category": "大模型|Agent|融资/商业|...",      # 智能分类（可选）
    "title_zh": "中文标题",                       # 中文标题（可选）
    "summary_zh": "中文摘要"                      # 中文摘要（可选）
}
```

---

## 日报格式示例

### 中文版

```
📰 AI日报 - 2026-05-12
今日精选 15 条 | 论文 5 | 产品 3 | 视频 2 | 资讯 3 | GitHub 2

---
🧠 大模型
[论文·cs.CL] GPT-5 发布：...
> OpenAI 发布 GPT-5 模型...

🤖 Agent
[产品·ProductHunt] AutoAgent - 自动化AI代理平台
> 一键部署AI代理工作流...

💰 融资/商业
[资讯·The Verge] Anthropic 完成 10 亿美元融资
> ...

---
🐱 由 Cookie 自动推送
```

### 英文版

```
📰 AI Daily - 2026-05-12
15 items today | Papers 5 | Products 3 | Videos 2 | News 3 | GitHub 2

---
🧠 LLMs
[Paper·cs.CL] GPT-5 Released: ...
> OpenAI released GPT-5 model...

🤖 Agent
[Product·ProductHunt] AutoAgent - Autonomous AI Agent Platform
> Deploy AI agent workflows with one click...

---
🐱 Auto-pushed by Cookie
```

---

## 架构图

```
                         ┌──────────────────┐
                         │   config.json    │
                         └────────┬─────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │    collect_ai_news.py      │
                    │      (主采集器)             │
                    └──────┬─────┬──────┬───────┘
                           │     │      │
         ┌─────────────────┘     │      └──────────────┐
         ▼                       ▼                     ▼
   ┌──────────┐           ┌──────────┐          ┌──────────┐
   │  RSS API │           │  REST    │          │ yt-dlp   │
   │ (arXiv)  │           │  (GitHub)│          │(YouTube) │
   └────┬─────┘           └────┬─────┘          └────┬─────┘
        │                      │                     │
        ▼                      ▼                     ▼
   ┌─────────────────────────────────────────────────────┐
   │           browser_fallback.py (Playwright)           │
   └────────────────────┬────────────────────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  classifier.py   │  ← 智能分类
              │  translator.py   │  ← 双语翻译
              └────────┬─────────┘
                       │
               ┌───────┴──────────┐
               ▼                  ▼
       ┌────────────┐     ┌──────────────┐
       │ push_to_   │     │ generate_    │
       │ feishu.py  │     │ report.py    │
       └──────┬─────┘     └──────┬───────┘
              │                  │
              ▼                  ▼
        ┌─────────┐       ┌──────────┐
        │ 飞书Webhook │       │ .md 报告   │
        │ Telegram   │       │ .json 数据 │
        │ Discord    │       │           │
        └─────────┘       └──────────┘
```

---

## 常见问题

**Q: arXiv 返回 0 篇论文？**
A: 检查 `days_back` 参数。arXiv API 有一定延迟，设为 2-3 天试试。

**Q: YouTube 采集失败？**
A: 确保安装 `yt-dlp`（`pip install yt-dlp`），系统会回退到 RSS 或浏览器抓取。

**Q: 飞书推送没有反应？**
A: 检查 `webhook_url` 是否正确，可以在浏览器访问验证 webhook 地址。

**Q: 想只推中文/英文？**
A: 设置 `config.json` 中的 `language` 为 `"zh"` 或 `"en"`。

**Q: 浏览器抓取太慢？**
A: 大多数源有 RSS/API 主方案，浏览器 fallback 仅在主方案失败时使用。

**Q: 本地 API 全部超时，无法采集数据？**
A: 推荐使用 `delegate_task` 子任务方式采集 —— 这是本环境（Windows 受限网络）下**最可靠的主要采集方法**，而非兜底方案。详见 `references/delegate-task-fallback.md`。已验证的子任务可采集源：

| 源 | 状态 | 命令 |
|----|------|------|
| **arXiv** | ✅ | `curl -s "http://export.arxiv.org/api/query?search_query=cat:cs.CL+OR+cs.LG+OR+cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=15"` |
| **Product Hunt** | ✅ | `curl -s "https://www.producthunt.com/feed?category=artificial-intelligence"` |
| **GitHub Trending** | ✅ | `curl -s "https://api.github.com/search/repositories?q=stars:>100+created:>YYYY-MM-DD&sort=stars&order=desc&per_page=5"` |
| **TechCrunch AI** | ✅ | `curl -s "https://techcrunch.com/category/artificial-intelligence/feed"` |
| **Ars Technica** | ✅ | `curl -s "https://feeds.arstechnica.com/arstechnica/technology-lab"` |
| **Hugging Face** | ✅ | `curl -s "https://huggingface.co/api/models?limit=5&sort=downloads&direction=-1"` |
| **The Verge AI** | ✅ | `curl -s "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"` |
| **Reddit AI** | ✅ | `curl -s -A "Mozilla/5.0" "https://www.reddit.com/r/artificial/hot.json"` |
| YouTube | ⚠️ | 依赖 yt-dlp 与网络环境，部分地区不稳定 |

> 注：`GitHub Trending` 命令中的 `YYYY-MM-DD` 请替换为约 30 天前的日期。

## Pitfalls

1. **`delegate_task` 是主要方法，不是兜底方案** — 在 Windows 受限网络环境下，99% 的境外 API 直连（arXiv、HuggingFace、YouTube、GitHub API）会因 DNS 或连接超时而失败。应优先使用 `delegate_task` 通过子任务采集，而非运行本地的 `collect_ai_news.py`。\\\n   ✅ 正确的流程：\\\n   先 `delegate_task` 采集 arXiv + Product Hunt + GitHub + TechCrunch + Ars Technica\
   再本地运行 Python 脚本补漏（仅 Product Hunt 有可能本地成功）\
   最后用 classifier + translator 分类翻译

2. **`collect_ai_news.py` 需要 `config.json`** — 首次运行前必须创建配置文件（可通过 `python scripts/setup_config.py` 生成，或手写一份复制 SKILL.md 中的示例配置）。

3. **Product Hunt feed 是 Atom 格式** — 不是 RSS 2.0。feedparser 可自动识别，但手动解析时注意 `<entry>` 标签而非 `<item>`。在子任务环境中可通过 `feedparser.parse()` 统一处理。

4. **Product Hunt RSS 请求用 `category=artificial-intelligence`** — 官方 API 不需要 token，RSS feed 即可获取 10-15 条最近产品。

5. **Playwright fallback 可能因版本不兼容失败** — `browser_fallback.py` 中的 `scrape_with_playwright` 依赖 Playwright 的 `ElementHandle.tag_name` 属性（property，非方法）。不同版本的 Playwright 或 arXiv 页面结构变化可能导致 fallback 失效。建议优先用 `delegate_task` 而非 Playwright。

6. **GitHub API 搜索日期参数需动态更新** — 搜索日期应随时间推移更新。在子任务中生成时拼接 `created:>$(date -d '-30 days' +%Y-%m-%d)` 或固定为约 30 天前。

7. **子任务返回格式必须是纯 Python 可 eval 的列表** — 因为结果会通过 JSON 序列化传回，确保每个 item 是简单 dict，不含自定义对象或不可序列化类型。

**Q: Product Hunt RSS 返回 Atom 格式，无法解析？**
A: Product Hunt 的 feed 是 Atom 格式（`<entry>` 标签）而非 RSS 2.0（`<item>` 标签）。使用 feedparser 可以自动识别两种格式。如需手动解析，注意用 `feed.entries` 统一处理。

---

## 依赖

```txt
requests>=2.28.0
feedparser>=6.0.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
yt-dlp>=2023.0.0
playwright>=1.35.0          # 可选，用于浏览器备选抓取
schedule>=1.1.0             # 可选，用于定时调度
```

---

## 技术细节

- **Python 3.10+** 兼容
- **Fallback 机制**：每个数据源都有 主方法 → 浏览器备选 → 渐进降级
- **去重**：基于 URL 的自动去重
- **增量更新**：只采集新数据，避免重复
- **日志系统**：`logs/` 目录下按日期记录详细日志
- **错误恢复**：单个源失败不影响其他源
- **可扩展架构**：新增一个数据源只需 3 步——写采集函数 + 写 fallback + 注册到主采集器

---

## 扩展指南

### 添加新的数据源

1. 在 `scripts/` 下创建采集模块（参考 `verge_collector.py`）
2. 在 `browser_fallback.py` 添加备选方案（参考 `fallback_verge_ai_news`）
3. 在 `collect_ai_news.py` 的 `main()` 中注册
4. 在 `config.json` 的 `sources` 添加配置项

### 添加新的推送渠道

在 `push_to_feishu.py` 中参考飞书 Webhook 方式添加其他渠道推送方法。

---

*🐱 由 Cookie 整合三个 AI 日报 skill 而成 — 最强、最全、最好用*
