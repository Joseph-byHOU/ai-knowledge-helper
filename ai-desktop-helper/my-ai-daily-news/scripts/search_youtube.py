#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search YouTube for AI creator videos
"""

import argparse
import json
import sys
import subprocess
from datetime import datetime, timedelta


# YouTube channel mappings
YOUTUBE_CREATORS = {
    "andrew_ng": "UCcIXc5mJsHVYTZR1maL5l9w",  # 吴恩达
    "matt_wolfe": "UCYhDJOrVbGznVMww_T8Z6mw",  # Matt Wolfe
    "ai_explained": "UCV7H2eCzUV7y0XmRMPfYRCg",  # AI Explained
    "ai_with_oliver": "UCcCpxP1q3r2p4xJhQY10mSg",  # AI with Oliver
    "greg_isenberg": "UC8VCiL8JxQkzD0Z9U6pV1Fg",  # Greg Isenberg
    "fireship": "UCsBjURrPoezykLs9EqgamOA",  # Fireship
}


def search_youtube_channel(channel_id, max_results=3, days_back=7):
    """Search YouTube channel for recent videos"""
    
    try:
        # Use yt-dlp to fetch channel videos
        # Get videos from the last N days
        date_after = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--playlist-end", str(max_results),
            "--dateafter", date_after,
            "--dump-json",
            f"https://www.youtube.com/channel/{channel_id}/videos"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video = json.loads(line)
                    videos.append({
                        "type": "视频",
                        "source": "YouTube",
                        "title": video.get("title", ""),
                        "summary": video.get("description", "")[:200] if video.get("description") else "",
                        "url": f"https://youtube.com/watch?v={video.get('id', '')}",
                        "published": video.get("upload_date", ""),
                        "duration": video.get("duration_string", ""),
                        "view_count": video.get("view_count", 0)
                    })
                except json.JSONDecodeError:
                    continue
        
        return videos
        
    except subprocess.TimeoutExpired:
        print("Timeout fetching YouTube videos", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("yt-dlp not found. Install with: pip install yt-dlp", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error fetching YouTube: {e}", file=sys.stderr)
        return []


def search_youtube(creators=None, max_per_creator=2, days_back=7):
    """Search multiple YouTube creators"""
    
    if creators is None:
        creators = ["andrew_ng", "matt_wolfe"]
    
    all_videos = []
    
    for creator in creators:
        if creator in YOUTUBE_CREATORS:
            channel_id = YOUTUBE_CREATORS[creator]
            videos = search_youtube_channel(channel_id, max_per_creator, days_back)
            all_videos.extend(videos)
    
    return all_videos


def format_output(videos, format_type="json"):
    """Format output for display"""
    if format_type == "json":
        return json.dumps(videos, ensure_ascii=False, indent=2)
    elif format_type == "markdown":
        lines = ["## 📺 YouTube AI Videos\n"]
        for video in videos:
            lines.append(f"**{video['title']}**")
            lines.append(f"> {video['summary'][:150]}..." if video['summary'] else "")
            lines.append(f"> 👀 {video.get('view_count', 0):,} views | ⏱️ {video.get('duration', 'N/A')}")
            lines.append(f"> 🔗 [Watch Video]({video['url']})")
            lines.append("")
        return "\n".join(lines)
    else:
        return str(videos)


def main():
    parser = argparse.ArgumentParser(description="Search YouTube for AI creator videos")
    parser.add_argument("--creator", nargs="+", 
                        choices=list(YOUTUBE_CREATORS.keys()),
                        default=["andrew_ng", "matt_wolfe"],
                        help="YouTube creators to search")
    parser.add_argument("--max", type=int, default=2,
                        help="Max videos per creator (default: 2)")
    parser.add_argument("--days", type=int, default=7,
                        help="Days back to search (default: 7)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    videos = search_youtube(args.creator, args.max, args.days)
    
    output = format_output(videos, args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Saved {len(videos)} videos to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
