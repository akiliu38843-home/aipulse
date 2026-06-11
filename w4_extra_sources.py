"""W4+ 补真实源：arXiv 研究前沿(feedparser) + PyPI 库采纳(pypistats)。容错，单源失败不拖垮。"""
import json, datetime, urllib.request, feedparser

OUT = {"collected_at": datetime.datetime.now().isoformat(timespec="seconds")}

# ---- arXiv 研究前沿（免费 Atom API，无 key）----
arx = {"status": None, "papers": []}
try:
    url = ("http://export.arxiv.org/api/query?search_query="
           "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL"
           "&sortBy=submittedDate&sortOrder=descending&max_results=12")
    d = feedparser.parse(url, request_headers={"User-Agent": "NorthStar/0.4"})
    for e in d.entries[:12]:
        arx["papers"].append({
            "title": " ".join((e.get("title") or "").split()),
            "date": (e.get("published") or "")[:10],
            "authors": ", ".join(a.get("name","") for a in (e.get("authors") or [])[:3]),
            "summary": " ".join((e.get("summary") or "").split())[:200],
            "link": e.get("link",""),
        })
    arx["status"] = f"ok:{len(arx['papers'])}"
except Exception as ex:
    arx["status"] = f"FAIL:{type(ex).__name__}:{str(ex)[:100]}"
OUT["arxiv"] = arx

# ---- PyPI 库采纳（pypistats 免费 JSON API）----
pkgs = ["langchain", "openai", "anthropic", "transformers", "vllm",
        "llama-index", "langgraph", "crewai", "huggingface-hub", "litellm"]
pj = {"status": None, "libs": []}
ok = 0
for p in pkgs:
    try:
        req = urllib.request.Request(f"https://pypistats.org/api/packages/{p}/recent",
                                     headers={"User-Agent": "NorthStar/0.4"})
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.load(r)
        dd = j.get("data", {})
        pj["libs"].append({"pkg": p, "last_month": dd.get("last_month"),
                           "last_week": dd.get("last_week")})
        ok += 1
    except Exception as ex:
        pj["libs"].append({"pkg": p, "error": f"{type(ex).__name__}:{str(ex)[:60]}"})
pj["libs"].sort(key=lambda x: -(x.get("last_month") or 0))
pj["status"] = f"ok:{ok}/{len(pkgs)}"
OUT["pypi"] = pj

json.dump(OUT, open("data/w4_extra.json", "w"), ensure_ascii=False, indent=1)
print("arXiv:", arx["status"],
      "| sample:", (arx["papers"][0]["title"][:70] if arx["papers"] else "-"))
print("PyPI:", pj["status"],
      "| top:", [(l["pkg"], l.get("last_month")) for l in pj["libs"][:5] if "error" not in l])
