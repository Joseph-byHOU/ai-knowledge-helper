#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速获取arXiv论文"""

import requests
import json
from datetime import datetime
from xml.etree import ElementTree as ET

def fetch_arxiv():
    print('正在获取arXiv论文...')
    
    base_url = 'http://export.arxiv.org/api/query'
    params = {
        'search_query': 'cat:cs.CL OR cat:cs.LG OR cat:cs.AI',
        'start': 0,
        'max_results': 15,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        print(f'状态码: {response.status_code}')
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip()
                summary = entry.find('atom:summary', ns).text.strip()
                url = entry.find('atom:id', ns).text.strip()
                published = entry.find('atom:published', ns).text[:10]
                cat = entry.find('atom:category', ns).get('term', 'cs.CL')
                
                papers.append({
                    'type': '论文',
                    'tag': '[论文]',
                    'title': title,
                    'summary': summary[:150] + '...' if len(summary) > 150 else summary,
                    'url': url,
                    'published': published,
                    'category': cat
                })
            
            print(f'获取到 {len(papers)} 篇论文')
            
            # 保存
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(papers),
                'items': papers
            }
            
            with open('data/daily_news_2026-04-08.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print('数据已保存')
            
            # 显示
            for i, p in enumerate(papers[:5], 1):
                print(f"{i}. [{p['published']}] {p['title'][:50]}...")
                
            return papers
    except Exception as e:
        print(f'错误: {e}')
    
    return []

if __name__ == '__main__':
    fetch_arxiv()
