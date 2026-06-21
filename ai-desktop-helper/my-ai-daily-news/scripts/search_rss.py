#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search RSS feeds for AI news
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
import feedparser
import requests


DEFAULT_FEEDS = {
    "paperweekly": {
        "name": "PaperWeekly",
        "url": "https://rsshub.app/zhihu/column/paperweekly",
        "enabled": False
    }
}


def parse_date(date_str):
    """Parse various date formats"""
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None


def search_rss_feed(url, name, max_items=3, days_back=7):
    """Search a single RSS feed"""
    
    try:
        feed = feedparser.parse(url)
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        items = []
        for entry in feed.entries[:max_items * 2]:  # Get extra to filter by date
            # Parse date
            pub_date = None
            if hasattr(entry, 'published'):
                pub_date = parse_date(entry.published)
            elif hasattr(entry, 'updated'):
                pub_date = parse_date(entry.updated)
            
            # Check if within date range
            if pub_date and pub_date < cutoff_date:
                continue
            
            item = {
                "type": "资讯",
                "source": name,
                "title": entry.title if hasattr(entry, 'title') else "",
                "summary": entry.summary[:300] if hasattr(entry, 'summary') else 
                          (entry.description[:300] if hasattr(entry, 'description') else ""),
                "url": entry.link if hasattr(entry, 'link') else "",
                "published": entry.published if hasattr(entry, 'published') else ""
            }
            items.append(item)
            
            if len(items) >= max_items:
                break
        
        return items
        
    except Exception as e:
        print(f"Error parsing RSS feed {name}: {e}", file=sys.stderr)
        return []


def search_rss(feeds=None, max_per_feed=3, days_back=7):
    """Search multiple RSS feeds"""
    
    if feeds is None:
        feeds = DEFAULT_FEEDS
    
    all_items = []
    
    for feed_id, feed_info in feeds.items():
        if feed_info.get("enabled", True) and feed_info.get("url"):
            items = search_rss_feed(
                feed_info["url"],
                feed_info.get("name", feed_id),
                max_per_feed,
                days_back
            )
            all_items.extend(items)
    
    return all_items


def format_output(items, format_type="json"):
    """Format output for display"""
    if format_type == "json":
        return json.dumps(items, ensure_ascii=False, indent=2)
    elif format_type == "markdown":
        lines = ["## 📰 RSS News\n"]
        for item in items:
            lines.append(f"**{item['title']}**")
            lines.append(f"> {item['summary'][:200]}...")
            lines.append(f"> Source: {item['source']}")
            lines.append(f"> 🔗 [Read More]({item['url']})")
            lines.append("")
        return "\n".join(lines)
    else:
        return str(items)


def main():
    parser = argparse.ArgumentParser(description="Search RSS feeds for AI news")
    parser.add_argument("--url", help="Custom RSS feed URL")
    parser.add_argument("--name", default="Custom Feed", help="Feed name")
    parser.add_argument("--max", type=int, default=3,
                        help="Max items per feed (default: 3)")
    parser.add_argument("--days", type=int, default=7,
                        help="Days back to search (default: 7)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    if args.url:
        # Single custom feed
        feeds = {
            "custom": {
                "name": args.name,
                "url": args.url,
                "enabled": True
            }
        }
    else:
        feeds = DEFAULT_FEEDS
    
    items = search_rss(feeds, args.max, args.days)
    
    output = format_output(items, args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Saved {len(items)} items to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
