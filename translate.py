"""自动翻译模块 - 用 DeepSeek 翻译英文内容为中文"""
import json, os, subprocess, time, hashlib

MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com/v1"
TIMEOUT = 30
CACHE_FILE = "data/translation_cache.json"

def get_key():
    return os.environ.get("DEEPSEEK_API_KEY")

def load_cache():
    if os.path.exists(CACHE_FILE):
        return json.load(open(CACHE_FILE))
    return {}

def save_cache(cache):
    json.dump(cache, open(CACHE_FILE, "w"), ensure_ascii=False, indent=1)

def translate_to_zh(text_en, context=""):
    """翻译英文到中文，带缓存"""
    if not text_en or not text_en.strip():
        return ""

    key = get_key()
    if not key:
        return text_en  # 没密钥就返回原文

    cache = load_cache()
    cache_key = hashlib.md5(f"EN2ZH|{text_en}|{context}".encode()).hexdigest()

    if cache_key in cache:
        return cache[cache_key]

    prompt = f"""Translate this English text to Chinese. Keep technical terms, proper nouns, and brand names unchanged. Be concise and natural.

Context: {context or 'AI job market intelligence'}
English: {text_en}

Output only the Chinese translation, no explanations."""

    body = json.dumps({
        "model": MODEL,
        "messages": [{"role":"user","content":prompt}],
        "temperature": 0.3
    })

    try:
        r = subprocess.run(
            ["curl","-s","-m",str(TIMEOUT),
             "-H",f"Authorization: Bearer {key}",
             "-H","Content-Type: application/json",
             "-X","POST",
             f"{BASE_URL}/chat/completions",
             "--data-binary","@-"],
            input=body, capture_output=True, text=True, timeout=TIMEOUT+5)

        if r.returncode != 0:
            return text_en

        resp = json.loads(r.stdout)
        zh = resp["choices"][0]["message"]["content"].strip()

        cache[cache_key] = zh
        save_cache(cache)
        return zh
    except:
        return text_en

def batch_translate(texts, context=""):
    """批量翻译（带延迟防止限流）"""
    results = []
    for i, txt in enumerate(texts):
        results.append(translate_to_zh(txt, context))
        if i < len(texts) - 1:
            time.sleep(0.5)
    return results

# ── P1-2 AI 分类 ──
_CLASSIFY_MAP = {
    "nl-cat-product": "New model releases, product launches, feature updates, new AI assistants or apps",
    "nl-cat-research": "Academic papers, benchmarks, technical deep-dives, training methods, datasets",
    "nl-cat-oss": "Open-source frameworks, GitHub releases, developer tools, HuggingFace model releases",
    "nl-cat-biz": "Funding rounds, acquisitions, enterprise deals, industry partnerships, company valuations",
    "nl-cat-safety": "AI safety, regulation, government policy, ethics, governance, alignment, bias, copyright",
    "nl-cat-opinion": "Analysis, opinion pieces, commentary, how-to guides, predictions, explainers, reflections",
    "nl-cat-other": "Miscellaneous AI news that doesn't clearly fit the above categories",
}

def classify_article(title, summary=""):
    """用 DeepSeek 对 AI 文章分类，返回 category_id；无密钥或失败时返回 None（调用方降级到关键词）"""
    if not title:
        return None
    key = get_key()
    if not key:
        return None
    cache = load_cache()
    cache_key = hashlib.md5(f"CLASSIFY|{title}|{(summary or '')[:200]}".encode()).hexdigest()
    if cache_key in cache:
        r = cache[cache_key]
        if r in _CLASSIFY_MAP:
            return r
    cats_str = "\n".join(f"  {k}: {v}" for k, v in _CLASSIFY_MAP.items())
    prompt = (f"Classify this AI news article into exactly one category.\n\n"
              f"Categories:\n{cats_str}\n\n"
              f"Title: {title}\n"
              f"Summary: {(summary or '(none)')[:300]}\n\n"
              f"Output ONLY the category ID (e.g. nl-cat-product), nothing else.")
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 25,
    })
    try:
        time.sleep(0.3)   # 轻限流
        r = subprocess.run(
            ["curl", "-s", "-m", str(TIMEOUT),
             "-H", f"Authorization: Bearer {key}",
             "-H", "Content-Type: application/json",
             "-X", "POST", f"{BASE_URL}/chat/completions",
             "--data-binary", "@-"],
            input=body, capture_output=True, text=True, timeout=TIMEOUT + 5)
        if r.returncode != 0:
            return None
        resp = json.loads(r.stdout)
        raw = resp["choices"][0]["message"]["content"].strip().strip('"').strip("'")
        if raw in _CLASSIFY_MAP:
            cache[cache_key] = raw; save_cache(cache); return raw
        for cat_id in _CLASSIFY_MAP:
            if cat_id in raw:
                cache[cache_key] = cat_id; save_cache(cache); return cat_id
        return None
    except:
        return None
