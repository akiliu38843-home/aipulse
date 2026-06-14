"""
fetch_newsletters.py — 抓取 AI 简报信源 RSS，按信源分组存储
输出: data/newsletters.json
用法: python3 fetch_newsletters.py
"""
import json, re, datetime, time, os, warnings
warnings.filterwarnings("ignore")
import feedparser

try:
    import requests as _req
    PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
    HEADERS = {"User-Agent": "Mozilla/5.0 AIPulse/1.0"}
    def fetch_feed(url):
        """用 requests 处理 308 重定向，再交给 feedparser 解析"""
        r = _req.get(url, proxies=PROXIES, headers=HEADERS, timeout=15, allow_redirects=True)
        return feedparser.parse(r.text)
except ImportError:
    os.environ.setdefault("http_proxy",  "http://127.0.0.1:7897")
    os.environ.setdefault("https_proxy", "http://127.0.0.1:7897")
    def fetch_feed(url):
        return feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0 AIPulse/1.0"})

# ── 信源清单（名称 / 一行简介 / RSS 地址 / 最多几条 / 可选关键词过滤）──
SOURCES = [
    {
        "name": "TLDR AI",
        "desc": "全球最大 AI 日报，80 万+ 订阅，工作日每天更新，产品新闻+模型发布+工具动态极简快讯",
        "url":  "https://tldr.tech/api/rss/ai",
        "max":  8,
    },
    {
        "name": "The Decoder",
        "desc": "专注 AI 的英文新闻站（德国），每天发 5–10 篇，研究进展+大公司动态+AI 与社会的深度报道",
        "url":  "https://the-decoder.com/feed/",
        "max":  8,
    },
    {
        "name": "VentureBeat AI",
        "desc": "美国老牌科技媒体 AI 频道，商业融资+企业落地+产品发布，商业视角为主",
        "url":  "https://venturebeat.com/feed/",
        "max":  8,
        "filter": ["AI", "artificial intelligence", "LLM", "machine learning",
                   "OpenAI", "Anthropic", "Google DeepMind", "Gemini", "Claude",
                   "language model", "generative"],
    },
    {
        "name": "Import AI",
        "desc": "Anthropic 联合创始人 Jack Clark 的研究周刊，专注 AI 安全+政策+前沿论文，已连续更新 8+ 年，第 460+ 期",
        "url":  "https://importai.substack.com/feed",
        "max":  5,
    },
    {
        "name": "Interconnects",
        "desc": "前 HuggingFace 研究员 Nathan Lambert 的 AI 分析周刊，重点关注强化学习+开源模型+AI 对齐进展",
        "url":  "https://www.interconnects.ai/feed",
        "max":  5,
    },
    {
        "name": "AI Snake Oil",
        "desc": "普林斯顿大学教授 Arvind Narayanan 主理，专门戳穿 AI 夸大宣传，帮你辨别真实进展与营销噱头",
        "url":  "https://aisnakeoil.substack.com/feed",
        "max":  5,
        "cutoff_days": 30,
    },
    {
        "name": "MIT Technology Review AI",
        "desc": "百年 MIT 科技媒体，深度报道 AI 与社会+伦理+监管政策，学术严谨，部分文章有 paywall",
        "url":  "https://www.technologyreview.com/feed/",
        "max":  6,
        "filter": ["AI", "artificial intelligence", "machine learning", "chatbot",
                   "GPT", "LLM", "robot", "algorithm", "generative", "neural"],
    },
    {
        "name": "HuggingFace Blog",
        "desc": "开源 AI 最大平台官方博客，新模型发布+技术教程+开源工具，每篇都是第一手资讯",
        "url":  "https://huggingface.co/blog/feed.xml",
        "max":  6,
    },
    {
        "name": "The Sequence",
        "desc": "面向 ML 工程师的日报，论文速读+工具评测+工程实战，Substack 上几乎每天更新",
        "url":  "https://thesequence.substack.com/feed",
        "max":  6,
    },
    {
        "name": "Hacker News AI 热议",
        "desc": "技术社区 Hacker News 上 AI 相关热帖实时流，过滤 30+ 点赞，开发者真实评价+风向标",
        "url":  "https://hnrss.org/newest?q=llm+OR+claude+OR+openai+OR+gemini&points=30",
        "max":  8,
    },
    {
        "name": "Last Week in AI",
        "desc": "研究员维护的 AI 周报，论文+产业新闻混合汇总，一次性看完最近 AI 发生了什么",
        "url":  "https://lastweekin.ai/feed",
        "max":  5,
        "cutoff_days": 30,   # 周刊，放宽到 30 天
    },
    {
        "name": "Gradient Flow",
        "desc": "O'Reilly 旗下 AI 行业分析博客，关注基础设施+算力经济+企业 AI 落地，商业+工程双视角",
        "url":  "https://gradientflow.com/feed/",
        "max":  5,
    },
    # ── 新增信源（2026-06-14）──
    {
        "name": "OpenAI Blog",
        "desc": "OpenAI 官方博客，新模型发布+安全研究+产品公告，第一手资讯",
        "url":  "https://openai.com/blog/rss.xml",
        "max":  8,
    },
    {
        "name": "Google DeepMind",
        "desc": "Google DeepMind 官方博客，前沿研究发布、Gemini 系列更新、技术突破",
        "url":  "https://deepmind.google/blog/rss.xml",
        "max":  8,
    },
    {
        "name": "The Verge AI",
        "desc": "科技媒体 The Verge 的 AI 专栏，产品评测+政策报道+行业新闻，面向普通读者",
        "url":  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "max":  8,
    },
    {
        "name": "TechCrunch AI",
        "desc": "TechCrunch AI 频道，AI 创业融资+产品发布+大厂动态，商业视角",
        "url":  "https://techcrunch.com/category/artificial-intelligence/feed/",
        "max":  8,
        "filter": ["AI", "artificial intelligence", "LLM", "GPT", "machine learning",
                   "OpenAI", "Anthropic", "Google", "Claude", "Gemini",
                   "language model", "generative", "chatbot", "neural", "model"],
    },
    {
        "name": "Simon Willison",
        "desc": "Django 联创 Simon Willison 的博客，每天记录 AI 工具实验与观察，最真实的开发者视角",
        "url":  "https://simonwillison.net/atom/everything/",
        "max":  8,
        "filter": ["AI", "LLM", "GPT", "Claude", "Gemini", "language model", "ChatGPT",
                   "openai", "anthropic", "embedding", "vector", "RAG", "agent",
                   "MCP", "tool use", "prompt", "llama", "mistral", "gemma"],
    },
    {
        "name": "Ahead of AI",
        "desc": "ML 研究员 Sebastian Raschka 的周刊，论文精读+技术深挖，适合工程师和研究者",
        "url":  "https://magazine.sebastianraschka.com/feed",
        "max":  5,
        "cutoff_days": 30,
    },
    {
        "name": "One Useful Thing",
        "desc": "沃顿商学院教授 Ethan Mollick 的博客，AI 对工作/教育的实际影响，有大量亲身实验与见解",
        "url":  "https://www.oneusefulthing.org/feed",
        "max":  6,
        "cutoff_days": 30,
    },
    {
        "name": "The Gradient",
        "desc": "Stanford 背景的 AI 研究发表平台，深度技术综述+研究者访谈，学术与产业交叉视角",
        "url":  "https://thegradient.pub/rss/",
        "max":  5,
        "cutoff_days": 180,  # 季刊节奏，放到 6 个月
    },
    # ── P4 新增：中文信源 ──
    {
        "name": "量子位",
        "desc": "中国 AI 科技媒体量子位，每日更新 AI 产品发布、研究进展、行业动态，中文读者首选",
        "url":  "https://www.qbitai.com/feed",
        "max":  8,
    },
]

