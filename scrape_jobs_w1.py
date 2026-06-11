"""W1 现状采集 — 北美 AI Engineer 招聘抓取（容错：单源失败不拖垮整体）"""
import sys, json, datetime, traceback
import pandas as pd
from jobspy import scrape_jobs

OUT_CSV = "data/jobs_raw.csv"
OUT_JSON = "data/jobs_w1.json"
SEARCH = "AI Engineer"
LOCATION = "United States"
PER_SITE = 35

frames = []
site_status = {}
for site in ["indeed", "google", "linkedin"]:
    try:
        kw = dict(site_name=[site], search_term=SEARCH, location=LOCATION,
                  results_wanted=PER_SITE, hours_old=720, country_indeed="USA",
                  verbose=0)
        if site == "google":
            kw["google_search_term"] = "AI Engineer jobs United States"
        df = scrape_jobs(**kw)
        n = 0 if df is None else len(df)
        site_status[site] = f"ok:{n}"
        if n:
            df["_src"] = site
            frames.append(df)
    except Exception as e:
        site_status[site] = f"FAIL:{type(e).__name__}:{str(e)[:120]}"

if not frames:
    print(json.dumps({"error": "all sites returned nothing", "site_status": site_status}, ensure_ascii=False))
    sys.exit(1)

jobs = pd.concat(frames, ignore_index=True)
# 去重（同公司+同标题）
before = len(jobs)
jobs = jobs.drop_duplicates(subset=[c for c in ["title", "company"] if c in jobs.columns]).reset_index(drop=True)
jobs.to_csv(OUT_CSV, index=False)

cols = [c for c in ["title","company","location","is_remote","min_amount","max_amount",
                    "interval","currency","date_posted","job_url","description","_src"] if c in jobs.columns]
recs = jobs[cols].fillna("").to_dict(orient="records")
# description 截断，控体积
for r in recs:
    d = str(r.get("description",""))
    r["description"] = d[:4000]
payload = {
    "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "search_term": SEARCH, "location": LOCATION,
    "site_status": site_status,
    "raw_count": before, "dedup_count": len(jobs),
    "jobs": recs,
}
# 原子写：先写 .tmp 再 rename。避免半截写入污染下游（CI 上 scrape 失败也不破坏旧 json）
# default=str：JobSpy 返回的 date 对象转字符串
import os as _os
_tmp = OUT_JSON + ".tmp"
json.dump(payload, open(_tmp,"w"), ensure_ascii=False, indent=1, default=str)
_os.replace(_tmp, OUT_JSON)
print(json.dumps({"site_status": site_status, "raw": before, "dedup": len(jobs),
                  "with_desc": sum(1 for r in recs if r["description"].strip()),
                  "sample_titles": [r["title"] for r in recs[:8]]}, ensure_ascii=False, indent=1))
