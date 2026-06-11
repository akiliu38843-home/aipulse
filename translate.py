"""自动翻译模块 - 用 DeepSeek 翻译中文内容为英文"""
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

def translate(text_zh, context=""):
    """翻译中文到英文，带缓存"""
    if not text_zh or not text_zh.strip():
        return ""

    key = get_key()
    if not key:
        return text_zh  # 没密钥就返回原文

    cache = load_cache()
    cache_key = hashlib.md5(f"{text_zh}|{context}".encode()).hexdigest()

    if cache_key in cache:
        return cache[cache_key]

    prompt = f"""Translate this Chinese text to English. Keep technical terms, proper nouns, and brand names unchanged. Be concise and natural.

Context: {context or 'AI job market intelligence'}
Chinese: {text_zh}

Output only the English translation, no explanations."""

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
            return text_zh

        resp = json.loads(r.stdout)
        en = resp["choices"][0]["message"]["content"].strip()

        cache[cache_key] = en
        save_cache(cache)
        return en
    except:
        return text_zh

def batch_translate(texts, context=""):
    """批量翻译（带延迟防止限流）"""
    results = []
    for i, txt in enumerate(texts):
        results.append(translate(txt, context))
        if i < len(texts) - 1:
            time.sleep(0.5)
    return results
