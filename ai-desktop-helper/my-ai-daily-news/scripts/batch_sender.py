#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分批发送AI日报到飞书
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

def load_news_data(data_path="data/daily_news.json"):
    """加载新闻数据"""
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"数据文件未找到: {data_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"数据文件格式错误: {e}")
        return None

def batch_items(items, batch_size=5):
    """将项目分批"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def format_items_batch(items, batch_num, total_batches, date_str):
    """格式化一批项目为飞书消息"""
    lines = []
    lines.append(f"📰 **AI日报 - {date_str}** (第 {batch_num}/{total_batches} 批)")
    lines.append("")
    
    for item in items:
        tag = item.get('tag', '[资讯]')
        title = item.get('title', '无标题')
        summary = item.get('summary', '')
        url = item.get('url', '')
        item_type = item.get('type', '资讯')
        
        # 限制摘要长度
        if summary:
            summary = summary[:150] + "..." if len(summary) > 150 else summary
        
        lines.append(f"**{tag} {title}**")
        if summary:
            lines.append(f"> {summary}")
        if url:
            lines.append(f"> 🔗 {url}")
        lines.append("")
    
    return '\n'.join(lines)

def main():
    """主入口"""
    # 加载新闻数据
    data_path = script_dir / "data" / "daily_news.json"
    news_data = load_news_data(data_path)
    
    if not news_data:
        print("没有新闻数据")
        return 1
    
    date_str = news_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    items = news_data.get('items', [])
    
    if not items:
        print("新闻列表为空")
        return 1
    
    print(f"加载了 {len(items)} 条新闻，日期: {date_str}")
    
    # 分批，每批5条
    batches = list(batch_items(items, 5))
    total_batches = len(batches)
    
    print(f"将分为 {total_batches} 批发送")
    
    # 输出每批内容到文件，供外部读取
    output_dir = script_dir / "output_batches"
    output_dir.mkdir(exist_ok=True)
    
    for i, batch in enumerate(batches, 1):
        content = format_items_batch(batch, i, total_batches, date_str)
        output_file = output_dir / f"batch_{i:02d}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已生成批次 {i}: {output_file}")
    
    print(f"\n批次文件已保存到: {output_dir}")
    return 0

if __name__ == "__main__":
    exit(main())
