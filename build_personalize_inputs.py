"""Build data/personalize_inputs.json — 给 api/personalize.py 用的精简数据
（不暴露完整 signals.db；只导出 LLM prompt 需要的真实数字）"""
import json, sqlite3, statistics, collections, datetime, re

con = sqlite3.connect("data/signals.db")
fore = [{"theme": c, "sources": n}
        for c, n in con.execute(
            "SELECT canonical, n_src FROM ontology WHERE layer='foresight' ORDER BY n_src DESC").fetchall()
        if n >= 2]
con.close()

# JD top skills（W1 抽取定稿）— 与 build_news/build_site 同源
JD_TOP=["Python","AWS/Azure 云","LLM/生成式AI应用","Docker/Kubernetes","TypeScript/Node","SQL",
        "AI Agents/编排","Eval 评测","RAG","Prompt engineering","MLOps/LLMOps","AI系统可观测性/成本"]
BASELINE=["Python","SQL","Docker/Kubernetes","AWS/Azure 云","LLM/生成式AI应用"]

# 薪资 + 远程 + top hirers（从 jobs_w1.json 实时算）
jw=json.load(open("data/jobs_w1.json"))
sal=[]; remote_n=0; cos=[]; ai_jobs=0
AI=re.compile(r"(?i)(\bAI\b|\bML\b|\bLLM\b|Machine Learning|Data Scientist|Applied Scientist|Research Scientist|Data Engineer|MLOps|Generative|Forward Deployed|Prompt Engineer|AI[/\s-]?Native)")
BLK=re.compile(r"(?i)(DevSecOps|Apriso|Dynamics 365|S1000D|Technical Author|Sourcer|Recruiter|Account Executive|Head of (Business )?Operations|Facilities|Electrical Engineer|Software Engineering Internship|Cloud Platform Specialist)")
for j in jw.get("jobs") or []:
    t=str(j.get("title","")); brief=str(j.get("description",""))[:520].lower()
    if BLK.search(t): continue
    if not (AI.search(t) or sum(1 for k in ("ai ","llm","machine learning","agent","generative","prompt","rag","embedding","fine-tun") if k in brief)>=3): continue
    ai_jobs+=1
    if str(j.get("is_remote")).lower() in ("true","1"): remote_n+=1
    co=str(j.get("company","")).strip()
    if co: cos.append(co)
    try:
        lo=float(j.get("min_amount") or 0); hi=float(j.get("max_amount") or 0)
        if lo>1000 and str(j.get("interval","")).startswith("year"): sal.append((lo+hi)/2)
    except: pass

this_week_med=int(statistics.median(sal)) if sal else 0
top_co=[c for c,_ in collections.Counter(cos).most_common(5)]
# 薪资稳定 baseline：W1 实测 ($185k median, $63-267k, n=22)。单周噪声大故 anchor 它。
BASELINE_SALARY={"median_k":185, "low_k":63, "high_k":267, "n":22, "remote_pct":11,
                 "source":"W1 (2026-05-19, 63 岗样本中 22 个有 yearly salary)"}

# 常见目标岗（从真实 JD 标题里抽 + 加上常见缺失项）
title_keys=("AI Engineer","ML Engineer","Machine Learning Engineer","Data Scientist","Applied Scientist",
            "Research Scientist","Data Engineer","Forward Deployed AI","MLOps Engineer","AI/ML Engineer",
            "Applied AI Engineer","AI Native Engineer","Prompt Engineer","AI Solutions Architect","AI Product Manager")
seen_titles=set()
for j in jw.get("jobs") or []:
    t=str(j.get("title",""))
    for k in title_keys:
        if k.lower() in t.lower(): seen_titles.add(k); break
target_roles=sorted(seen_titles) or ["AI Engineer","ML Engineer","Data Scientist","Applied Scientist"]

out={
 "as_of": datetime.date.today().isoformat(),
 "foresight": fore,
 "baseline_skills": BASELINE,
 "jd_top_skills": JD_TOP,
 "salary": BASELINE_SALARY,
 "salary_this_week_snapshot": {"median_k": this_week_med//1000, "n": len(sal),
                                "note": "本周样本量不稳，仅辅助参考；以 salary baseline 为准"},
 "top_employers": top_co,
 "target_roles": target_roles,
 "ai_jobs_total": ai_jobs,
}
json.dump(out, open("data/personalize_inputs.json","w"), ensure_ascii=False, indent=1)
print(f"✓ data/personalize_inputs.json · fore={len(fore)} · jd_skills={len(JD_TOP)} · sal_baseline=${BASELINE_SALARY['median_k']}k(n={BASELINE_SALARY['n']}) · this_week_med=${this_week_med//1000}k(n={len(sal)}) · roles={len(target_roles)} · ai_jobs={ai_jobs}")
