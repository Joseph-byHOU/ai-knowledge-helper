#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中英文翻译 & 双语报告生成模块
为 AI 日报提供中英文双语能力
"""

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def translate_title(title, target_lang="zh"):
    """
    简单的标题翻译（基于规则 + 常见词汇替换）
    实际使用时可接入翻译 API

    Args:
        title: 原标题
        target_lang: 目标语言 "zh" 或 "en"

    Returns:
        str: 翻译后的标题
    """
    if not title:
        return ""

    # 如果已经是中文，返回原样
    if target_lang == "zh" and has_chinese(title):
        return title
    if target_lang == "en" and not has_chinese(title):
        return title

    # 常见 AI 词汇翻译表
    AI_TERMS = {
        # En → Zh
        "releases": "发布",
        "launches": "推出",
        "introduces": "推出",
        "announces": "宣布",
        "unveils": "发布",
        "new": "全新",
        "model": "模型",
        "framework": "框架",
        "platform": "平台",
        "tool": "工具",
        "agent": "代理",
        "agents": "代理",
        "LLM": "大语言模型",
        "GPT": "GPT",
        "training": "训练",
        "fine-tuning": "微调",
        "reasoning": "推理",
        "generation": "生成",
        "evaluation": "评估",
        "benchmark": "基准",
        "open-source": "开源",
        "open source": "开源",
        "funding": "融资",
        "investment": "投资",
        "acquires": "收购",
        "partners with": "合作",
        "AI": "AI",
        "artificial intelligence": "人工智能",
        "machine learning": "机器学习",
        "deep learning": "深度学习",
        "neural network": "神经网络",
        "transformer": "Transformer",
        "safety": "安全",
        "alignment": "对齐",
        "robustness": "鲁棒性",
        "multimodal": "多模态",
        "efficient": "高效",
        "scalable": "可扩展",
    }

    if target_lang == "zh":
        result = title
        for en_term, zh_term in sorted(AI_TERMS.items(), key=lambda x: -len(x[0])):
            # 区分大小写替换
            result = re.sub(r'\b' + re.escape(en_term) + r'\b', zh_term, result, flags=re.IGNORECASE)
        return result

    return title


def has_chinese(text):
    """检查文本是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def summarize_text(text, max_length=150, lang="zh"):
    """
    智能摘要：截取并优化显示

    Args:
        text: 原文
        max_length: 最大长度
        lang: 语言

    Returns:
        str: 摘要文本
    """
    if not text:
        return "暂无描述" if lang == "zh" else "No description"

    # 清理空白
    text = re.sub(r'\s+', ' ', text).strip()

    if len(text) <= max_length:
        return text

    # 在句号/换行处截断
    truncated = text[:max_length]
    # 在最后一个完整句子处截断
    last_period = max(
        truncated.rfind('.'),
        truncated.rfind('。'),
        truncated.rfind('!'),
        truncated.rfind('！'),
        truncated.rfind('?'),
        truncated.rfind('？'),
    )

    if last_period > max_length // 2:
        return truncated[:last_period + 1]

    # 在最后一个空格截断
    last_space = truncated.rfind(' ')
    if last_space > max_length // 2:
        return truncated[:last_space] + "..."

    return truncated + "..."


def format_zh_report(news_data, items_by_category=None):
    """
    生成中文日报

    Args:
        news_data: 新闻数据字典
        items_by_category: 按分类分组的新闻

    Returns:
        str: 中文日报文本
    """
    date_str = news_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    items = news_data.get('items', [])

    lines = []
    lines.append(f"📰 **AI日报 - {date_str}**")
    
    # 统计
    total = len(items)
    paper_count = sum(1 for i in items if i.get('type') == '论文')
    product_count = sum(1 for i in items if i.get('type') == '产品')
    github_count = sum(1 for i in items if i.get('type') == '开源项目')
    other_count = total - paper_count - product_count - github_count
    lines.append(f"今日精选 {total} 条 | 论文 {paper_count} | 产品 {product_count} | 开源 {github_count} | 其他 {other_count}")
    lines.append("")

    if items_by_category:
        # 按分类输出
        category_order = ["大模型", "Agent", "应用/产品", "融资/商业", "安全/治理", "开源", "其他"]
        for cat in category_order:
            if cat in items_by_category and items_by_category[cat]:
                icon_map = {
                    "大模型": "🧠", "Agent": "🤖", "应用/产品": "🔧",
                    "融资/商业": "💰", "安全/治理": "🛡️", "开源": "🔓", "其他": "📌"
                }
                lines.append("---")
                lines.append(f"{icon_map.get(cat, '📌')} **{cat}**")
                lines.append("")
                for item in items_by_category[cat]:
                    tag = item.get('tag', '[资讯]')
                    title = item.get('title_zh', item.get('title', '无标题'))
                    summary = item.get('summary_zh', item.get('summary', ''))
                    summary = summarize_text(summary, 100, "zh")
                    url = item.get('url', '')

                    lines.append(f"**{tag} {title}**")
                    if summary:
                        lines.append(f"> {summary}")
                    if url:
                        lines.append(f"> 🔗 [查看详情]({url})")
                    lines.append("")
    else:
        # 无分类，按类型输出
        type_order = ["论文", "产品", "视频", "资讯", "开源项目"]
        type_icons = {"论文": "📚", "产品": "🚀", "视频": "📺", "资讯": "📰", "开源项目": "⭐"}
        for t in type_order:
            type_items = [i for i in items if i.get('type') == t]
            if type_items:
                lines.append("---")
                lines.append(f"{type_icons.get(t, '📌')} **{t}**")
                lines.append("")
                for item in type_items:
                    tag = item.get('tag', '[资讯]')
                    title = item.get('title_zh', item.get('title', '无标题'))
                    summary = item.get('summary_zh', item.get('summary', ''))
                    summary = summarize_text(summary, 100, "zh")
                    url = item.get('url', '')
                    lines.append(f"**{tag} {title}**")
                    if summary:
                        lines.append(f"> {summary}")
                    if url:
                        lines.append(f"> 🔗 [查看详情]({url})")
                    lines.append("")

    lines.append("---")
    lines.append("🐱 *由 Cookie 自动推送*")
    return '\n'.join(lines)


