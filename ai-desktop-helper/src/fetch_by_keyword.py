#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词在线抓取脚本
从命令行参数接收关键词，搜索 arXiv API，
无结果时 fallback 到 HuggingFace Papers，
结果增量合并到 data/daily_news.json，
最后一行输出 {"items": [...]}
"""
import sys
import json
import time
import os
import re
import urllib.request
import urllib.parse
import urllib.error
import html
from xml.etree import ElementTree as ET

def get_data_file():
    """兼容在 Electron 内部运行时以项目根目录为 cwd，以及直接运行时脚本所在目录"""
    cwd_data = os.path.join(os.getcwd(), 'data', 'daily_news.json')
    if os.path.exists(os.path.dirname(cwd_data)) or os.getcwd().endswith('ai-desktop-helper'):
        return cwd_data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'daily_news.json')


DATA_FILE = get_data_file()


def fetch_arxiv(keyword, retries=3):
    """arXiv API 全文检索"""
    base_url = 'http://export.arxiv.org/api/query'
    escaped = urllib.parse.quote(f'all:"{keyword}"')
    query = f'search_query={escaped}&start=0&max_results=10&sortBy=relevance&sortOrder=descending'

    for attempt in range(1, retries + 1):
        try:
            url = f'{base_url}?{query}'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'ai-desktop-helper/0.1'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_data = resp.read().decode('utf-8')

            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                arxiv_id = entry.find('atom:id', ns)
                published = entry.find('atom:published', ns)
                categories = entry.findall('atom:category', ns)

                title_text = html.unescape(title.text.strip().replace('\n', ' ')) if title is not None else ''
                summary_text = html.unescape(summary.text.strip().replace('\n', ' ')) if summary is not None else ''
                url_text = arxiv_id.text.strip() if arxiv_id is not None else ''
                pub_date = published.text[:10] if published is not None else ''
                cat = categories[0].get('term', 'cs.CL') if categories else 'cs.CL'

                papers.append({
                    'type': '论文',
                    'tag': f'[论文·{cat}]',
                    'title': title_text[:200],
                    'summary': summary_text[:300] + '...' if len(summary_text) > 300 else summary_text,
                    'url': url_text,
                    'published': pub_date,
                    'category': cat,
                    'source': 'arxiv',
                    'keyword': keyword
                })

            if papers:
                return papers
            print(f'[arxiv] 尝试 {attempt}: 无结果，重试...')
            time.sleep(2 * attempt)

        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = 4 * attempt
                print(f'[arxiv] HTTP {e.code}, 等待 {wait}s...')
                time.sleep(wait)
                continue
            print(f'[arxiv] HTTP {e.code}: {str(e)[:100]}')
            break
        except Exception as e:
            print(f'[arxiv] 错误: {str(e)[:100]}')
            time.sleep(2 * attempt)

    return []


def fetch_huggingface_papers(keyword, retries=2):
    """HuggingFace Papers 搜索"""
    for attempt in range(1, retries + 1):
        try:
            url = f'https://huggingface.co/api/daily_papers?limit=20'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ai-desktop-helper/0.1'
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                papers_data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f'[huggingface] 错误: {str(e)[:100]}')
            time.sleep(2 * attempt)
            continue

        kw_lower = keyword.lower()
        matched = []
        for paper in papers_data:
            title = paper.get('title', '') or ''
            if kw_lower in title.lower():
                paper_id = paper.get('paper', {}).get('id', '')
                url = f'https://arxiv.org/abs/{paper_id}' if paper_id else ''
                summary = paper.get('summary', '') or ''
                matched.append({
                    'type': '论文',
                    'tag': '[论文·HuggingFace]',
                    'title': title,
                    'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                    'url': url,
                    'published': paper.get('publishedAt', '')[:10] if paper.get('publishedAt') else '',
                    'category': '',
                    'source': 'huggingface',
                    'keyword': keyword
                })

        if matched:
            return matched
        print(f'[huggingface] 尝试 {attempt}: 无匹配结果')
        break

    return []


def merge_into_daily(new_items):
    """增量去重合并到 daily_news.json"""
    existing = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'items' in data:
                existing = data['items']
            elif isinstance(data, list):
                existing = data
        except Exception:
            existing = []

    seen_urls = set()
    for item in existing:
        if item.get('url'):
            seen_urls.add(item['url'])

    added = 0
    for item in new_items:
        if item.get('url') and item['url'] not in seen_urls:
            existing.append(item)
            seen_urls.add(item['url'])
            added += 1

    from datetime import datetime
    now = datetime.now()
    output = {
        'date': now.strftime('%Y-%m-%d'),
        'updated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(existing),
        'items': existing
    }

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'[merge] 新增 {added} 条, 总计 {len(existing)} 条')


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': '请提供搜索关键词'}, ensure_ascii=False))
        sys.exit(1)

    keyword = sys.argv[1].strip()
    print(f'🔍 搜索关键词: {keyword}')
    print('=' * 40)

    # 第一阶段：arXiv
    papers = fetch_arxiv(keyword)
    if papers:
        print(f'[arxiv] 找到 {len(papers)} 篇论文')
    else:
        print('[arxiv] 无结果，尝试 HuggingFace Papers...')
        papers = fetch_huggingface_papers(keyword)
        if papers:
            print(f'[huggingface] 找到 {len(papers)} 篇论文')
        else:
            print('[huggingface] 也无结果')

    if not papers:
        print(json.dumps({'items': [], 'total': 0, 'keyword': keyword}, ensure_ascii=False))
        return

    # 合并到 daily_news.json
    merge_into_daily(papers)

    # 最后一行输出 JSON
    result = {'items': papers, 'total': len(papers), 'keyword': keyword}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
