#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Product Hunt for AI products
"""

import argparse
import json
import sys
import requests
from datetime import datetime


def search_producthunt(max_results=5):
    """Search Product Hunt for AI products"""
    
    # Product Hunt API requires authentication
    # Using RSS feed as alternative
    url = "https://www.producthunt.com/feed?category=artificial-intelligence"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse RSS
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}
        
        products = []
        for item in root.findall('.//item')[:max_results]:
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pub_date = item.find('pubDate')
            
            product = {
                "type": "产品",
                "source": "Product Hunt",
                "title": title.text if title is not None else "",
                "summary": description.text[:200] if description is not None and description.text else "",
                "url": link.text if link is not None else "",
                "published": pub_date.text if pub_date is not None else ""
            }
            products.append(product)
        
        return products
        
    except Exception as e:
        print(f"Error fetching Product Hunt: {e}", file=sys.stderr)
        return []


def format_output(products, format_type="json"):
    """Format output for display"""
    if format_type == "json":
        return json.dumps(products, ensure_ascii=False, indent=2)
    elif format_type == "markdown":
        lines = ["## 🚀 Product Hunt AI Products\n"]
        for product in products:
            lines.append(f"**{product['title']}**")
            lines.append(f"> {product['summary']}")
            lines.append(f"> 🔗 [View on Product Hunt]({product['url']})")
            lines.append("")
        return "\n".join(lines)
    else:
        return str(products)


def main():
    parser = argparse.ArgumentParser(description="Search Product Hunt for AI products")
    parser.add_argument("--max", type=int, default=5,
                        help="Maximum products to fetch (default: 5)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    products = search_producthunt(args.max)
    
    output = format_output(products, args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Saved {len(products)} products to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
