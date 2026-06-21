#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate AI Daily News Report combining all sources
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Import search modules
sys.path.insert(0, str(Path(__file__).parent))
import search_arxiv
import search_huggingface
import search_producthunt
import search_youtube
import search_rss


def generate_report(sources=None, max_items=5, days_back=None):
    """Generate combined report from multiple sources"""
    
    if sources is None or sources == ["all"]:
        sources = ["arxiv", "huggingface", "producthunt", "youtube", "rss"]
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sources": {},
        "summary": {}
    }
    
    all_items = []
    
    # arXiv
    if "arxiv" in sources:
        print("Fetching arXiv papers...", file=sys.stderr)
        papers = search_arxiv.search_arxiv(max_results=max_items, days_back=days_back or 1)
        report["sources"]["arxiv"] = papers
        all_items.extend(papers)
        report["summary"]["arxiv"] = len(papers)
    
    # Hugging Face
    if "huggingface" in sources:
        print("Fetching Hugging Face models...", file=sys.stderr)
        models = search_huggingface.search_huggingface(max_results=max_items)
        report["sources"]["huggingface"] = models
        all_items.extend(models)
        report["summary"]["huggingface"] = len(models)
    
    # Product Hunt
    if "producthunt" in sources:
        print("Fetching Product Hunt products...", file=sys.stderr)
        products = search_producthunt.search_producthunt(max_results=max_items)
        report["sources"]["producthunt"] = products
        all_items.extend(products)
        report["summary"]["producthunt"] = len(products)
    
    # YouTube
    if "youtube" in sources:
        print("Fetching YouTube videos...", file=sys.stderr)
        videos = search_youtube.search_youtube(max_per_creator=2, days_back=days_back or 7)
        report["sources"]["youtube"] = videos
        all_items.extend(videos)
        report["summary"]["youtube"] = len(videos)
    
    # RSS
    if "rss" in sources:
        print("Fetching RSS feeds...", file=sys.stderr)
        rss_items = search_rss.search_rss(max_per_feed=3, days_back=days_back or 7)
        report["sources"]["rss"] = rss_items
        all_items.extend(rss_items)
        report["summary"]["rss"] = len(rss_items)
    
    report["total_items"] = len(all_items)
    report["all_items"] = all_items
    
    return report


def format_markdown_report(report):
    """Format report as markdown"""
    
    lines = []
    lines.append(f"# 📰 AI Daily News - {report['date']}")
    lines.append("")
    
    # Summary
    total = report.get("total_items", 0)
    lines.append(f"**Total: {total} items**")
    lines.append("")
    
    for source, count in report.get("summary", {}).items():
        emoji = {
            "arxiv": "📚",
            "huggingface": "🤗",
            "producthunt": "🚀",
            "youtube": "📺",
            "rss": "📰"
        }.get(source, "📌")
        lines.append(f"- {emoji} {source.capitalize()}: {count}")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # arXiv Papers
    if "arxiv" in report.get("sources", {}) and report["sources"]["arxiv"]:
        lines.append("## 📚 arXiv Papers")
        lines.append("")
        for paper in report["sources"]["arxiv"]:
            lines.append(f"### {paper['title']}")
            lines.append("")
            lines.append(f"> {paper['summary'][:300]}...")
            lines.append("")
            lines.append(f"**Authors:** {', '.join(paper.get('authors', [])[:3])}")
            lines.append(f"")
            lines.append(f"🔗 [arXiv]({paper['url']}) | [PDF]({paper.get('pdf_url', '')})")
            lines.append("")
    
    # Hugging Face
    if "huggingface" in report.get("sources", {}) and report["sources"]["huggingface"]:
        lines.append("## 🤗 Hugging Face Models")
        lines.append("")
        for model in report["sources"]["huggingface"]:
            lines.append(f"### {model['title']}")
            lines.append("")
            if model.get('summary'):
                lines.append(f"> {model['summary'][:200]}...")
                lines.append("")
            lines.append(f"⬇️ {model.get('downloads', 0):,} downloads | ❤️ {model.get('likes', 0):,} likes")
            lines.append("")
            lines.append(f"🔗 [View Model]({model['url']})")
            lines.append("")
    
    # Product Hunt
    if "producthunt" in report.get("sources", {}) and report["sources"]["producthunt"]:
        lines.append("## 🚀 Product Hunt")
        lines.append("")
        for product in report["sources"]["producthunt"]:
            lines.append(f"### {product['title']}")
            lines.append("")
            lines.append(f"> {product['summary']}")
            lines.append("")
            lines.append(f"🔗 [View on Product Hunt]({product['url']})")
            lines.append("")
    
    # YouTube
    if "youtube" in report.get("sources", {}) and report["sources"]["youtube"]:
        lines.append("## 📺 YouTube Videos")
        lines.append("")
        for video in report["sources"]["youtube"]:
            lines.append(f"### {video['title']}")
            lines.append("")
            if video.get('summary'):
                lines.append(f"> {video['summary'][:150]}...")
                lines.append("")
            lines.append(f"👀 {video.get('view_count', 0):,} views | ⏱️ {video.get('duration', 'N/A')}")
            lines.append("")
            lines.append(f"🔗 [Watch Video]({video['url']})")
            lines.append("")
    
    # RSS
    if "rss" in report.get("sources", {}) and report["sources"]["rss"]:
        lines.append("## 📰 RSS News")
        lines.append("")
        for item in report["sources"]["rss"]:
            lines.append(f"### {item['title']}")
            lines.append("")
            lines.append(f"> {item['summary'][:200]}...")
            lines.append("")
            lines.append(f"Source: {item['source']}")
            lines.append("")
            lines.append(f"🔗 [Read More]({item['url']})")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*Generated by AI Daily News Search* 🐱")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate AI Daily News Report")
    parser.add_argument("--sources", nargs="+", default=["all"],
                        choices=["all", "arxiv", "huggingface", "producthunt", "youtube", "rss"],
                        help="Sources to include (default: all)")
    parser.add_argument("--max", type=int, default=5,
                        help="Max items per source (default: 5)")
    parser.add_argument("--days", type=int,
                        help="Days back to search")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown",
                        help="Output format")
    parser.add_argument("--output", default="ai_daily_report.md",
                        help="Output file path")
    
    args = parser.parse_args()
    
    print("Generating AI Daily News Report...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    report = generate_report(args.sources, args.max, args.days)
    
    if args.format == "json":
        output = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        output = format_markdown_report(report)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print("=" * 50, file=sys.stderr)
    print(f"✅ Report saved to: {args.output}", file=sys.stderr)
    print(f"📊 Total items: {report['total_items']}", file=sys.stderr)
    for source, count in report.get("summary", {}).items():
        print(f"  - {source}: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()
