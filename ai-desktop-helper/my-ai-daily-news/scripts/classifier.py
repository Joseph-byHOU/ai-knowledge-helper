#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻智能分类引擎
根据标题和摘要自动归类到大模型/Agent/融资/安全/应用/开源
"""

import re
import logging

logger = logging.getLogger(__name__)

# 分类关键词规则（中英文）
CLASSIFICATION_RULES = {
    "大模型": {
        "icon": "🧠",
        "keywords_en": [
            r'\bllm\b', r'\blarge\s*language\s*model', r'\bfoundation\s*model',
            r'\bgpt[-\s]?\d', r'\bclaude\b', r'\bgemini\b', r'\bllama\b', r'\bmistral\b',
            r'\btransformer', r'\bpretrain', r'\bpre-train', r'\bfine.?tun',
            r'\btokenizer', r'\bcontext\s*window', r'\bparameter\s*[es]?\b',
            r'\btraining\s*recipe', r'\bscaling\s*law', r'\bemergent\s*abilit',
            r'\breasoning', r'\breasoning\s*model', r'\bchain.?of.?thought',
            r'\bmultimodal\b', r'\blanguage\s*model', r'\btext.?to.?text',
            r'\binstruct', r'\balignment\s*tuning', r'\brlhf\b', r'\bdpo\b',
            r'\bgrokking', r'\bmoe\b', r'\bmixture.?of.?experts',
        ],
        "keywords_zh": [
            r'大模型', r'语言模型', r'预训练', r'微调', r'参数',
            r'推理模型', r'思维链', r'多模态', r'基础模型', r'对齐',
            r'强化学习', r'专家混合', r'涌现', r'扩展定律',
        ]
    },
    "Agent": {
        "icon": "🤖",
        "keywords_en": [
            r'\bagent', r'\bautonomous', r'\btool\s*use', r'\btool.?calling',
            r'\bfunction.?call', r'\bworkflow', r'\borchestrat',
            r'\bmulti.?agent', r'\bagentic', r'\bplanning',
            r'\breact\b', r'\breflexion', r'\bcode\s*generat',
            r'\bself.?operat', r'\bcomputer\s*use',
            r'\bbrowser\s*agent', r'\bembodiment', r'\brobot',
        ],
        "keywords_zh": [
            r'代理', r'自主', r'工具调用', r'工作流', r'编排',
            r'多代理', r'规划', r'代码生成', r'自动化',
        ]
    },
    "融资/商业": {
        "icon": "💰",
        "keywords_en": [
            r'\bfunding\b', r'\bacquisition', r'\bacqui', r'\bipo\b',
            r'\binvestment', r'\binvestor', r'\bventure\b', r'\bstartup',
            r'\brevenue\b', r'\bprofit', r'\bvaluation', r'\bexit\b',
            r'\bmerger', r'\bpartnership', r'\bcollaborat',
            r'\benterprise', r'\bcommercial', r'\bmonetiz',
            r'\bbusiness\s*model', r'\bgoto.?market',
        ],
        "keywords_zh": [
            r'融资', r'收购', r'上市', r'投资', r'创业',
            r'营收', r'估值', r'合作', r'商业化', r'商业模式',
        ]
    },
    "安全/治理": {
        "icon": "🛡️",
        "keywords_en": [
            r'\bsafety\b', r'\balignment\b', r'\bregulation',
            r'\bgovernance', r'\bethics?\b', r'\bharm\b',
            r'\bbias\b', r'\bfairness\b', r'\btransparen',
            r'\baccountab', r'\bred.?team', r'\bjailbreak',
            r'\bpoison', r'\badversar', r'\brobustness',
            r'\bhallucinat', r'\bcopyright', r'\bpolicy',
            r'\blegislat', r'\bexecutive\s*order', r'\bai\s*act',
        ],
        "keywords_zh": [
            r'安全', r'对齐', r'监管', r'治理', r'伦理',
            r'偏见', r'公平', r'透明', r'问责', r'红队',
            r'幻觉', r'版权', r'政策', r'立法',
        ]
    },
    "应用/产品": {
        "icon": "🔧",
        "keywords_en": [
            r'\blaunch\b', r'\brelease\b', r'\bproduct\b',
            r'\bapp\b', r'\bapplication', r'\bplatform',
            r'\bfeature\b', r'\bupdate\b', r'\bnew\s*tool',
            r'\bsearch\b', r'\brecommend', r'\bgenerat',
            r'\bsummar', r'\btranslate', r'\bchatbot',
            r'\bassistant', r'\bcopilot\b', r'\bcoding\b',
            r'\bwrite', r'\bimage\s*gen', r'\bvideo\s*gen',
            r'\bcode\s*gen', r'\bmusic\s*gen', r'\bspeech\b',
            r'\bvoice\b', r'\btext.?to.?speech', r'\btts\b',
            r'\bstt\b', r'\basr\b', r'\bocr\b',
            r'\bdocument', r'\bknowledge\s*base', r'\brag\b',
            r'\bretriev', r'\bembedding', r'\bvector\b',
            r'\bdatabase', r'\bapi\b', r'\bsdk\b',
        ],
        "keywords_zh": [
            r'发布', r'产品', r'应用', r'平台', r'功能',
            r'更新', r'工具', r'搜索', r'推荐', r'生成',
            r'摘要', r'翻译', r'聊天', r'助手', r'编码',
            r'图像生成', r'视频生成', r'语音', r'文档',
            r'知识库', r'检索', r'向量', r'数据库',
        ]
    },
    "开源": {
        "icon": "🔓",
        "keywords_en": [
            r'open.?source', r'github\b', r'repository',
            r'apache\s*2\.?0', r'mit\s*license', r'gpl\b',
            r'oss\b', r'open.?weight', r'open.?model',
            r'hugging.?face', r'pypi\b', r'pip\s+install',
            r'docker\b', r'container', r'kubernetes',
        ],
        "keywords_zh": [
            r'开源', r'仓库', r'许可证', r'开放权重',
            r'开放模型', r'容器化',
        ]
    }
}


def classify_item(item):
    """
    对单条新闻进行分类

    Args:
        item: 新闻字典，包含 title, summary, type 等字段

    Returns:
        str: 分类名称（如 "大模型"），如果无法分类则返回 "其他"
    """
    # 构建匹配文本（标题 + 摘要）
    title = item.get("title", "") or ""
    summary = item.get("summary", "") or ""
    text = f"{title} {summary}".lower()

    # GitHub 项目直接归为开源
    if item.get("type") == "开源项目" or item.get("source") == "github":
        return "开源"

    # 按分类计分
    scores = {}
    for category, rules in CLASSIFICATION_RULES.items():
        score = 0
        for pattern in rules["keywords_en"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1
        for pattern in rules["keywords_zh"]:
            if re.search(pattern, text):
                score += 2  # 中文匹配权重更高
        scores[category] = score

    # 选择得分最高的分类
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score > 0:
        logger.debug(f"分类 [{best_category}] 得分={best_score}: {title[:30]}...")
        return best_category
    else:
        # 根据类型兜底
        type_to_category = {
            "论文": "大模型",
            "产品": "应用/产品",
            "视频": "应用/产品",
            "开源项目": "开源",
        }
        return type_to_category.get(item.get("type", ""), "其他")


def classify_items(items):
    """
    批量分类新闻

    Args:
        items: 新闻字典列表

    Returns:
        dict: { category_name: [items] } 按分类分组
    """
    classified = {}
    
    for item in items:
        category = classify_item(item)
        if category not in classified:
            classified[category] = []
        item["category"] = category
        classified[category].append(item)

    logger.info(f"分类完成: {len(items)} 条 → {len(classified)} 个分类")
    for cat, cat_items in classified.items():
        icon = CLASSIFICATION_RULES.get(cat, {}).get("icon", "📌")
        logger.info(f"  {icon} {cat}: {len(cat_items)} 条")

    return classified


def get_category_icon(category):
    """获取分类对应的emoji图标"""
    return CLASSIFICATION_RULES.get(category, {}).get("icon", "📌")


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)

    test_items = [
        {"title": "GPT-5: Scaling to 10 Trillion Parameters", "summary": "OpenAI releases new LLM", "type": "论文"},
        {"title": "LangChain Agents v2: Multi-agent orchestration", "summary": "Framework for autonomous workflows", "type": "产品"},
        {"title": "Anthropic raises $5B Series F", "summary": "AI startup funding round", "type": "资讯"},
        {"title": "MIT releases open-source model under Apache 2.0", "summary": "Open weight model", "type": "资讯"},
        {"title": "New text-to-video model generates 4K clips", "summary": "AI video generation", "type": "产品"},
        {"type": "开源项目", "title": "facebookresearch/llama", "summary": "Open source LLM", "source": "github"},
    ]

    result = classify_items(test_items)
    for cat, items in result.items():
        icon = get_category_icon(cat)
        print(f"{icon} {cat}:")
        for item in items:
            print(f"  - {item['title'][:40]}")
