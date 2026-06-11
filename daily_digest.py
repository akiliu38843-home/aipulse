"""Daily Digest — 给 AI native 同事的每日 3 件事。

汇总过去 N 小时所有源（arxiv / HN hot / HF trending / blog RSS / OpenAI/Anthropic 官博）
→ LLM 排序+编辑成「今天最该看的 3 件事」+ 一句话总结
→ 写 signals.db.daily_digest 表 + data/daily_digest_latest.json

设计原则：
- 对 AI native 工程师有用 > 对小白有用 (LLM prompt 明确人群)
- 每件事附 why_important + so_what_for_you 两句
- 双语（中英），用户可在前端切语言
- 失败时输出空 digest（不假装），前端显示「无新事」

两层 dedup（v2 加, 2026-05-22）：
- 硬: 近 DEDUP_DAYS 天的 item URL 集合, raw items 里 exact URL match 直接 drop
- 软: 把近 DEDUP_DAYS 天的 titles 列在 LLM prompt, 让它避开同角度
"""
import json, os, sys, sqlite3, datetime, subprocess, time, urllib.request, urllib.parse, re
from collections import defaultdict

MODEL = "gpt-5.4-mini"
TIMEOUT = 60
LOOKBACK_HOURS = 36   # 留富裕 — RSS/HF 不一定每日都有新增
DEDUP_DAYS = 7        # 不重复前 7 天讲过的 URL / 主题

def get_key_base():
    key = os.environ.get("UYILINK_API_KEY")
    base = os.environ.get("UYILINK_BASE_URL")
    if key and base: return key, base
    p = os.path.expanduser("~/.uyilink_key_tmp")
    if os.path.exists(p): return open(p).read().strip(), "https://sz.uyilink.com/v1"
    return None, None
KEY, BASE = get_key_base()
if not KEY:
    print("⚠ UYILINK_API_KEY 未配置 → 跳过 daily_digest"); sys.exit(0)

def llm(prompt, max_retry=3):
    body = json.dumps({"model":MODEL,
        "messages":[{"role":"system","content":"You output strict JSON only."},
                    {"role":"user","content":prompt}],
        "response_format":{"type":"json_object"}}, ensure_ascii=False)
    for attempt in range(max_retry):
        try:
            r = subprocess.run(["curl","-s","-m",str(TIMEOUT),
                "-H",f"Authorization: Bearer {KEY}","-H","Content-Type: application/json",
                "-X","POST",f"{BASE.rstrip('/')}/chat/completions","--data-binary","@-"],
                input=body, capture_output=True, text=True, timeout=TIMEOUT+5)
            if r.returncode != 0: raise RuntimeError(f"curl rc={r.returncode}")
            resp = json.loads(r.stdout)
            if "error" in resp: raise RuntimeError(f"LLM err: {resp['error']}")
            return json.loads(resp["choices"][0]["message"]["content"]), resp.get("usage",{})
        except Exception as e:
            if attempt < max_retry-1: time.sleep(2**attempt)
            else: raise

def fetch_arxiv_recent():
    """arXiv cs.AI/LG/CL 近 36h 论文"""
    import feedparser
    url = ("http://export.arxiv.org/api/query?search_query="
           "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL"
           "&sortBy=submittedDate&sortOrder=descending&max_results=20")
    d = feedparser.parse(url, request_headers={"User-Agent":"NorthStar/0.5"})
    cutoff = time.time() - LOOKBACK_HOURS*3600
    items = []
    for e in d.entries:
        tp = e.get("published_parsed")
        if tp and time.mktime(tp) < cutoff: continue
        items.append({"source":"arXiv","title":e.get("title","").replace("\n"," ").strip(),
                      "url":e.get("link",""),"date":e.get("published","")[:10],
                      "summary":(e.get("summary","") or "").replace("\n"," ").strip()[:300]})
    return items[:8]

def fetch_hn_hot():
    """HN 近 36h 高分 AI 故事"""
    since = int(time.time()) - LOOKBACK_HOURS*3600
    try:
        u = ("https://hn.algolia.com/api/v1/search?query=" + urllib.parse.quote("AI agent LLM") +
             f"&tags=story&numericFilters=created_at_i>{since},points>40&hitsPerPage=12")
        r = subprocess.run(["curl","-s","-m","20","-A","NorthStar/0.5",u],
                           capture_output=True, text=True, timeout=25)
        d = json.loads(r.stdout)
        return [{"source":"Hacker News","title":h.get("title",""),"url":h.get("url","") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                 "points":h.get("points",0),"date":(h.get("created_at","") or "")[:10]} for h in d.get("hits",[])][:8]
    except Exception as e:
        print(f"  ✗ HN: {e}"); return []

