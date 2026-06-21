#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Hugging Face for trending AI models
"""

import argparse
import json
import sys
import requests


def search_huggingface(max_results=5, task=None):
    """Search Hugging Face for trending models"""
    
    # Hugging Face API endpoint
    url = "https://huggingface.co/api/models"
    
    params = {
        "limit": max_results,
        "sort": "downloads",
        "direction": -1,  # descending
        "full": "true"
    }
    
    if task:
        params["filter"] = task
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        models = response.json()
        
        results = []
        for model in models[:max_results]:
            result = {
                "type": "模型",
                "source": "Hugging Face",
                "title": model.get("modelId", ""),
                "summary": model.get("cardData", {}).get("description", "")[:200] if model.get("cardData") else "",
                "url": f"https://huggingface.co/{model.get('modelId', '')}",
                "downloads": model.get("downloads", 0),
                "likes": model.get("likes", 0),
                "tags": model.get("tags", []),
                "pipeline_tag": model.get("pipeline_tag", "")
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        print(f"Error fetching Hugging Face: {e}", file=sys.stderr)
        return []


def format_output(models, format_type="json"):
    """Format output for display"""
    if format_type == "json":
        return json.dumps(models, ensure_ascii=False, indent=2)
    elif format_type == "markdown":
        lines = ["## 🤗 Hugging Face Trending Models\n"]
        for model in models:
            lines.append(f"**{model['title']}**")
            lines.append(f"> {model['summary'][:150]}..." if model['summary'] else "> No description")
            lines.append(f"> ⬇️ {model['downloads']:,} downloads | ❤️ {model['likes']:,} likes")
            lines.append(f"> 🏷️ {', '.join(model['tags'][:3])}")
            lines.append(f"> 🔗 [View Model]({model['url']})")
            lines.append("")
        return "\n".join(lines)
    else:
        return str(models)


def main():
    parser = argparse.ArgumentParser(description="Search Hugging Face for trending models")
    parser.add_argument("--max", type=int, default=5,
                        help="Maximum models to fetch (default: 5)")
    parser.add_argument("--task", help="Filter by task (e.g., text-generation, image-classification)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    models = search_huggingface(args.max, args.task)
    
    output = format_output(models, args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Saved {len(models)} models to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
