#!/usr/bin/env python3
"""
Reddit RSS Parser for Open Source Models
Extracts and filters posts from r/LocalLLaMA and r/unsloth
"""

import feedparser
import re
from typing import List, Dict, Optional
from datetime import datetime

# Keywords related to open source models
MODEL_KEYWORDS = [
    'model', 'llm', 'gpt', 'llama', 'mistral', 'qwen', 'deepseek',
    'yi', 'baichuan', 'chatglm', 'gemma', 'phi', 'mixtral',
    'unsloth', 'finetune', 'training', 'quantize', 'quantization',
    'gguf', 'awq', 'gptq', 'exl2', 'hqq', 'lora', 'qlora',
    'local', 'run locally', 'inference', 'benchmark', 'performance',
    'release', 'v2', 'v3', 'update', 'new model'
]

# Keywords to exclude (complaints, pure errors, emotional posts)
EXCLUDE_KEYWORDS = [
    'help', 'error', 'bug', 'crash', 'stuck', 'slow', 'frustrated',
    'why is', 'how do i', 'beginner question', 'basic question',
    'rant', 'complaint', 'issue with', 'not working'
]

def is_model_related(title: str, content: str) -> bool:
    """Check if post is related to open source models"""
    text = (title + ' ' + content).lower()
    
    # Check for model-related keywords
    has_model_keyword = any(kw in text for kw in MODEL_KEYWORDS)
    
    # Check for exclude keywords
    has_exclude_keyword = any(kw in text for kw in EXCLUDE_KEYWORDS)
    
    return has_model_keyword and not has_exclude_keyword

def extract_model_info(content: str) -> Dict[str, str]:
    """Extract model names and entry points from content"""
    info = {
        'model_name': None,
        'lm_studio': None,
        'unsloth': None,
        'official_link': None
    }
    
    content_lower = content.lower()
    
    # Extract model names (common patterns)
    model_patterns = [
        r'(llama[-\s]?\d+(?:\.\d+)*)',
        r'(mistral[-\s]?\d+(?:\.\d+)*)',
        r'(qwen[-\s]?\d+(?:\.\d+)*)',
        r'(gemma[-\s]?\d+(?:\.\d+)*)',
        r'(phi[-\s]?\d+(?:\.\d+)*)',
        r'(yi[-\s]?\d+(?:\.\d+)*)',
        r'(deepseek[-\s]?\w+)'
    ]
    
    for pattern in model_patterns:
        match = re.search(pattern, content_lower)
        if match:
            info['model_name'] = match.group(0).upper()
            break
    
    # Look for LM Studio links
    lm_studio_match = re.search(r'(https?://(?:www\.)?lmstudio\.ai/\S+)', content, re.IGNORECASE)
    if lm_studio_match:
        info['lm_studio'] = lm_studio_match.group(0)
    
    # Look for Unsloth links
    unsloth_match = re.search(r'(https?://(?:www\.)?unsloth\.ai/\S+)', content, re.IGNORECASE)
    if unsloth_match:
        info['unsloth'] = unsunsloth_match.group(0)
    
    # Look for HuggingFace or GitHub links (official sources)
    hf_match = re.search(r'(https?://huggingface\.co/\S+)', content, re.IGNORECASE)
    if hf_match:
        info['official_link'] = hf_match.group(0)
    
    github_match = re.search(r'(https?://github\.com/\S+)', content, re.IGNORECASE)
    if github_match and not info['official_link']:
        info['official_link'] = github_match.group(0)
    
    return info

def classify_stage(content: str) -> str:
    """Classify the development stage mentioned in the post"""
    content_lower = content.lower()
    
    if any(kw in content_lower for kw in ['release', 'released', 'announcing', 'new model']):
        return '发布'
    elif any(kw in content_lower for kw in ['adapter', 'adapt', 'support', 'compatible']):
        return '适配'
    elif any(kw in content_lower for kw in ['quantize', 'quantization', 'gguf', 'awq', 'gptq']):
        return '量化'
    elif any(kw in content_lower for kw in ['train', 'finetune', 'lora', 'qlora', 'training']):
        return '训练'
    elif any(kw in content_lower for kw in ['run locally', 'inference', 'benchmark', 'test']):
        return '本地可用'
    else:
        return '讨论'