def fetch_hf_trending():
    """HF trending models（最新一份 snapshot 即可，不限 24h）"""
    try:
        from huggingface_hub import HfApi
        models = list(HfApi().list_models(sort="trendingScore", limit=12))
        return [{"source":"HuggingFace","title":m.id,"url":f"https://huggingface.co/{m.id}",
                 "pipeline":getattr(m,"pipeline_tag","") or "","date":""} for m in models][:5]
    except Exception as e:
        print(f"  ✗ HF: {e}"); return []

def fetch_blogs():
    """复用现有 blogs_w2.json，过滤近 36h"""
    p = "data/blogs_w2.json"
    if not os.path.exists(p): return []
    d = json.load(open(p))
    cutoff = (datetime.datetime.now() - datetime.timedelta(hours=LOOKBACK_HOURS)).strftime("%Y-%m-%d")
    items = []
    for it in (d.get("items") or []):
        if (it.get("date","") or "") >= cutoff:
            items.append({"source":it.get("source",""),"title":it.get("title",""),
                          "url":it.get("link",""),"date":it.get("date",""),
                          "summary":(it.get("summary","") or "")[:250]})
    return items[:6]

def load_recent_history():
    """读 signals.db.daily_digest 表近 DEDUP_DAYS 天的 URL 集合 + 标题列表"""
    if not os.path.exists("data/signals.db"): return set(), []
    try:
        con = sqlite3.connect("data/signals.db")
        cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_digest'")
        if not cur.fetchone(): con.close(); return set(), []
        rows = con.execute("SELECT payload_json FROM daily_digest WHERE date >= date('now', ?)",
                           (f"-{DEDUP_DAYS} days",)).fetchall()
        con.close()
    except Exception as e:
        print(f"  ⚠ 读历史 digest 失败: {e}"); return set(), []
    urls, titles = set(), []
    for (p,) in rows:
        try: d = json.loads(p)
        except: continue
        for it in d.get("items", []):
            u = (it.get("url") or "").strip()
            if u: urls.add(u)
            for k in ("title_zh", "title_en"):
                t = (it.get(k) or "").strip()
                if t: titles.append(t)
    return urls, titles

