"""W3+ ②H-1B 全量：USCIS Employer Data Hub CSV → 过滤 AI 公司 → top sponsors + 3 年趋势。

CSV 列: "Fiscal Year",Employer,"Initial Approval","Initial Denial","Continuing Approval","Continuing Denial",NAICS,"Tax ID",State,City,ZIP
- Initial Approval = 新 H-1B 批准（最有价值的 sponsor 信号，"刚招进来给办新签证的"）
- Continuing Approval = 续签批准

AI 公司识别 = 硬品牌名单 + 关键词。FY2023 是最新完整年，FY2021-2023 三年看趋势。
"""
import csv, json, io, re, subprocess, datetime, collections, os

YEARS = [2021, 2022, 2023]
CSV_URL = "https://www.uscis.gov/sites/default/files/document/data/h1b_datahubexport-{year}.csv"

# AI 关键词正则（在公司全名里命中即算 AI 相关）
AI_KEYWORDS = re.compile(r"(?i)(\bAI\b|\bA\.I\.\b|ARTIFICIAL INTELLIGENCE|MACHINE LEARNING|DEEP LEARNING|\bDATA SCIENCE|ROBOTIC INTELLIGENCE)")

# AI 品牌硬名单（大写匹配，子串包含即算）— AI native 公司 + 大厂(AI 业务非常显著的)
AI_BRANDS = {
    # AI native
    "OPENAI","ANTHROPIC","HUGGING FACE","HUGGINGFACE","SCALE AI","COHERE","MISTRAL",
    "INFLECTION","ADEPT","CHARACTER.AI","PERPLEXITY","REKA AI",
    "RUNWAY","STABILITY AI","JASPER","MIDJOURNEY",
    "DATABRICKS","SNOWFLAKE","WEAVIATE","PINECONE",
    "DEEPMIND","XAI ","X.AI",
    "MOSAIC","WEIGHTS & BIASES","WEIGHTS AND BIASES",
    "REPLICATE","TOGETHER AI","FIREWORKS AI","GROQ","CEREBRAS","SAMBANOVA",
    "ROBOFLOW","LANGCHAIN","CREW",
    # 大厂（AI 业务凸显）
    "NVIDIA","GOOGLE","ALPHABET","META PLATFORMS","MICROSOFT","AMAZON",
    "APPLE INC","TESLA INC","SALESFORCE","ORACLE","INTEL",
    "PALANTIR","ADOBE","NETFLIX","UBER","AIRBNB",
    "C3.AI","C3 AI",
}
def is_ai_employer(name: str) -> bool:
    n = (name or "").upper()
    if AI_KEYWORDS.search(name or ""): return True
    return any(b in n for b in AI_BRANDS)

