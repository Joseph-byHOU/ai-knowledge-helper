#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型解读脚本
从 stdin 接收 JSON {title, summary, url, type, category, ...}
调用 LLM API 生成解读，最后一行输出 {"markdown": "..."}
"""
import json
import sys
import os
import traceback
import urllib.request
import urllib.error

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'baseUrl': '', 'apiKey': '', 'modelName': ''}


def is_anthropic(base_url):
    if not base_url:
        return False
    return 'anthropic' in base_url.lower() or 'claude' in base_url.lower()


def call_openai(messages, api_key, base_url, model):
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    payload = {
        'model': model,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 2048
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode('utf-8')
        result = json.loads(raw)
        return extract_openai_text(result, raw)


def call_anthropic(messages, api_key, base_url, model):
    """尝试 /chat/completions 兼容路径，仅在端点不存在时 fallback 到原生 /messages API"""
    fallback_statuses = {404, 405}
    last_error = None

    # 先尝试 /chat/completions 兼容路径
    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2048
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode('utf-8')
            result = json.loads(raw)
            return extract_openai_text(result, raw)
    except urllib.error.HTTPError as e:
        # 只有端点不存在/不被允许时才走原生 API；其他错误（401/429/500等）直接抛出
        if e.code in fallback_statuses:
            last_error = e
        else:
            raise
    except Exception as e:
        # 网络超时、连接失败等也直接抛出，避免用错误请求继续 fallback
        raise

    # 走原生 /messages API
    if last_error is None:
        raise RuntimeError('未知错误导致进入 Anthropic fallback 路径')
    url = f"{base_url.rstrip('/')}/messages"
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }
    # 提取 system message
    system = ''
    msgs = []
    for m in messages:
        if m['role'] == 'system':
            system = m['content']
        else:
            msgs.append(m)

    payload = {
        'model': model or 'claude-sonnet-4-20250514',
        'max_tokens': 2048,
        'messages': msgs
    }
    if system:
        payload['system'] = system

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode('utf-8')
        result = json.loads(raw)
        return extract_anthropic_text(result, raw)


def extract_openai_text(result, raw_response=''):
    """从 OpenAI 兼容 /chat/completions 响应中安全提取文本内容"""
    choices = result.get('choices')
    if not choices or not isinstance(choices, list):
        raise ValueError(f"响应中没有 choices 字段: {raw_response[:500]}")

    message = choices[0].get('message') if isinstance(choices[0], dict) else None
    if not message:
        raise ValueError(f"响应中没有 message 字段: {raw_response[:500]}")

    if 'content' in message:
        return message['content']

    # 某些中转可能把内容放在 reasoning_content 或其他字段
    for key in ('reasoning_content', 'text'):
        if key in message:
            return message[key]

    raise KeyError(f"'content' (响应 message 中无内容字段): {raw_response[:500]}")


def extract_anthropic_text(result, raw_response=''):
    """从 Anthropic /messages 响应中安全提取文本内容"""
    content = result.get('content')
    if not content:
        raise ValueError(f"Anthropic 响应中没有 content 字段: {raw_response[:500]}")

    # 优先取第一个 text 类型的 content block
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'text' and 'text' in block:
            return block['text']

    # 兼容旧格式 / 异常格式：只要 block 里有 text 字段就取
    for block in content:
        if isinstance(block, dict) and 'text' in block:
            return block['text']

    # 完全没有文本时抛出包含原始响应的异常，方便排查
    raise KeyError(f"'text' (响应中无文本块): {raw_response[:500]}")


def build_prompt(info):
    title = info.get('title', '')
    title_zh = info.get('title_zh', '')
    summary = info.get('summary', '')
    summary_zh = info.get('summary_zh', '')
    url = info.get('url', '')
    item_type = info.get('type', '未知')
    category = info.get('category', '')
    tag = info.get('tag', '')
    source = info.get('source', '')

    display_title = title_zh or title
    display_summary = summary_zh or summary

    system_prompt = """你是 AI 学习助手 Cookie，一只聪明的小蓝猫 🐱💙
请用中文对以下 AI 资讯进行专业解读，包含：
1. **核心要点**：这篇文章/产品/项目在讲什么
2. **为什么重要**：它对 AI 领域有什么影响
3. **技术亮点**：关键的技术创新或突破
4. **我的看法**：Cookie 的视角和评价（可以带点傲娇）

格式要求：
- 使用 Markdown
- 要点清晰，条理分明
- 专业但不枯燥，可以加点猫咪的小表情
- 控制在 500-800 字"""

    user_prompt = f"""## 类型
{item_type}
{f'| 分类: {category}' if category else ''}
{f'| 来源: {source}' if source else ''}
{f'| 标签: {tag}' if tag else ''}

## 标题
{display_title}

## 摘要
{display_summary}

## 原文链接
{url}

请给出专业解读："""

    return system_prompt, user_prompt


def config_guide():
    """当配置缺失时返回友好的引导消息"""
    return json.dumps({
        'markdown': """## 🐱 嗯？还没配置 AI 呢～

想要我给你解读内容，需要先在左侧面板配置以下信息：

1. **接口地址 (baseUrl)** — 你使用的 API 地址
   - 例如 `https://api.openai.com` 或你的中转地址
2. **API Key** — 你的密钥
3. **模型名称** — 例如 `gpt-4o`、`claude-sonnet-4` 等

配置好后保存，再右键点"解读"就可以啦！😊

> 支持 OpenAI 兼容接口和 Anthropic Claude 原生接口
"""
    }, ensure_ascii=False)


def main():
    raw = sys.stdin.read()
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({'markdown': '⚠️ 数据格式错误，无法解读'}, ensure_ascii=False))
        return

    config = load_config()
    base_url = config.get('baseUrl', '').strip()
    api_key = config.get('apiKey', '').strip()
    model_name = config.get('modelName', '').strip()

    if not base_url or not api_key or not model_name:
        print(config_guide())
        return

    try:
        system_prompt, user_prompt = build_prompt(info)
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        if is_anthropic(base_url):
            content = call_anthropic(messages, api_key, base_url, model_name)
        else:
            content = call_openai(messages, api_key, base_url, model_name)

        print(json.dumps({'markdown': content}, ensure_ascii=False))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        print(json.dumps({
            'markdown': f'⚠️ API 调用失败 (HTTP {e.code})\n\n```\n{error_body[:500]}\n```\n\n请检查左侧 AI 配置是否正确。'
        }, ensure_ascii=False))
    except Exception as e:
        # 在终端/控制台留下完整堆栈，方便排查
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({
            'markdown': f'⚠️ 解读出错: {type(e).__name__}: {str(e)}\n\n请检查网络连接和 AI 配置。\n\n如果问题持续，请查看控制台日志获取原始响应详情。'
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()