DEFAULT_CUTOFF_DAYS = 14

def clean(s, n=400):
    s = " ".join(re.sub(r"<[^>]+>", " ", s or "").split())
    return s[:n] + ("…" if len(s) > n else "")

def passes_filter(title, summary, keywords):
    if not keywords:
        return True
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in keywords)

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

out = {
    "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "sources": [],
}

for src in SOURCES:
    name = src["name"]
    print(f"  [{name}]", end=" ", flush=True)
    cutoff = time.time() - src.get("cutoff_days", DEFAULT_CUTOFF_DAYS) * 86400
    items = []
    status = "?"
    try:
        d = fetch_feed(src["url"])
        seen = set()
        budget = src["max"] * 4   # 多取几条再过滤
        for e in d.entries[:budget]:
            tp = e.get("published_parsed") or e.get("updated_parsed")
            ts = time.mktime(tp) if tp else None
            # 只过过期判断，今天抓到的直接用
            if ts and ts < cutoff:
                continue
            title   = clean(e.get("title", ""), 200)
            summary = clean(e.get("summary", ""), 400)
            link    = e.get("link", "")
            date    = time.strftime("%Y-%m-%d", tp) if tp else ""

            if not title or link in seen:
                continue
            if not passes_filter(title, summary, src.get("filter")):
                continue
            seen.add(link)
            items.append({
                "title":   title,
                "date":    date,
                "link":    link,
                "summary": summary,
            })
            if len(items) >= src["max"]:
                break
        status = f"ok:{len(items)}"
    except Exception as ex:
        status = f"FAIL:{type(ex).__name__}:{str(ex)[:80]}"

    print(status)
    out["sources"].append({
        "id":     slug(name),
        "name":   name,
        "desc":   src["desc"],
        "url":    src["url"],
        "status": status,
        "items":  items,
    })

