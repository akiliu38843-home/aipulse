"""W2 前瞻·企业 — 抓北美 AI 公司最新 10-K，抽 AI 战略/R&D 相关段落（容错，单公司失败不拖垮）"""
import sys, json, re, datetime, traceback
from edgar import Company, set_identity

set_identity("NorthStar Research FrankieBuckleydrd@post.com")

TICKERS = ["NVDA", "MSFT", "PLTR", "META"]
KW = re.compile(r"(artificial intelligence|machine learning|generative|\bAI\b|\bLLM\b|"
                r"large language model|deep learning|foundation model|research and development|"
                r"R&D|data center|accelerat|inference|GPU)", re.I)

out = {"collected_at": datetime.datetime.now().isoformat(timespec="seconds"), "companies": {}}
for tk in TICKERS:
    rec = {"status": None, "filing_date": None, "excerpts": []}
    try:
        c = Company(tk)
        filings = c.get_filings(form="10-K")
        latest = filings.latest(1)
        rec["filing_date"] = str(getattr(latest, "filing_date", ""))
        text = ""
        # 多版本兜底取正文
        for getter in ("markdown", "text"):
            try:
                obj = latest.obj()
                if hasattr(obj, getter):
                    text = getattr(obj, getter)() if callable(getattr(obj, getter)) else getattr(obj, getter)
                    if text: break
            except Exception:
                pass
        if not text:
            try: text = latest.text()
            except Exception:
                try: text = latest.markdown()
                except Exception: text = ""
        if not text:
            rec["status"] = "no-text"
            out["companies"][tk] = rec; continue
        # 切段，留含 AI/R&D 关键词的，去重，控量
        paras = re.split(r"\n\s*\n", text)
        seen, picked, total = set(), [], 0
        for p in paras:
            p = " ".join(p.split())
            if 120 <= len(p) <= 1200 and KW.search(p):
                h = p[:80]
                if h in seen: continue
                seen.add(h); picked.append(p); total += len(p)
                if total > 11000: break
        rec["status"] = f"ok:{len(picked)}paras"
        rec["excerpts"] = picked
    except Exception as e:
        rec["status"] = f"FAIL:{type(e).__name__}:{str(e)[:140]}"
    out["companies"][tk] = rec

json.dump(out, open("data/edgar_w2.json", "w"), ensure_ascii=False, indent=1)
for tk, r in out["companies"].items():
    print(tk, r["status"], "filing", r["filing_date"], "| excerpt_chars",
          sum(len(x) for x in r["excerpts"]))