def parse_rss(url: str) -> List[Dict]:
    """Parse RSS feed and return filtered posts"""
    feed = feedparser.parse(url)
    posts = []
    
    for entry in feed.entries:
        post = {
            'title': entry,
            'subreddit': feed.title,
            'link': entry.link,
            'content': entry.get('description', ''),
            'score': getattr(entry, 'score', 0),
            'comments': getattr(entry, 'num_comments', 0),
            'published': entry.get('published', '')
        }
        
        # Check if post is model-related
        if is_model_related(post['title'], post['content']):
            # Extract additional info
            model_info = extract_model_info(post['content'])
            post['model_info'] = model_info
            post['stage'] = classify_stage(post['content'])
            posts.append(post)
    
    return posts

def merge_posts(posts1: List[Dict], posts2: List[Dict]) -> List[Dict]:
    """Merge posts from two subreddits and sort by score"""
    all_posts = posts1 + posts2
    
    # Sort by score (Reddit's default sorting)
    all_posts.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return all_posts

def generate_summary(posts: List[Dict]) -> str:
    """Generate Chinese summary of posts"""
    if not posts:
        return "本周未找到与开源模型直接相关的热门帖子。"
    
    output = []
    output.append(f"# 本周开源模型热帖 Top {min(len(posts), 10)}\n")
    
    for i, post in enumerate(posts[:10], 1):
        model_info = post['model_info']
        model_name = model_info.get('model_name', '未确认')
        
        output.append(f"\n## {i}. {post['title']}")
        output.append(f"\n**来源：** {post['subreddit']}")
        output.append(f"**链接：** {post['link']}")
        output.append(f"**热度：** {post['score']} 👍")
        
        # Core content summary
        content = post['content']
        # Strip HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        # Take first 200 chars as summary
        summary = content[:200] + '...' if len(content) > 200 else content
        output.append(f"**核心内容：** {summary.strip()}")
        
        # Stage classification
        output.append(f"**流程阶段：** {post['stage']}")
        
        # Entry points
        entry_points = []
        if model_info.get('lm_studio'):
            entry_points.append(f"LM Studio: {model_info['lm_studio']}")
        if model_info.get('unsloth'):
            entry_points.append(f"Unsloth: {model_info['unsloth']}")
        if model_info.get('official_link'):
            entry_points.append(f"官方: {model_info['official_link']}")
        
        if entry_points:
            output.append("**可用入口：**")
            for ep in entry_points:
                output.append(f"  - {ep}")
        else:
            output.append("**可用入口：** 未确认")
        
        output.append("---")
    
    # Add topic summary
    output.append("\n## 本周讨论主题总结")
    
    # Extract model names mentioned
    models_mentioned = set()
    for post in posts:
        model_name = post['model_info'].get('model_name')
        if model_name:
            models_mentioned.add(model_name)
    
    if models_mentioned:
        output.append(f"\n**热门模型：** {', '.join(sorted(models_mentioned))}")
    
    # Count stages
    stage_counts = {}
    for post in posts:
        stage = post['stage']
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    output.append("\n**讨论焦点：**")
    for stage, in sorted(stage_counts.items(), key=lambda x: x[1], reverse=True):
        output.append(f"  - {stage}: {count} 条")
    
    # Entry points summary
    output.append("\n## 可用入口整理\n")
    
    model_entries = {}
    for post in posts:
        model_name = post['model_info'].get('model_name', '其他')
        if model_name not in model_entries:
            model_entries[model_name] = post['model_info']
    
    for model_name, info in sorted(model_entries.items()):
        output.append(f"\n### {model_name}")
        if info.get('lm_studio'):
            output.append(f"- LM Studio: {info['lm_studio']}")
        else:
            output.append("- LM Studio: 未确认")
        
        if info.get('unsloth'):
            output.append(f"- Unsloth: {info['unsloth']}")
        else:
            output.append("- Unsloth: 未确认")
        
        if info.get('official_link'):
            output.append(f"- 官方: {info['official_link']}")
        else:
            output.append("- 官方: 未确认")
    
    return '\n'.join(output)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_rss.py <rss_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    posts = parse_rss(url)
    
    print(f"Parsed {len(posts)} model-related posts from {url}")
    for post in posts[:5]:
        print(f"  - {post['title'][:60]}... (score: {post['score']})")
