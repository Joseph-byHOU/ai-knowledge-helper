#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Verge AI 栏目收集模块
收集 The Verge 人工智能相关新闻
"""

import json
import logging
import re
from datetime import datetime, timedelta

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# The Verge AI RSS 地址 (尝试多种可能的RSS地址)
THE_VERGE_AI_RSS_URLS = [
    "https://www.theverge.com/ai-artificial-intelligence/rss",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.theverge.com/rss/frontpage",
    "https://www.theverge.com/rss/index.xml"
]
THE_VERGE_AI_URL = "https://www.theverge.com/ai-artificial-intelligence"


def fetch_verge_ai_news(max_items=5, days_back=1):
    """
    获取 The Verge AI 栏目新闻
    
    先尝试RSS，如果失败则使用网页抓取
    
    Args:
        max_items: 最大返回条目数
        days_back: 回溯天数
    
    Returns:
        list: 格式化的新闻条目列表
    """
    items = []
    
    # 先尝试 RSS
    for rss_url in THE_VERGE_AI_RSS_URLS:
        try:
            logger.info(f"正在尝试 The Verge RSS: {rss_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                if feed.entries:
                    logger.info(f"RSS 成功: {rss_url}")
                    items = _parse_verge_feed(feed, max_items, days_back)
                    if items:
                        return items
                        
        except Exception as e:
            logger.warning(f"RSS 尝试失败 {rss_url}: {e}")
            continue
    
    # RSS 都失败了，使用网页抓取
    logger.info("RSS 获取失败，尝试网页抓取...")
    return _fetch_verge_from_web(max_items, days_back)


def _parse_verge_feed(feed, max_items, days_back):
    """解析 The Verge RSS Feed"""
    items = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    for entry in feed.entries[:max_items * 2]:
        try:
            # 解析发布时间（优先使用 feedparser 解析好的时间元组）
            published = None
            published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
            if published_parsed:
                try:
                    published = datetime(*published_parsed[:6])
                except Exception:
                    published = None

            # 检查时间范围（feedparser 返回的是 UTC 时间）
            if published and published.replace(tzinfo=None) < cutoff_date:
                continue
            
            # 提取内容摘要
            summary = entry.get('summary', entry.get('description', ''))
            if summary:
                soup = BeautifulSoup(summary, 'html.parser')
                summary = soup.get_text()
                summary = re.sub(r'\s+', ' ', summary).strip()
                summary = summary[:250] + "..." if len(summary) > 250 else summary
            else:
                summary = "The Verge AI 最新报道"
            
            # 获取作者
            author = entry.get('author', '')
            if not author:
                author = 'The Verge'
            
            # 构建条目
            item = {
                "type": "资讯",
                "tag": "[资讯·The Verge]",
                "title": entry.get('title', '无标题').strip(),
                "summary": summary,
                "url": entry.get('link', ''),
                "published": published.strftime('%Y-%m-%d') if published else datetime.now().strftime('%Y-%m-%d'),
                "source": "The Verge",
                "author": author
            }
            
            items.append(item)
            
            if len(items) >= max_items:
                break
                
        except Exception as e:
            logger.warning(f"解析 The Verge 条目失败: {e}")
            continue
    
    logger.info(f"The Verge AI (RSS) 获取完成: {len(items)}条")
    return items[:max_items]


def _fetch_verge_from_web(max_items=5, days_back=1):
    """从 The Verge 网页直接抓取"""
    items = []
    
    try:
        logger.info("正在从 The Verge 网页抓取...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(THE_VERGE_AI_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # The Verge 的文章通常包含在特定结构中
        # 查找文章卡片
        articles = soup.find_all('div', class_=re.compile(r'content-hub-|duet--content--|relative'))
        
        # 如果没有找到，尝试其他选择器
        if not articles:
            articles = soup.find_all('article')
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for article in articles[:max_items * 2]:
            try:
                # 提取标题
                title_el = article.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|headline'))
                if not title_el:
                    title_el = article.find('a', href=True)
                
                if not title_el:
                    continue
                
                title = title_el.get_text().strip()
                if not title or len(title) < 10:
                    continue
                
                # 提取链接
                link = ''
                if title_el.name == 'a':
                    link = title_el.get('href', '')
                else:
                    link_el = title_el.find_parent('a') or article.find('a', href=True)
                    if link_el:
                        link = link_el.get('href', '')
                
                # 补全链接
                if link and not link.startswith('http'):
                    link = 'https://www.theverge.com' + link
                
                # 提取摘要/描述
                summary = ''
                desc_el = article.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt'))
                if desc_el:
                    summary = desc_el.get_text().strip()
                
                if not summary:
                    # 尝试从其他元素获取
                    text_content = article.get_text()
                    # 移除标题后作为摘要
                    summary = text_content.replace(title, '').strip()[:200]
                
                # 提取日期
                date_el = article.find('time')
                published = datetime.now()
                if date_el:
                    date_str = date_el.get('datetime', '') or date_el.get_text()
                    try:
                        if date_str:
                            # 尝试解析日期
                            for fmt in ['%Y-%m-%d', '%b %d, %Y', '%B %d, %Y']:
                                try:
                                    published = datetime.strptime(date_str.strip(), fmt)
                                    break
                                except:
                                    continue
                    except:
                        pass
                
                # 检查时间范围
                if published < cutoff_date:
                    continue
                
                # 提取作者
                author = 'The Verge'
                author_el = article.find(['span', 'a'], class_=re.compile(r'author|byline'))
                if author_el:
                    author = author_el.get_text().strip()
                
                # 构建条目
                item = {
                    "type": "资讯",
                    "tag": "[资讯·The Verge]",
                    "title": title,
                    "summary": summary[:250] if len(summary) > 250 else summary,
                    "url": link,
                    "published": published.strftime('%Y-%m-%d'),
                    "source": "The Verge",
                    "author": author
                }
                
                items.append(item)
                
                if len(items) >= max_items:
                    break
                    
            except Exception as e:
                logger.warning(f"解析 The Verge 文章失败: {e}")
                continue
        
        logger.info(f"The Verge AI (Web) 获取完成: {len(items)}条")
        
    except Exception as e:
        logger.error(f"从 The Verge 网页抓取失败: {e}")
    
    return items[:max_items]


def fallback_verge_ai_news(max_items=5, days_back=1):
    """
    使用浏览器备选方案抓取 The Verge AI
    当 RSS 获取失败时使用
    """
    items = []
    
    try:
        from browser_fallback import scrape_with_playwright
        
        extraction_config = {
            'wait_for_selector': '.duet--content--content-body, article',
            'selectors': {
                'item_selector': '.duet--content--content-body > div, article .max-w-content-block',
                'title': 'h2 a, h3 a',
                'summary': 'p',
                'date': 'time'
            },
            'max_items': max_items
        }
        
        results = scrape_with_playwright(THE_VERGE_AI_URL, extraction_config)
        
        for item in results:
            item.update({
                'type': '资讯',
                'tag': '[资讯·The Verge]',
                'source': 'theverge-browser'
            })
            items.append(item)
            
        logger.info(f"The Verge AI (浏览器备选) 获取完成: {len(items)}条")
        
    except Exception as e:
        logger.error(f"The Verge AI 浏览器备选失败: {e}")
    
    return items[:max_items]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("测试 The Verge AI 收集器...")
    
    items = fetch_verge_ai_news(max_items=3, days_back=3)
    
    print(f"\n获取到 {len(items)} 条内容:\n")
    for item in items:
        print(f"[{item['tag']}] {item['title']}")
        print(f"作者: {item.get('author', 'N/A')}")
        print(f"发布时间: {item['published']}")
        print(f"摘要: {item['summary'][:100]}...")
        print(f"链接: {item['url']}")
        print("-" * 50)
