#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search arXiv for latest AI/ML papers
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from urllib.parse import urlencode
import requests
import xml.etree.ElementTree as ET


def search_arxiv(categories=None, max_results=5, days_back=1):
    """Search arXiv for papers in specified categories"""
    if categories is None:
        categories = ["cs.CL", "cs.LG", "cs.AI"]
    
    # Build query
    cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # arXiv API parameters
    params = {
        "search_query": cat_query,
        "start": 0,
        "max_results": max_results * len(categories),
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    url = f"http://export.arxiv.org/api/query?{urlencode(params)}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Define namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            paper = {
                "type": "论文",
                "source": "arXiv",
                "title": entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else "",
                "summary": entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else "",
                "url": entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else "",
                "published": entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else "",
                "authors": [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns) if author.find('atom:name', ns) is not None],
                "categories": [cat.get('term') for cat in entry.findall('atom:category', ns)]
            }
            
            # Convert arXiv ID to PDF link
            if paper["url"]:
                arxiv_id = paper["url"].split('/')[-1]
                paper["pdf_url"] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            papers.append(paper)
        
        # Limit results per category
        return papers[:max_results]
        
    except Exception as e:
        print(f"Error fetching arXiv: {e}", file=sys.stderr)
        return []


def format_output(papers, format_type="json"):
    """Format output for display"""
    if format_type == "json":
        return json.dumps(papers, ensure_ascii=False, indent=2)
    elif format_type == "markdown":
        lines = ["## 📚 arXiv Papers\n"]
        for paper in papers:
            lines.append(f"**{paper['title']}**")
            lines.append(f"> {paper['summary'][:200]}...")
            lines.append(f"> Authors: {', '.join(paper['authors'][:3])}")
            lines.append(f"> 🔗 [arXiv]({paper['url']}) | [PDF]({paper.get('pdf_url', '')})")
            lines.append("")
        return "\n".join(lines)
    else:
        return str(papers)


def main():
    parser = argparse.ArgumentParser(description="Search arXiv for AI/ML papers")
    parser.add_argument("--category", nargs="+", default=["cs.CL", "cs.LG", "cs.AI"],
                        help="arXiv categories (default: cs.CL cs.LG cs.AI)")
    parser.add_argument("--max", type=int, default=5,
                        help="Maximum papers per category (default: 5)")
    parser.add_argument("--days", type=int, default=1,
                        help="Days back to search (default: 1)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    papers = search_arxiv(args.category, args.max, args.days)
    
    output = format_output(papers, args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Saved {len(papers)} papers to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