def build_digest():
    print("═══ 抓最新源 ═══")
    arx = fetch_arxiv_recent();  print(f"  arXiv 近 {LOOKBACK_HOURS}h: {len(arx)} 篇")
    hn  = fetch_hn_hot();        print(f"  HN 高分: {len(hn)} 条")
    hf  = fetch_hf_trending();   print(f"  HF trending: {len(hf)} 个模型")
    bg  = fetch_blogs();         print(f"  blogs 近 {LOOKBACK_HOURS}h: {len(bg)} 篇")

    # 硬去重：拉近 DEDUP_DAYS 天讲过的 URL，过滤掉
    past_urls, past_titles = load_recent_history()
    print(f"\n═══ 近 {DEDUP_DAYS} 天历史 digest: {len(past_urls)} 个 URL / {len(past_titles)} 个标题 ═══")

    def keep(x):
        u = (x.get("url") or "").strip()
        return not u or u not in past_urls

    arx2 = [x for x in arx if keep(x)]; bg2 = [x for x in bg if keep(x)]
    hn2  = [x for x in hn  if keep(x)]; hf2 = [x for x in hf  if keep(x)]
    dropped = (len(arx)-len(arx2)) + (len(hn)-len(hn2)) + (len(hf)-len(hf2)) + (len(bg)-len(bg2))
    if dropped: print(f"  硬去重过滤掉 {dropped} 个旧 URL")

    all_items = []
    for i,x in enumerate(arx2): all_items.append(("arxiv",i,x))
    for i,x in enumerate(hn2):  all_items.append(("hn",i,x))
    for i,x in enumerate(hf2):  all_items.append(("hf",i,x))
    for i,x in enumerate(bg2):  all_items.append(("blog",i,x))

    if not all_items:
        print("⚠ 硬去重后无可用素材")
        return None
    if len(all_items) < 3:
        print(f"⚠ 去重后仅 {len(all_items)} 条候选, digest 可能不足 3 件")

    # 喂给 LLM
    lines = []
    for src, idx, x in all_items:
        head = f"[{src}#{idx}] {x.get('title','')[:130]}"
        meta = []
        if x.get("date"): meta.append(x["date"])
        if x.get("points"): meta.append(f"{x['points']}pts")
        if x.get("pipeline"): meta.append(x["pipeline"])
        head += " (" + " · ".join(meta) + ")" if meta else ""
        if x.get("summary"): head += " :: " + x["summary"][:160]
        lines.append(head)
    blob = "\n".join(lines)[:9500]

    # 软去重 prompt 段
    recent_block = ""
    if past_titles:
        sample = past_titles[:30]
        recent_block = f"""
RECENTLY COVERED (past {DEDUP_DAYS} days — AVOID same angle / restatement):
{json.dumps(sample, ensure_ascii=False)}

If today's candidates would just rehash one of these, DROP it and pick a fresher angle. Picking a related-but-genuinely-new development is fine; restating yesterday's news is not.
"""

    prompt = f"""You are NorthStar's editor. Your audience: engineers AT AN AI-NATIVE COMPANY (already shipping LLM products, sophisticated). They DO NOT need "learn AI basics" — they need "what does today change for me" signal.

Raw items collected in the past {LOOKBACK_HOURS}h:

{blob}
{recent_block}
TASK: Pick exactly 3 items that an AI-native engineer should NOT miss today. Output strict JSON:

{{
  "as_of": "{datetime.date.today().isoformat()}",
  "summary_one_line_zh": "<≤40字 中文一句话概括今天 AI 圈的主线>",
  "summary_one_line_en": "<≤15 word English one-line>",
  "items": [
    {{
      "rank": 1,
      "source_tag": "<arxiv#N | hn#N | hf#N | blog#N>",
      "title_zh": "<≤30字 中文标题, 可改写原标题让它更准>",
      "title_en": "<≤12 word English>",
      "why_zh": "<≤60字 为什么对 AI native 工程师重要 — 别说大白话>",
      "why_en": "<≤25 word English>",
      "so_what_zh": "<≤50字 你今天/本周可以做的具体一件事>",
      "so_what_en": "<≤20 word English>"
    }}
  ]
}}

Rules:
- Pick items that genuinely move the field forward OR signal a market shift — not me-too announcements.
- Mix sources: don't pick 3 arxiv papers. Aim for diversity (e.g., 1 paper + 1 community signal + 1 model/release).
- so_what_zh/en MUST be concrete — "重新评估你的 RAG pipeline" / "试用 X 替换 Y"，不要"关注 LLM 趋势"这种空话。
- Output JSON only."""

    print(f"\n═══ LLM ranking + 编辑 ({MODEL}) ═══")
    result, usage = llm(prompt)

    # 用 source_tag 反查原 URL（LLM 不抄 URL 更可靠）
    src_map = {}
    for src, idx, x in all_items:
        src_map[f"{src}#{idx}"] = x.get("url","")
    for item in result.get("items", []):
        tag = (item.get("source_tag") or "").strip()
        if tag in src_map:
            item["url"] = src_map[tag]
        else:
            item["url"] = ""

    print(f"  ✓ tokens: {usage.get('total_tokens')} · items: {len(result.get('items',[]))} · urls 回填 {sum(1 for x in result.get('items',[]) if x.get('url'))}")
    return result, all_items

def write_db(digest):
    con = sqlite3.connect("data/signals.db")
    con.execute("CREATE TABLE IF NOT EXISTS daily_digest(date TEXT PRIMARY KEY, payload_json TEXT, run_ts TEXT)")
    con.execute("INSERT OR REPLACE INTO daily_digest VALUES(?,?,?)",
                (digest["as_of"], json.dumps(digest, ensure_ascii=False),
                 datetime.datetime.now().isoformat(timespec="seconds")))
    con.commit(); con.close()

if __name__ == "__main__":
    out = build_digest()
    if not out:
        print("空 digest, 不写库"); sys.exit(0)
    digest, raw = out
    json.dump(digest, open("data/daily_digest_latest.json","w"), ensure_ascii=False, indent=1)
    write_db(digest)
    print(f"\n✓ data/daily_digest_latest.json + signals.db.daily_digest({digest['as_of']}) 已写")
    print(f"\n《今日 3 件事》:")
    for it in digest.get("items",[]):
        print(f"  {it['rank']}. [{it['source_tag']}] {it.get('title_zh','')}")
        print(f"     → {it.get('so_what_zh','')}")
