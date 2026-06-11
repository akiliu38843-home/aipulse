"""W2 前瞻·思想领袖 — RSS 抓 AI 明星/实验室博客近 90 天文章（容错，单源失败不拖垮）"""
import json, re, datetime, time, urllib.request
import feedparser

FEEDS = {
 "Simon Willison":      "https://simonwillison.net/atom/everything/",
 "Lilian Weng":         "https://lilianweng.github.io/index.xml",
 "Sebastian Raschka":   "https://magazine.sebastianraschka.com/feed",
 "HuggingFace Blog":    "https://huggingface.co/blog/feed.xml",
 "Chip Huyen":          "https://huyenchip.com/feed.xml",
 "Eugene Yan":          "https://eugeneyan.com/rss/",
 "Jay Alammar":         "https://jalammar.github.io/feed.xml",
 "Berkeley BAIR":       "https://bair.berkeley.edu/blog/feed.xml",
 "The Gradient":        "https://thegradient.pub/rss/",
 "DeepLearning.AI Batch":"https://www.deeplearning.ai/the-batch/feed/",
 "OpenAI News":         "https://openai.com/news/rss.xml",
 "Google Research":     "https://research.google/blog/rss/",
 "Anthropic News":      "https://www.anthropic.com/rss.xml",
 "Sebastian Ruder":     "https://www.ruder.io/rss/",
}
CUTOFF = time.time() - 90*86400
def clean(s): return " ".join(re.sub(r"<[^>]+>", " ", s or "").split())

out = {"collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
       "source_status": {}, "items": []}
for name, url in FEEDS.items():
    try:
        d = feedparser.parse(url, request_headers={"User-Agent":"Mozilla/5.0 NorthStar"})
        n = 0
        for e in d.entries[:8]:
            tp = e.get("published_parsed") or e.get("updated_parsed")
            ts = time.mktime(tp) if tp else None
            if ts and ts < CUTOFF:
                continue
            out["items"].append({
                "source": name,
                "title": clean(e.get("title","")),
                "date": time.strftime("%Y-%m-%d", tp) if tp else "",
                "summary": clean(e.get("summary",""))[:600],
                "link": e.get("link",""),
            })
            n += 1
        out["source_status"][name] = (f"ok:{n}" if (n or d.entries) else "empty") + \
            ("" if d.entries else f" (bozo:{getattr(d,'bozo',0)})")
    except Exception as ex:
        out["source_status"][name] = f"FAIL:{type(ex).__name__}:{str(ex)[:90]}"

json.dump(out, open("data/blogs_w2.json","w"), ensure_ascii=False, indent=1)
ok = sum(1 for v in out["source_status"].values() if v.startswith("ok"))
print(json.dumps(out["source_status"], ensure_ascii=False, indent=1))
print(f"--- feeds_ok={ok}/{len(FEEDS)}  items_collected={len(out['items'])} ---")
