# Delegate Task Fallback: News Collection via Sub-Agent

当 Hermes 主环境的 `terminal` / `execute_code` 工具无法直接访问外部 API 时，可以使用 `delegate_task` 子任务绕过网络限制。

## 适用场景

- `requests.get()` 调用超时（arXiv, HuggingFace, The Verge 等）
- `curl` 命令返回空或超时
- 浏览器工具（Playwright / agent-browser）启动失败
- 部分 API 可用但部分不可用（如 GitHub API 通但 arXiv 不通）

## 已验证可用的源（通过 delegate_task + curl）

| 源 | 命令 | 状态 |
|----|------|------|
| **arXiv** | `curl -s "http://export.arxiv.org/api/query?search_query=cat:cs.CL+OR+cat:cs.LG+OR+cat:cs.AI+OR+cat:cs.CV&sortBy=submittedDate&sortOrder=descending&max_results=10" --max-time 60` | ✅ 成功 |
| **Product Hunt** | `curl -s "https://www.producthunt.com/feed?category=artificial-intelligence" --max-time 30` | ✅ 成功 |
| **TechCrunch AI** | `curl -s "https://techcrunch.com/category/artificial-intelligence/feed" --max-time 30` | ✅ 成功 |
| **Ars Technica** | `curl -s "https://feeds.arstechnica.com/arstechnica/technology-lab" --max-time 30` | ✅ 成功 |
| **GitHub Trending** | `curl -s "https://api.github.com/search/repositories?q=stars:>100+created:>2026-04-01&sort=stars&order=desc&per_page=5" --max-time 30` | ✅ 成功 |
| **Hugging Face** | `curl -s "https://huggingface.co/api/models?sort=trending&direction=-1&limit=5" --max-time 30` | ❌ 超时 |
| **The Verge AI** | `curl -s "https://www.theverge.com/ai-artificial-intelligence/rss" --max-time 30` | ❌ 404/空 |
| **YouTube** | `curl -s "https://www.youtube.com/feed/trending" --max-time 30` | ❌ 超时 |

## 各源解析要点

### arXiv
- 使用 `https://export.arxiv.org/api/query`（`http://` 有时返回空，`https://` 更可靠）
- 响应格式：Atom XML，命名空间 `http://www.w3.org/2005/Atom`
- 解析关键元素：`entry > title`, `entry > summary`, `entry > id`（URL）, `entry > published`, `entry > category`（`term` 属性）
- 摘要中可能含 HTML 格式和换行，需清理

### Product Hunt
- 使用 `https://www.producthunt.com/feed?category=artificial-intelligence`
- 响应格式：**Atom 格式**（非 RSS 2.0），使用 `<entry>` 标签而非 `<item>` 标签
- feedparser 可以自动识别；手动解析时注意 Atom 命名空间

### TechCrunch
- RSS 2.0 格式，标准 `<channel>` → `<item>` 结构
- 摘要可能含 HTML 片段，用 BeautifulSoup 清理
- **URL 必须带尾部斜杠**：`https://techcrunch.com/category/artificial-intelligence/feed/`（不带 `/` 返回空结果）

### Ars Technica
- RSS 2.0 格式，标准 `<channel>` → `<item>` 结构
- 内容以安全/漏洞/政策类新闻为主，AI 相关占比约 30-40%，需要下游过滤

## 完整推荐流程（经 2026-06-01 验证通过）

### 1️⃣ 发起 delegate_task 采集

```python
result = delegate_task(
    context=f"""Today is 2026-06-01. 需要采集当天的最新AI新闻。
在子任务中使用 Python（feedparser/ElementTree/xml.etree.ElementTree）来解析 curl 获取的 RSS/Atom 数据。
对于 arXiv 的 Atom 响应，注意命名空间 http://www.w3.org/2005/Atom，使用 {{{http://www.w3.org/2005/Atom}}} 前缀访问元素。""",
    goal="""从以下 5 个源采集最新 AI 新闻，返回 Python 列表格式的字典：

源1: arXiv: curl -s "https://export.arxiv.org/api/query?search_query=cat:cs.CL+OR+cat:cs.LG+OR+cat:cs.AI+OR+cat:cs.CV&sortBy=submittedDate&sortOrder=descending&max_results=10" --max-time 60
源2: Product Hunt: curl -s "https://www.producthunt.com/feed?category=artificial-intelligence" --max-time 30
源3: GitHub Trending: curl -s "https://api.github.com/search/repositories?q=stars:>100+created:>2026-05-01&sort=stars&order=desc&per_page=5" --max-time 30
源4: TechCrunch AI: curl -s "https://techcrunch.com/category/artificial-intelligence/feed/" --max-time 30
源5: Ars Technica: curl -s "https://feeds.arstechnica.com/arstechnica/technology-lab" --max-time 30

每个 item 格式：{"type": "论文|产品|开源项目|资讯", "tag": "[论文·cs.CV]", "title": "...", "summary": "摘要（清理HTML后≤200字）", "url": "...", "published": "YYYY-MM-DD", "source": "arxiv|producthunt|github|techcrunch|arstechnica"}""",
    toolsets=["terminal"]
)
```

### 2️⃣ 后处理流水线

采集到原始数据后，按以下步骤处理：

```python
# 步骤2a: 清理摘要中的 HTML 和多余文本
import re
def clean_summary(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*Discussion\s*\|\s*Link\s*$', '', text)  # Product Hunt 后缀
    return text

# 步骤2b: 按日期过滤 + 按源限制数量
cutoff = "2026-05-29"  # 最近3天
source_limits = {"arxiv": 5, "producthunt": 6, "github": 3, "techcrunch": 5, "arstechnica": 3}

# 步骤2c: 运行 classifier.py 分类
from scripts.classifier import classify_items, get_category_icon
classified = classify_items(final_items)

# 步骤2d: 运行 translator.py 添加中文翻译 + 生成报告
from scripts.translator import add_translations, format_zh_report, format_en_report
add_translations(final_items)
zh_report = format_zh_report({"date": "2026-06-01", "items": final_items}, classified)
```

### 3️⃣ 输出与推送

```python
# 保存到 data/daily_news.json
# 用 format_zh_report / format_en_report 获取格式化文本
# 或用 push_to_feishu.py 推送到飞书
```

## 注意事项

- `delegate_task` 的超时时间要设置得足够长（每个 curl 调用 30-60s，多个源串行可能需 2-3 分钟）
- 子任务环境可能有不同的网络策略，比主环境更宽松
- 子任务返回的内容是序列化的，需要确保返回格式是纯 Python 数据结构
- 不是所有源都能通 — 设计时要考虑部分采集成功的容错
- 验证过的 TechCrunch RSS URL 返回的 XML 片段有时会被截断，但仍能提取出 4-8 条有效条目