def format_en_report(news_data, items_by_category=None):
    """
    生成英文日报

    Args:
        news_data: 新闻数据字典
        items_by_category: 按分类分组的新闻

    Returns:
        str: 英文日报文本
    """
    date_str = news_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    items = news_data.get('items', [])

    lines = []
    lines.append(f"📰 **AI Daily - {date_str}**")

    total = len(items)
    paper_count = sum(1 for i in items if i.get('type') == '论文')
    product_count = sum(1 for i in items if i.get('type') == '产品')
    github_count = sum(1 for i in items if i.get('type') == '开源项目')
    lines.append(f"{total} items today | Papers {paper_count} | Products {product_count} | GitHub {github_count}")
    lines.append("")

    category_map_en = {
        "大模型": "🧠 LLMs", "Agent": "🤖 Agents", "应用/产品": "🔧 Apps & Products",
        "融资/商业": "💰 Funding & Business", "安全/治理": "🛡️ Safety & Governance",
        "开源": "🔓 Open Source", "其他": "📌 Other"
    }
    type_map_en = {
        "论文": "📚 Papers", "产品": "🚀 Products", "视频": "📺 Videos",
        "资讯": "📰 News", "开源项目": "⭐ GitHub"
    }

    if items_by_category:
        category_order = ["大模型", "Agent", "应用/产品", "融资/商业", "安全/治理", "开源", "其他"]
        for cat in category_order:
            if cat in items_by_category and items_by_category[cat]:
                lines.append("---")
                lines.append(f"**{category_map_en.get(cat, cat)}**")
                lines.append("")
                for item in items_by_category[cat]:
                    tag = item.get('tag', '[News]')
                    title = item.get('title', 'No title')
                    summary = summarize_text(item.get('summary', ''), 150, "en")
                    url = item.get('url', '')
                    lines.append(f"**{tag} {title}**")
                    if summary:
                        lines.append(f"> {summary}")
                    if url:
                        lines.append(f"> 🔗 [Details]({url})")
                    lines.append("")
    else:
        type_order = ["论文", "产品", "视频", "资讯", "开源项目"]
        for t in type_order:
            type_items = [i for i in items if i.get('type') == t]
            if type_items:
                lines.append("---")
                lines.append(f"**{type_map_en.get(t, t)}**")
                lines.append("")
                for item in type_items:
                    tag = item.get('tag', '[News]')
                    title = item.get('title', 'No title')
                    summary = summarize_text(item.get('summary', ''), 150, "en")
                    url = item.get('url', '')
                    lines.append(f"**{tag} {title}**")
                    if summary:
                        lines.append(f"> {summary}")
                    if url:
                        lines.append(f"> 🔗 [Details]({url})")
                    lines.append("")

    lines.append("---")
    lines.append("🐱 *Auto-pushed by Cookie*")
    return '\n'.join(lines)


def generate_bilingual_report(news_data, items_by_category=None):
    """
    生成中英双语报告

    Returns:
        tuple: (zh_report, en_report)
    """
    zh = format_zh_report(news_data, items_by_category)
    en = format_en_report(news_data, items_by_category)
    return zh, en


def add_translations(items):
    """
    为新闻添加中文翻译字段

    Args:
        items: 新闻列表

    Returns:
        list: 添加了 title_zh / summary_zh 的新闻列表
    """
    for item in items:
        title = item.get("title", "")
        summary = item.get("summary", "")

        if title and not has_chinese(title):
            item["title_zh"] = translate_title(title, "zh")

        if summary and not has_chinese(summary):
            # 取前100字符翻译标题式摘要
            short_summary = summary[:200]
            item["summary_zh"] = translate_title(short_summary, "zh")
        else:
            item["summary_zh"] = summary

    return items


if __name__ == "__main__":
    # 测试
    test_data = {
        "date": "2026-05-12",
        "items": [
            {"type": "论文", "tag": "[论文·cs.CL]", "title": "GPT-5: Scaling Language Models to 10 Trillion Parameters",
             "summary": "OpenAI releases GPT-5 with 10 trillion parameters, achieving state-of-the-art results on multiple benchmarks.",
             "url": "https://arxiv.org/abs/1234.56789"},
            {"type": "产品", "tag": "[产品·ProductHunt]", "title": "AutoAgent Pro - AI Agent Platform",
             "summary": "Build and deploy AI agents with no code.",
             "url": "https://producthunt.com/posts/autoagent"},
        ]
    }

    add_translations(test_data["items"])
    zh, en = generate_bilingual_report(test_data)
    print("=== 中文版 ===")
    print(zh)
    print("\n=== English ===")
    print(en)