def norm_name(name: str) -> str:
    """归一化雇主名：合并 AMAZON COM/AMAZON.COM 等同体变体。
    去掉点/逗号/多余空格，统一大写，再去掉法律实体后缀。"""
    n = re.sub(r"[.,]", " ", (name or "").upper())
    n = re.sub(r"\s+", " ", n).strip()
    n = re.sub(r"\b(LLC|INC|CORPORATION|CORP|LTD|LP|LLP|LIMITED|HOLDINGS|GROUP|SERVICES|CO|COMPANY)\b", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n

def fetch_csv(year: int, max_retry: int = 3) -> str | None:
    """curl 下载（urllib + 7897 代理偶发 SSL EOF；curl 稳）+ 重试"""
    import time as _t
    url = CSV_URL.format(year=year)
    for attempt in range(max_retry):
        r = subprocess.run(
            ["curl","-s","-m","60","-A","Mozilla/5.0 NorthStar",url],
            capture_output=True, timeout=70)
        if r.returncode == 0:
            text = r.stdout.decode("utf-8","replace")
            if len(text) >= 1000 and "<!DOCTYPE html>" not in text[:200]:
                return text
        if attempt < max_retry - 1:
            _t.sleep(2 ** attempt)
    return None

def parse_year(year: int):
    text = fetch_csv(year)
    if not text:
        print(f"  ✗ FY{year}: 下载失败/HTML fallback"); return None
    reader = csv.DictReader(io.StringIO(text))
    by_emp = collections.defaultdict(lambda: {"display":"","init":0,"init_d":0,"cont":0,"cont_d":0,
                                                "states":collections.Counter(),"naics":"","city":""})
    total_rows = 0
    for row in reader:
        total_rows += 1
        name = (row.get("Employer") or "").strip()
        if not name or not is_ai_employer(name): continue
        key = norm_name(name)
        e = by_emp[key]
        # 用最长的原始名作为 display（一般更完整）
        if len(name) > len(e["display"]): e["display"] = name
        def num(k):
            v = row.get(k,"") or "0"
            try: return int(v.replace(",",""))
            except: return 0
        e["init"]  += num("Initial Approval")
        e["init_d"]+= num("Initial Denial")
        e["cont"]  += num("Continuing Approval")
        e["cont_d"]+= num("Continuing Denial")
        st = (row.get("State","") or "").strip()
        if st: e["states"][st] += 1
        if not e["naics"]: e["naics"] = (row.get("NAICS","") or "").strip()
        if not e["city"]:  e["city"]  = (row.get("City","") or "").strip()
    print(f"  ✓ FY{year}: 解析 {total_rows} 行 → {len(by_emp)} 家 AI 雇主(归一后), 新批 {sum(e['init'] for e in by_emp.values())}")
    return by_emp, total_rows

def main():
    out = {"as_of": str(datetime.date.today()), "fiscal_years": {}}
    agg = collections.defaultdict(lambda: {"init_total":0, "cont_total":0, "by_year":{}, "state_top":"", "naics":"", "city":""})
    yearly_ai_total = {}

    rows_per_year = {}
    for y in YEARS:
        r = parse_year(y)
        if not r: continue
        emps, total_rows = r
        rows_per_year[f"FY{y}"] = total_rows
        yearly_init = sum(e["init"] for e in emps.values())
        yearly_ai_total[f"FY{y}"] = yearly_init
        out["fiscal_years"][f"FY{y}"] = {"n_ai_employers": len(emps), "n_initial_approvals": yearly_init, "csv_total_rows": total_rows}
        for key, e in emps.items():
            a = agg[key]
            a["display"] = e["display"] if len(e["display"]) > len(a.get("display","")) else a.get("display","")
            a["init_total"] += e["init"]
            a["cont_total"] += e["cont"]
            a["by_year"][f"FY{y}"] = e["init"]
            if not a["state_top"] and e["states"]:
                a["state_top"] = e["states"].most_common(1)[0][0]
            if not a["naics"]: a["naics"] = e["naics"]
            if not a["city"]:  a["city"]  = e["city"]
    # FY2023 完整性诊断（FY2021/2022 通常 ~60k 行；FY2023 若 < 50k 可能仍是部分数据）
    max_rows = max(rows_per_year.values()) if rows_per_year else 1
    out["data_completeness"] = {
        f"FY{y}": {"rows": rows_per_year.get(f"FY{y}",0),
                    "pct_of_max": round(rows_per_year.get(f"FY{y}",0)/max_rows*100,1)}
        for y in YEARS if f"FY{y}" in rows_per_year}

    # Top 25 sponsors by 3-year initial approvals
    top = sorted(agg.items(), key=lambda x:-x[1]["init_total"])[:25]
    out["top_sponsors"] = [
        {"name": (d.get("display") or k).strip(),
         "initial_3y": d["init_total"],
         "by_year": d["by_year"],
         "state_top": d["state_top"],
         "city": d["city"],
         "naics": d["naics"]}
        for k,d in top]
    out["trend_ai_initial_by_fy"] = yearly_ai_total
    out["summary"] = {
        "n_ai_employers_3y": len(agg),
        "total_initial_3y": sum(d["init_total"] for d in agg.values()),
        "fiscal_years_loaded": list(out["fiscal_years"].keys()),
    }
    os.makedirs("data", exist_ok=True)
    json.dump(out, open("data/h1b_ai.json","w"), ensure_ascii=False, indent=1)
    print(f"\n✓ data/h1b_ai.json: top {len(top)} sponsors · {len(agg)} AI 雇主 (3 年) · {out['summary']['total_initial_3y']} 初次批准合计")
    print("\nTop 8 AI sponsors (3 年初次批准合计):")
    for s in out["top_sponsors"][:8]:
        yrs = "/".join(str(s["by_year"].get(f"FY{y}",0)) for y in YEARS)
        print(f"  {s['name'][:48]:<50}{s['initial_3y']:>5} ({yrs}) · {s['state_top']} {s['city'][:15]}")

if __name__ == "__main__":
    main()
