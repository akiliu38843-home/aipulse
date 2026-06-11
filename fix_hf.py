"""修 HF：huggingface_hub 1.15 去掉了 direction/fetch_config 参数"""
import json, datetime, collections, sqlite3, hashlib
from huggingface_hub import HfApi

api = HfApi()
models, used = [], None
for sort_key in ("trendingScore", "trending_score", "downloads", "likes"):
    try:
        models = list(api.list_models(sort=sort_key, limit=30))
        used = sort_key
        if models: break
    except Exception as e:
        last = f"{type(e).__name__}:{str(e)[:90]}"
if not models:
    print("HF still FAIL:", last); raise SystemExit(1)

tags = collections.Counter(); trending = []
for m in models:
    pt = getattr(m, "pipeline_tag", None) or "unknown"
    tags[pt] += 1
    trending.append({"id": m.id, "pipeline": pt,
                     "downloads": getattr(m, "downloads", None),
                     "likes": getattr(m, "likes", None)})
tag_freq = dict(tags.most_common())

# 合并进 w3_sources.json
d = json.load(open("data/w3_sources.json"))
d["hf"] = {"status": f"ok:{len(models)} sort={used}", "tag_freq": tag_freq, "trending": trending}
json.dump(d, open("data/w3_sources.json", "w"), ensure_ascii=False, indent=1)

# 写 signals.db
con = sqlite3.connect("data/signals.db")
RUN = datetime.datetime.now().isoformat(timespec="seconds")
PT2 = {"text-generation":"LLM/生成式AI应用","text-to-image":"多模态","image-text-to-text":"多模态",
 "automatic-speech-recognition":"多模态","feature-extraction":"RAG","sentence-similarity":"RAG",
 "text-ranking":"RAG","any-to-any":"多模态","image-to-video":"多模态","video-text-to-text":"多模态",
 "robotics":"具身/机器人AI","text-to-speech":"多模态","image-to-text":"多模态"}
for pt, cnt in tag_freq.items():
    th = PT2.get(pt)
    if th:
        sid = hashlib.md5(f"{th}|hf|HF|{pt}".encode()).hexdigest()[:16]
        con.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?,?,?)",
                     (sid, th, f"HF trending pipeline={pt} x{cnt}", "hf", "HuggingFace Hub","", "", "", RUN))
con.commit()
print("HF ok sort=%s | tag_freq=%s" % (used, json.dumps(tag_freq, ensure_ascii=False)[:260]))
print("top trending ids:", [t["id"] for t in trending[:8]])
print("signals now:", con.execute("SELECT source_type,count(*) FROM signals GROUP BY source_type").fetchall())
con.close()
