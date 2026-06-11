"""W3-W4 欠账清理：用 LLM 真做 ① ENT 战略抽取 ② BLOG 主题聚类 ③ 主题归一(ALIAS map)。
读 DEEPSEEK_API_KEY env。

替换：
  - add_llm_signals.py 里硬编码的 ENT 4 家一句话 + BLOG 三大焦点
  - theme_ontology.py 里手工维护的 ALIAS 字典 → 写入 signals.db.alias_map 表

调用：python3 llm_extract.py [--dry-run]   失败时不写库，原样保留旧 signals
"""
import json, os, sys, sqlite3, datetime, urllib.request, urllib.error, hashlib

MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com/v1"
TIMEOUT = 60
DRY = "--dry-run" in sys.argv

def get_key():
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key: return key
    return None

KEY = get_key()
if not KEY:
    # CI 没配 secret 时 graceful skip，不让 workflow 整个 fail
    print("⚠ DEEPSEEK_API_KEY not configured — skip llm_extract")
    print("  signals.db.enterprise/blog/alias_map 保留上次跑的结果，theme_ontology.py 会 fallback 到 hardcoded ALIAS")
    sys.exit(0)

import time, subprocess
def llm(prompt, schema_hint="", max_retry=3):
    """通过 subprocess curl 调 LLM"""
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role":"system","content":"You output strict JSON only. No markdown, no prose."+(f"\nExpected: {schema_hint}" if schema_hint else "")},
            {"role":"user","content":prompt}
        ]
    }, ensure_ascii=False)
    last_err = None
    for attempt in range(max_retry):
        try:
            r = subprocess.run(
                ["curl","-s","-m",str(TIMEOUT),
                 "-H",f"Authorization: Bearer {KEY}",
                 "-H","Content-Type: application/json",
                 "-X","POST",
                 f"{BASE_URL}/chat/completions",
                 "--data-binary","@-"],
                input=body, capture_output=True, text=True, timeout=TIMEOUT+5)
            if r.returncode != 0 or not r.stdout.strip():
                raise RuntimeError(f"curl rc={r.returncode}: {(r.stderr or r.stdout)[:160]}")
            resp = json.loads(r.stdout)
            if "error" in resp:
                raise RuntimeError(f"LLM err: {resp['error']}")
            content = resp["choices"][0]["message"]["content"]
            return json.loads(content), resp.get("usage", {})
        except Exception as e:
            last_err = e
            if attempt < max_retry - 1:
                time.sleep(2 ** attempt)
                continue
    raise last_err

# ════════════ ① ENT 战略抽取 ════════════
def extract_enterprise():
    edg = json.load(open("data/edgar_w2.json"))
    out = {}
    for tk, rec in edg.get("companies", {}).items():
        if "error" in str(rec.get("status","")): continue
        # 取每段前 280 字, 拼最多 10 段 -> 控总长 < 3500 字（代理 7897 容易掐大包）
        excerpts = "\n\n".join(p[:280] for p in (rec.get("excerpts") or [])[:10])[:3500]
        if not excerpts: continue
        time.sleep(1.5)   # 给代理喘息
        prompt = f"""Read this Fortune 100 company's recent 10-K filing excerpts, extract their AI strategy.

Ticker: {tk}
Filing date: {rec.get("filing_date","")}
Excerpts:
{excerpts}

Output strict JSON:
{{
  "name": "<full company name>",
  "ai_strategy_one_line_zh": "<≤60字中文一句话总结其 AI 战略重心>",
  "ai_strategy_one_line_en": "<≤25 word English summary>",
  "canonical_theme": "<one of: Agents/Eval/Serving/Multimodal/RAG/AI Safety/Foundation Models/Enterprise AI Platform>",
  "concrete_bets": [<2-3 short concrete bet phrases, e.g., 'CUDA software stack', 'AIP platform'>]
}}"""
        try:
            r, u = llm(prompt, "company AI strategy JSON")
            out[tk] = r; out[tk]["_usage"] = u
            print(f"  ✓ {tk}: {r.get('canonical_theme','-')} · {r.get('ai_strategy_one_line_zh','')[:40]}…")
        except Exception as e:
            print(f"  ✗ {tk}: {type(e).__name__}: {str(e)[:80]}")
            out[tk] = {"error": str(e)}
    return out

# ════════════ ② BLOG 主题聚类 ════════════
def cluster_blogs():
    blg = json.load(open("data/blogs_w2.json"))
    items = blg.get("items") or []
    # 给 LLM 看 title+summary（精简）
    lines = []
    for i, it in enumerate(items[:50]):
        s = (it.get("summary") or "")[:120].replace("\n"," ")
        lines.append(f"{i+1}. [{it.get('source')}] {it.get('title')[:90]}  ::  {s}")
    blob = "\n".join(lines)[:9000]
    prompt = f"""You have {len(items)} recent AI-focused blog/news articles. Cluster them into 3-5 dominant themes this issue.

Articles:
{blob}

Output strict JSON:
{{
  "themes": [
    {{
      "name_zh": "<≤8字主题名>",
      "name_en": "<≤4 word theme name>",
      "canonical_signal": "<one of: AI Agents/编排, Eval 评测, RAG, Serving 推理, 多模态, AI安全/Responsible AI, AI编码agent当硬技能, LLM/生成式AI应用, OTHER>",
      "member_indices": [<1-based indices of articles that fit, ≥2>],
      "evidence_one_line_zh": "<≤80字中文为啥归为这主题>",
      "evidence_one_line_en": "<≤30 word English>"
    }}
  ]
}}
Rules: cover ≥60% of articles; one article can fit only one theme; cluster size ≥2."""
    r, u = llm(prompt, "blog cluster JSON")
    print(f"  ✓ blog clusters: {len(r.get('themes',[]))} themes; usage={u.get('total_tokens')} t")
    return r

