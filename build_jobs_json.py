"""从已抓的 CSV 修复出 W1 JSON（date 用 str 兜底，不重新抓）"""
import json, datetime, pandas as pd

d = pd.read_csv("data/jobs_raw.csv")
before = len(d)
d = d.drop_duplicates(subset=[c for c in ["title","company"] if c in d.columns]).reset_index(drop=True)

cols = [c for c in ["title","company","location","is_remote","min_amount","max_amount",
                    "interval","currency","date_posted","job_url","site","description"] if c in d.columns]
recs = d[cols].fillna("").to_dict(orient="records")
for r in recs:
    r["description"] = str(r.get("description",""))[:4000]
    for k,v in list(r.items()):
        if not isinstance(v,(str,int,float,bool)): r[k]=str(v)

payload = {
    "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "search_term":"AI Engineer","location":"United States",
    "raw_count":before,"dedup_count":len(d),
    "site_breakdown": d["site"].value_counts().to_dict() if "site" in d else {},
    "jobs":recs,
}
json.dump(payload, open("data/jobs_w1.json","w"), ensure_ascii=False, indent=1, default=str)
print("dedup", len(d), "of", before,
      "| with_desc", sum(1 for r in recs if r["description"].strip()),
      "| remote", sum(1 for r in recs if str(r.get("is_remote")).lower() in("true","1")),
      "| with_salary", sum(1 for r in recs if str(r.get("min_amount")).strip() not in("","nan","0","0.0")))
