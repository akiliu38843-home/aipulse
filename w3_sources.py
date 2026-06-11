"""W3 — 接 HF Hub(采纳曲线) + Hacker News(招聘盲区/热度) 两源，写 signals.db"""
import json, datetime, urllib.request, urllib.parse, collections, re, sqlite3, hashlib
from huggingface_hub import HfApi

OUT = {"collected_at": datetime.datetime.now().isoformat(timespec="seconds")}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NorthStar/0.3"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

# ---------- HF Hub：采纳曲线（trending + 高下载，看 pipeline_tag 分布）----------
hf = {"trending": [], "tag_freq": {}}
try:
    api = HfApi()
    models = list(api.list_models(sort="trendingScore", direction=-1, limit=30, fetch_config=False))
    tags = collections.Counter()
    for m in models:
        pt = getattr(m, "pipeline_tag", None) or "unknown"
        tags[pt] += 1
        hf["trending"].append({"id": m.id, "pipeline": pt,
                               "downloads": getattr(m, "downloads", None),
                               "likes": getattr(m, "likes", None)})
    hf["tag_freq"] = dict(tags.most_common())
    hf["status"] = f"ok:{len(models)}"
except Exception as e:
    hf["status"] = f"FAIL:{type(e).__name__}:{str(e)[:120]}"
OUT["hf"] = hf

# ---------- Hacker News（Algolia API，无 key）----------
hn = {}
try:
    s = get("https://hn.algolia.com/api/v1/search?query=" +
            urllib.parse.quote("Ask HN: Who is hiring?") + "&tags=story&hitsPerPage=6")
    whoishiring = None
    for h in s.get("hits", []):
        t = (h.get("title") or "")
        if "who is hiring" in t.lower() and "ask hn" in t.lower():
            whoishiring = h; break
    hn["thread"] = {"title": whoishiring.get("title"), "objectID": whoishiring.get("objectID"),
                    "created": whoishiring.get("created_at")} if whoishiring else None
    SKILL = ["LLM","agent","RAG","eval","prompt","PyTorch","Python","TypeScript","Rust",
             "Kubernetes","inference","fine-tun","multimodal","vLLM","MLOps","Claude","Codex","Cursor"]
    skill_hits = collections.Counter(); n_comments = 0
    if whoishiring:
        sid = whoishiring["objectID"]
        c = get(f"https://hn.algolia.com/api/v1/search?tags=comment,story_{sid}&hitsPerPage=200")
        for cm in c.get("hits", []):
            txt = (cm.get("comment_text") or "")
            if not txt: continue
            n_comments += 1
            low = txt.lower()
            for k in SKILL:
                if k.lower() in low: skill_hits[k] += 1
    hn["who_is_hiring_comments"] = n_comments
    hn["skill_freq_in_hiring"] = dict(skill_hits.most_common())
    # AI 话题热度（近 35 天高分 story）
    import time
    since = int(time.time()) - 35*86400
    heat = get("https://hn.algolia.com/api/v1/search?query=" + urllib.parse.quote("AI agent LLM") +
               f"&tags=story&numericFilters=created_at_i>{since},points>80&hitsPerPage=15")
    hn["hot_ai_stories"] = [{"title": h.get("title"), "points": h.get("points"),
                             "url": h.get("url")} for h in heat.get("hits", [])][:12]
    hn["status"] = "ok"
except Exception as e:
    hn["status"] = f"FAIL:{type(e).__name__}:{str(e)[:120]}"
OUT["hn"] = hn

json.dump(OUT, open("data/w3_sources.json", "w"), ensure_ascii=False, indent=1)

# ---------- 写 signals.db ----------
con = sqlite3.connect("data/signals.db")
RUN = datetime.datetime.now().isoformat(timespec="seconds")
def put(theme, raw, st, sn):
    sid = hashlib.md5(f"{theme}|{st}|{sn}|{raw[:60]}".encode()).hexdigest()[:16]
    con.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?,?,?)",
                (sid, theme, raw[:400], st, sn, "", "", "", RUN))
# HF pipeline_tag → 主题（取前几类）
PT2THEME = {"text-generation":"LLM/生成式AI应用","text-to-image":"多模态",
 "image-text-to-text":"多模态","automatic-speech-recognition":"多模态",
 "feature-extraction":"RAG","sentence-similarity":"RAG","text-ranking":"RAG",
 "any-to-any":"多模态","image-to-video":"多模态","robotics":"具身/机器人AI"}
for pt, cnt in hf.get("tag_freq", {}).items():
    th = PT2THEME.get(pt)
    if th: put(th, f"HF trending pipeline={pt} x{cnt}", "hf", "HuggingFace Hub")
for k, v in hn.get("skill_freq_in_hiring", {}).items():
    if v >= 3:
        m = {"agent":"AI Agents/编排","RAG":"RAG","eval":"Eval 评测","LLM":"LLM/生成式AI应用",
             "Claude":"AI编码agent当硬技能","Codex":"AI编码agent当硬技能","Cursor":"AI编码agent当硬技能",
             "inference":"Serving 推理","vLLM":"Serving 推理","MLOps":"MLOps/LLMOps"}.get(k)
        if m: put(m, f"HN Who-is-hiring 提及 {k} x{v}", "hn", "HackerNews Who-is-hiring")
con.commit()
con.execute("INSERT INTO snapshots(run_ts,kind,payload_json) VALUES(?,?,?)",
            (RUN,"w3-hf-hn", json.dumps(OUT, ensure_ascii=False)))
con.commit()
print("HF:", hf["status"], "| tags:", json.dumps(hf.get("tag_freq",{}), ensure_ascii=False)[:200])
print("HN:", hn["status"], "| who-is-hiring comments:", hn.get("who_is_hiring_comments"),
      "| skill_freq:", json.dumps(hn.get("skill_freq_in_hiring",{}), ensure_ascii=False)[:220])
print("HN hot stories:", len(hn.get("hot_ai_stories",[])))
print("signals now:", con.execute("SELECT source_type,count(*) FROM signals GROUP BY source_type").fetchall())
con.close()