# ════════════ ③ 主题归一 (ALIAS map) ════════════
def build_alias_map():
    """读所有 signals 表里的 distinct theme，让 LLM 输出 canonical 归一映射。"""
    con = sqlite3.connect("data/signals.db")
    themes = [t for (t,) in con.execute("SELECT DISTINCT theme FROM signals").fetchall()]
    con.close()
    # 给 LLM 一份现有 canonical 列表作为锚（来自 W2-W3 我手工建的）
    KNOWN_CANONICAL = ["AI Agents/编排","Eval 评测","RAG","Serving 推理","多模态",
        "AI安全/Responsible AI","AI编码agent当硬技能","LLM/生成式AI应用",
        "MLOps/LLMOps","AI系统可观测性/成本","Python","SQL","Docker/Kubernetes",
        "TypeScript/Node","AWS/Azure 云","Prompt engineering","MCP 协议",
        "LLM架构(attention/MoE)","开放权重/微调(LoRA/DoRA)","与AI协作的工作方式","具身/机器人AI"]
    prompt = f"""Normalize these raw theme strings to canonical names. Group equivalents.

Known canonical names (PREFER these; use exactly these spellings if applicable):
{json.dumps(KNOWN_CANONICAL, ensure_ascii=False)}

Raw themes to map:
{json.dumps(themes, ensure_ascii=False)}

Output strict JSON:
{{
  "mapping": {{ "<raw theme>": "<canonical name>" }},
  "new_canonicals": [<list of canonicals you proposed that weren't in the known list>],
  "notes": "<brief reasoning if you needed new canonicals>"
}}
Rule: NEVER invent canonical names for trivial spelling variants. Map "Eval/评测" → "Eval 评测" not new."""
    r, u = llm(prompt, "alias map JSON")
    m = r.get("mapping", {})
    print(f"  ✓ alias map: {len(m)} raw → canonical; new canonicals: {r.get('new_canonicals',[])}; tokens={u.get('total_tokens')}")
    return r

# ════════════ 写库 ════════════
def write_signals_db(ent, blog, alias):
    con = sqlite3.connect("data/signals.db")
    RUN = datetime.datetime.now().isoformat(timespec="seconds")

    # 替换 enterprise 信号
    con.execute("DELETE FROM signals WHERE source_type='enterprise'")
    for tk, r in ent.items():
        if "error" in r: continue
        nm = r.get("name", tk)
        theme = r.get("canonical_theme", "Enterprise AI Platform")
        raw_zh = r.get("ai_strategy_one_line_zh","")
        sid = hashlib.md5(f"{theme}|enterprise|{tk}".encode()).hexdigest()[:16]
        con.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?,?,?)",
                    (sid, theme, f"{nm}: {raw_zh}", "enterprise", f"{tk} 10-K", "", "", "", RUN))

    # 替换 blog 信号
    con.execute("DELETE FROM signals WHERE source_type='blog'")
    for th in blog.get("themes", []):
        canon = th.get("canonical_signal", "OTHER")
        if canon == "OTHER": continue
        sid = hashlib.md5(f"{canon}|blog|{th.get('name_zh','')}".encode()).hexdigest()[:16]
        con.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?,?,?)",
                    (sid, canon, f"{th.get('name_zh','')}: {th.get('evidence_one_line_zh','')}",
                     "blog", f"博客圈聚类({len(th.get('member_indices',[]))} 篇)", "", "", "", RUN))

    # alias_map 表
    con.execute("CREATE TABLE IF NOT EXISTS alias_map(raw TEXT PRIMARY KEY, canonical TEXT, run_ts TEXT)")
    for raw, canon in (alias.get("mapping") or {}).items():
        if raw == canon: continue  # 自映射没意义
        con.execute("INSERT OR REPLACE INTO alias_map VALUES(?,?,?)", (raw, canon, RUN))

    # 留痕
    con.execute("INSERT INTO snapshots(run_ts,kind,payload_json) VALUES(?,?,?)",
                (RUN, "llm-extract", json.dumps({"ent_count":len([1 for r in ent.values() if "error" not in r]),
                                                  "blog_themes":len(blog.get("themes",[])),
                                                  "alias_count":len(alias.get("mapping",{}))}, ensure_ascii=False)))
    con.commit(); con.close()

# ════════════ main ════════════
print("═══ ① ENT (4 家 10-K AI 战略 LLM 抽取) ═══")
ent = extract_enterprise()
print()
print("═══ ② BLOG (42 篇近 90 天聚类) ═══")
blog = cluster_blogs()
print()
print("═══ ③ ALIAS map (主题归一 LLM 化) ═══")
alias = build_alias_map()
print()

# 把全部产物落到 data/llm_extracted.json（审计 trail）
out = {"as_of": datetime.date.today().isoformat(), "model": MODEL, "enterprise": ent, "blog": blog, "alias": alias}
json.dump(out, open("data/llm_extracted.json","w"), ensure_ascii=False, indent=1)
print(f"✓ data/llm_extracted.json written ({os.path.getsize('data/llm_extracted.json')} bytes)")

if DRY:
    print("--dry-run: 不写 signals.db")
else:
    write_signals_db(ent, blog, alias)
    print("✓ signals.db 已更新 (enterprise/blog signals 替换 + alias_map 表写入)")