# ── P4 非 RSS 信源 ────────────────────────────────────────────────────────────

def fetch_hf_papers(max_items=12):
    """HuggingFace Daily Papers JSON API（免认证，当日收录的 AI 论文）"""
    r = _req.get("https://huggingface.co/api/daily_papers",
                 proxies=PROXIES,
                 headers={"User-Agent": "AIPulse/1.0"},
                 timeout=15)
    r.raise_for_status()
    papers = r.json()
    items = []
    for p in papers:
        paper = p.get("paper", {})
        title = paper.get("title") or p.get("title") or ""
        if not title:
            continue
        arxiv_id = paper.get("id", "")
        summary  = clean(paper.get("ai_summary") or paper.get("summary") or "", 400)
        pub      = (paper.get("publishedAt") or p.get("publishedAt") or "")[:10]
        upvotes  = paper.get("upvotes", 0)
        link     = (f"https://huggingface.co/papers/{arxiv_id}"
                    if arxiv_id else "https://huggingface.co/papers")
        # 标题只放论文名；把点赞数折进摘要首行（点赞为 0 时不显示）
        vote_str = f"👍 {upvotes} upvotes · " if upvotes > 0 else ""
        items.append({
            "title":   clean(title, 200),
            "date":    pub,
            "link":    link,
            "summary": clean(f"{vote_str}{summary}", 420),
        })
        if len(items) >= max_items:
            break
    return items


