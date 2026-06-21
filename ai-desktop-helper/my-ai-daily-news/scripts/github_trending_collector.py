#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 热门开源项目收集脚本
获取今日热度增速最快的开源项目
"""

import json
import logging
import re
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse

from browser_fallback import try_with_fallback

logger = logging.getLogger(__name__)


def fetch_github_trending_daily(max_results=3):
    """
    获取 GitHub 今日热门项目（按 star 增速排序）
    
    使用 GitHub Search API 搜索最近创建的、star 增长快的项目
    返回项目列表，包含名称、链接、README 概要
    """
    projects = []
    
    try:
        logger.info("正在获取 GitHub 热门项目...")
        
        # 使用更简单的方式：搜索最近一周创建的、高 star 项目
        # 按 star 数排序
        url = "https://api.github.com/search/repositories"
        
        # 构建查询 - 使用 created 而不是 pushed，避免日期格式问题
        created_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        query = f"stars:>100 created:>{created_date}"
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results * 2
        }
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Daily-News-Bot"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        # 获取每个项目的详细信息
        for item in items[:max_results]:
            try:
                project = process_github_project(item)
                if project:
                    projects.append(project)
                    
                if len(projects) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"处理项目 {item.get('full_name')} 失败: {e}")
                continue
        
        logger.info(f"GitHub 热门项目获取完成: {len(projects)}条")
        return projects[:max_results]
        
    except Exception as e:
        logger.error(f"获取 GitHub 热门项目失败: {e}")
        return projects


def process_github_project(item):
    """
    处理 GitHub API 返回的项目数据
    """
    full_name = item.get("full_name", "")
    html_url = item.get("html_url", "")
    description = item.get("description", "") or "暂无描述"
    stars = item.get("stargazers_count", 0)
    forks = item.get("forks_count", 0)
    language = item.get("language", "Unknown") or "Unknown"
    
    # 获取 README 概要
    readme_summary = fetch_readme_summary(full_name)
    
    # 构建项目信息
    project = {
        "type": "开源项目",
        "tag": "[GitHub]",
        "title": full_name,
        "name": item.get("name", ""),
        "owner": item.get("owner", {}).get("login", ""),
        "summary": description,
        "readme_summary": readme_summary,
        "url": html_url,
        "stars": stars,
        "forks": forks,
        "language": language,
        "published": datetime.now().strftime('%Y-%m-%d'),
        "category": "GitHub Trending"
    }
    
    return project


def fetch_readme_summary(repo_full_name):
    """
    获取项目的 README 内容概要
    
    尝试获取 README.md 内容并提取前200字作为概要
    """
    try:
        # 尝试获取 README
        url = f"https://api.github.com/repos/{repo_full_name}/readme"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Daily-News-Bot"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            
            # Base64 解码
            import base64
            try:
                readme_content = base64.b64decode(content).decode('utf-8', errors='ignore')
                
                # 清理 markdown 格式，提取纯文本
                readme_text = clean_markdown(readme_content)
                
                # 取前 300 字符作为概要
                summary = readme_text[:300].strip()
                if len(readme_text) > 300:
                    summary += "..."
                
                return summary
            except Exception as e:
                logger.debug(f"解码 README 失败: {e}")
        
        return "暂无 README 信息"
        
    except Exception as e:
        logger.debug(f"获取 README 失败 {repo_full_name}: {e}")
        return "暂无 README 信息"


def clean_markdown(text):
    """
    清理 markdown 格式，提取纯文本
    """
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', ' ', text)
    text = re.sub(r'`[^`]*`', ' ', text)
    
    # 移除图片
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)
    
    # 移除链接，保留文本
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 移除标题标记
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # 移除强调标记
    text = re.sub(r'\*\*|__|\*|_', '', text)
    
    # 移除表格分隔线
    text = re.sub(r'\|[-:]+\|', ' ', text)
    text = re.sub(r'\|', ' ', text)
    
    # 合并空白
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def fetch_trending_from_scraping(max_results=3):
    """
    备用方案：通过网页抓取获取 GitHub Trending
    当 API 限制或失败时使用
    """
    projects = []
    
    try:
        from playwright.sync_api import sync_playwright
        
        logger.info("使用浏览器抓取 GitHub Trending...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 访问 GitHub Trending 页面
            page.goto("https://github.com/trending", timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # 等待项目列表加载
            page.wait_for_selector("article.Box-row", timeout=10000)
            
            # 提取项目信息
            items = page.query_selector_all("article.Box-row")[:max_results]
            
            for item in items:
                try:
                    # 获取项目名称
                    name_elem = item.query_selector("h2 a")
                    if not name_elem:
                        continue
                    
                    full_name = name_elem.inner_text().strip().replace(" ", "").replace("\n", "")
                    href = name_elem.get_attribute("href")
                    url = f"https://github.com{href}"
                    
                    # 获取描述
                    desc_elem = item.query_selector("p.col-9")
                    description = desc_elem.inner_text().strip() if desc_elem else "暂无描述"
                    
                    # 获取语言
                    lang_elem = item.query_selector("[itemprop='programmingLanguage']")
                    language = lang_elem.inner_text().strip() if lang_elem else "Unknown"
                    
                    # 获取 stars
                    stars_elem = item.query_selector("a.Link--muted[href$='/stargazers']")
                    stars_text = stars_elem.inner_text().strip() if stars_elem else "0"
                    stars = parse_count(stars_text)
                    
                    # 获取 README 概要
                    readme_summary = fetch_readme_summary(full_name)
                    
                    project = {
                        "type": "开源项目",
                        "tag": "[GitHub]",
                        "title": full_name,
                        "name": full_name.split("/")[-1] if "/" in full_name else full_name,
                        "owner": full_name.split("/")[0] if "/" in full_name else "",
                        "summary": description,
                        "readme_summary": readme_summary,
                        "url": url,
                        "stars": stars,
                        "forks": 0,
                        "language": language,
                        "published": datetime.now().strftime('%Y-%m-%d'),
                        "category": "GitHub Trending"
                    }
                    
                    projects.append(project)
                    
                except Exception as e:
                    logger.warning(f"处理 trending 项目失败: {e}")
                    continue
            
            browser.close()
        
        logger.info(f"浏览器抓取完成: {len(projects)}条")
        return projects
        
    except Exception as e:
        logger.error(f"浏览器抓取 GitHub Trending 失败: {e}")
        return projects


def parse_count(count_text):
    """
    解析带单位的数字，如 "1.2k" -> 1200
    """
    count_text = count_text.strip().lower()
    
    if 'k' in count_text:
        return int(float(count_text.replace('k', '')) * 1000)
    elif 'm' in count_text:
        return int(float(count_text.replace('m', '')) * 1000000)
    else:
        try:
            return int(count_text.replace(',', ''))
        except:
            return 0


def fetch_github_trending(max_results=3):
    """
    获取 GitHub 热门项目（主入口）
    优先使用 API，失败时使用浏览器抓取
    """
    # 先尝试 API 方式
    projects = fetch_github_trending_daily(max_results)
    
    # 如果 API 方式获取不足，尝试浏览器抓取
    if len(projects) < max_results:
        logger.info(f"API 获取不足 ({len(projects)}/{max_results})，尝试浏览器抓取...")
        scraping_projects = fetch_trending_from_scraping(max_results - len(projects))
        
        # 合并结果，去重
        existing_urls = {p["url"] for p in projects}
        for p in scraping_projects:
            if p["url"] not in existing_urls:
                projects.append(p)
    
    return projects[:max_results]


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    projects = fetch_github_trending(3)
    print(json.dumps(projects, ensure_ascii=False, indent=2))