def fetch_github_trending_ai(max_items=8):
    """GitHub Today Trending — 过滤 AI/ML 仓库（网页抓取）"""
    # 多词短语 / 全词匹配才算命中，避免 "ai" 误伤 "trail"/"aimed" 等
    _PHRASE_KW = [
        "machine learning", "deep learning", "language model", "neural network",
        "stable diffusion", "text-to-", "fine-tun", "inference engine",
        "vision model", "multimodal", "retrieval augmented",
    ]
    _WORD_KW = {
        "llm", "gpt", "claude", "gemini", "llama", "mistral", "qwen",
        "transformer", "diffusion", "chatbot", "rag", "embedding",
        "generative", "openai", "anthropic", "huggingface",
        "langchain", "llamaindex", "llamacpp", "ollama", "vllm",
        "whisper", "stable-diffusion", "comfyui", "automatic1111",
    }

    def _is_ai(text):
        t = text.lower()
        words = set(re.findall(r"[a-z0-9]+", t))
        # whole-word match for "ai"
        if re.search(r"\bai\b", t): return True
        if any(kw in words for kw in _WORD_KW): return True
        if any(ph in t for ph in _PHRASE_KW): return True
        return False

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
               "Accept-Language": "en-US,en;q=0.9"}
    items, seen = [], set()
    for lang in ["", "Python", "Jupyter+Notebook"]:
        if len(items) >= max_items:
            break
        qs = ("since=daily" + (f"&l={lang}" if lang else ""))
        r = _req.get(f"https://github.com/trending?{qs}",
                     proxies=PROXIES, headers=headers, timeout=15)
        r.raise_for_status()
        # extract <article class="...Box-row..."> blocks
        blocks = re.findall(
            r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>',
            r.text, re.DOTALL)
        for blk in blocks:
            # repo path — prefer h2 > a to avoid sponsor/nav links
            mpath = re.search(
                r'<h2[^>]*>\s*<a\s[^>]*href="(/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"',
                blk)
            if not mpath:
                mpath = re.search(
                    r'href="(/[a-zA-Z0-9_.-]{2,}/[a-zA-Z0-9_.-]{2,})"', blk)
            if not mpath:
                continue
            path = mpath.group(1).rstrip("/")
            # skip GitHub's own non-repo paths
            if path.startswith(("/sponsors", "/explore", "/trending",
                                 "/topics", "/marketplace")):
                continue
            if path in seen:
                continue
            seen.add(path)
            # description — prefer <p class="...col-9...">
            mdesc = re.search(
                r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', blk, re.DOTALL)
            if not mdesc:
                mdesc = re.search(r'<p[^>]*>(.*?)</p>', blk, re.DOTALL)
            desc = (re.sub(r'\s+', ' ',
                           re.sub('<[^>]+>', '', mdesc.group(1))).strip()
                    if mdesc else "")
            repo_name = path.strip("/")
            if not _is_ai(repo_name + " " + desc):
                continue
            # stars today
            mstars = re.search(r'([\d,]+)\s*stars today', blk, re.IGNORECASE)
            stars_str = f" · ⭐{mstars.group(1)} today" if mstars else ""
            items.append({
                "title":   clean(f"🔥 {repo_name}{stars_str}", 200),
                "date":    datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                "link":    f"https://github.com{path}",
                "summary": clean(desc, 400),
            })
            if len(items) >= max_items:
                break
    return items


def translate_descs_zh(items):
    """
    用 DeepSeek API 批量翻译 items 里的 summary 字段（英文 → 中文）。
    成功则在每条 item 上追加 summary_zh 字段；失败静默跳过。
    """
    import os as _os
    key = _os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        return  # 无密钥，跳过
    descs = [it.get("summary", "") for it in items]
    if not any(descs):
        return
    prompt = (
        "把下面 JSON 数组里的每条英文描述翻译成简洁自然的中文（不超过 60 字），"
        "只返回翻译后的 JSON 字符串数组，不要任何其他内容：\n"
        + json.dumps(descs, ensure_ascii=False)
    )
    try:
        resp = _req.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": "deepseek-chat",
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2, "max_tokens": 800},
            proxies=PROXIES, timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # 剥掉可能的 ```json ... ``` 包裹
        raw = re.sub(r"^```[a-z]*\n?|```$", "", raw.strip()).strip()
        translated = json.loads(raw)
        if isinstance(translated, list):
            for it, zh in zip(items, translated):
                if zh and isinstance(zh, str):
                    it["summary_zh"] = zh.strip()
    except Exception as ex:
        print(f"  [translate_zh] SKIP:{type(ex).__name__}:{str(ex)[:60]}")


NON_RSS = [
    {
        "name": "HuggingFace Daily Papers",
        "desc": "HuggingFace 每日收录的 AI 论文（社区投票精选），直接链到 HF 论文页，带 AI 摘要",
        "url":  "https://huggingface.co/api/daily_papers",
        "type": "hf_papers",
        "max":  12,
    },
    {
        "name": "GitHub Trending AI",
        "desc": "GitHub 每日 Trending 中 AI/ML 相关仓库，反映开发者社区最关注的开源项目动向",
        "url":  "https://github.com/trending",
        "type": "github_trending",
        "max":  8,
    },
]

# ── P5 OpenRouter 实时价格 ───────────────────────────────────────────────────

# 精选模型：(组, 显示名, openrouter_id, provider_code)
_PRICE_CURATED = [
    # 旗舰 — 最强但最贵
    ("旗舰", "Claude Fable 5",  "anthropic/claude-fable-5",   "ac"),
    ("旗舰", "GPT-5 Pro",       "openai/gpt-5-pro",           "oa"),
    ("旗舰", "Grok 4",          "x-ai/grok-4.20",             "xai"),
    # 实用 — 日常首选
    ("实用", "Claude Sonnet 4.6","anthropic/claude-sonnet-4.6","ac"),
    ("实用", "GPT-5",            "openai/gpt-5",               "oa"),
    ("实用", "GPT-5.5",          "openai/gpt-5.5",             "oa"),
    ("实用", "Gemini 3.5 Flash", "google/gemini-3.5-flash",    "gl"),
    ("实用", "DeepSeek R1",      "deepseek/deepseek-r1",       "ds"),
    # 推理 — 慢但深思
    ("推理", "o3",              "openai/o3",                   "oa"),
    ("推理", "o4-mini",         "openai/o4-mini",              "oa"),
    # 省钱 — 高频/测试用
    ("省钱", "Claude Haiku 4.5","anthropic/claude-haiku-4.5",  "ac"),
    ("省钱", "GPT-5 nano",      "openai/gpt-5-nano",           "oa"),
    ("省钱", "GPT-4o mini",     "openai/gpt-4o-mini",          "oa"),
    ("省钱", "Llama 4 Maverick","meta-llama/llama-4-maverick",  "ll"),
    ("省钱", "Qwen3 Max",       "qwen/qwen3-max",              "qw"),
]

def fetch_openrouter_prices():
    """从 OpenRouter 公开 JSON API 拉取精选模型的实时价格"""
    r = _req.get("https://openrouter.ai/api/v1/models",
                 proxies=PROXIES,
                 headers={"User-Agent": "AIPulse/1.0"},
                 timeout=15)
    r.raise_for_status()
    model_map = {m["id"]: m for m in r.json()["data"]}

    groups_order = ["旗舰", "实用", "推理", "省钱"]
    groups = {g: [] for g in groups_order}

    for grp, dname, or_id, prov in _PRICE_CURATED:
        m = model_map.get(or_id)
        if not m:
            continue
        pr = m.get("pricing", {})
        inp = round(float(pr.get("prompt",     0)) * 1_000_000, 3)
        out = round(float(pr.get("completion", 0)) * 1_000_000, 3)
        ctx = m.get("context_length", 0) // 1000
        groups[grp].append({
            "name": dname, "id": or_id, "prov": prov,
            "input": inp, "output": out, "ctx_k": ctx,
        })

    return {
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "groups": [{"label": g, "models": groups[g]}
                   for g in groups_order if groups[g]],
    }


print("\n── AI 价格快照 ──")
try:
    prices = fetch_openrouter_prices()
    total = sum(len(g["models"]) for g in prices["groups"])
    json.dump(prices, open("data/ai_prices.json", "w"), ensure_ascii=False, indent=1)
    print(f"  [OpenRouter] ok:{total} 个模型价格 → data/ai_prices.json")
except Exception as ex:
    print(f"  [OpenRouter] FAIL:{type(ex).__name__}:{str(ex)[:80]}")

print("\n── 非 RSS 信源 ──")
for src in NON_RSS:
    name = src["name"]
    print(f"  [{name}]", end=" ", flush=True)
    items, status = [], "?"
    try:
        if src["type"] == "hf_papers":
            items = fetch_hf_papers(max_items=src["max"])
        elif src["type"] == "github_trending":
            items = fetch_github_trending_ai(max_items=src["max"])
            translate_descs_zh(items)  # 追加 summary_zh 字段
        status = f"ok:{len(items)}"
    except Exception as ex:
        status = f"FAIL:{type(ex).__name__}:{str(ex)[:80]}"
    print(status)
    out["sources"].append({
        "id":     slug(name),
        "name":   name,
        "desc":   src["desc"],
        "url":    src["url"],
        "status": status,
        "items":  items,
    })

os.makedirs("data", exist_ok=True)
json.dump(out, open("data/newsletters.json", "w"), ensure_ascii=False, indent=1)

all_srcs = SOURCES + NON_RSS
ok  = sum(1 for s in out["sources"] if s["status"].startswith("ok"))
tot = sum(len(s["items"]) for s in out["sources"])
print(f"\n✅ 完成：{ok}/{len(all_srcs)} 个信源成功  共 {tot} 条文章")
print(f"   → data/newsletters.json")
