"""W3 — canonical 主题本体（解决 W2 头号硬伤）
做两件 W2 没做的事：
 1) alias→canonical 归一（v0 字符串精确匹配太脆）
 2) 给每个 canonical 标 layer：baseline(基础技能,普遍要求,不是'弱信号')/ foresight(前瞻信号,才参与"该提前学什么"排序)
"""
import sqlite3, json, datetime

# alias(原始 theme 串) -> canonical
# 硬编码 ALIAS = fallback; LLM 生成的 alias_map (signals.db) 优先。
# 这条手工映射 W2 时建的；llm_extract.py 跑过后会写一份更全的进 signals.db.alias_map
HARDCODED_ALIAS = {
 "AI编码agent(Claude Code/Cursor)当必备技能":"AI编码agent当硬技能",
 "AI编码agent(Codex/Claude Code/Cursor)当技能":"AI编码agent当硬技能",
 "AI编码agent当硬技能":"AI编码agent当硬技能",
 "企业数据上的应用LLM":"AI Agents/编排",
 "AI Agents/编排":"AI Agents/编排",
 "Prompt injection/AI安全":"AI安全/Responsible AI",
 "AI安全/Responsible AI":"AI安全/Responsible AI",
 "Token/成本可观测":"AI系统可观测性/成本",
 "AI系统可观测性":"AI系统可观测性/成本",
 "AI系统可观测性/成本":"AI系统可观测性/成本",
 "LLM/生成式AI应用":"LLM/生成式AI应用",
}
# 优先从 signals.db.alias_map 读 LLM 生成的；缺则 fallback 硬编码
def _load_alias():
    try:
        c=sqlite3.connect("data/signals.db")
        rows=c.execute("SELECT raw,canonical FROM alias_map").fetchall()
        c.close()
        if rows:
            print(f"[ontology] using LLM-generated alias_map: {len(rows)} entries")
            return dict(rows)
    except Exception:
        pass
    print(f"[ontology] LLM alias_map empty/missing → fallback to hardcoded ({len(HARDCODED_ALIAS)} entries)")
    return HARDCODED_ALIAS
ALIAS = _load_alias()
# canonical -> layer
LAYER = {
 # 基础技能：普遍必备，只在 jobs 出现是"太基础没被前瞻源单列"，非弱信号
 "Python":"baseline","SQL":"baseline","TypeScript/Node":"baseline",
 "Docker/Kubernetes":"baseline","AWS/Azure 云":"baseline","Prompt engineering":"baseline",
 "LLM/生成式AI应用":"baseline",
 # 前瞻信号：参与"该提前学什么"排序
 "AI Agents/编排":"foresight","Eval 评测":"foresight","Serving 推理":"foresight",
 "AI编码agent当硬技能":"foresight","RAG":"foresight","多模态":"foresight",
 "AI安全/Responsible AI":"foresight","MLOps/LLMOps":"foresight",
 "AI系统可观测性/成本":"foresight","MCP 协议":"foresight",
 "LLM架构(attention/MoE)":"research","开放权重/微调(LoRA/DoRA)":"foresight",
 "与AI协作的工作方式":"meta","具身/机器人AI":"foresight",
}
def canon(t): return ALIAS.get(t, t)

con = sqlite3.connect("data/signals.db")
agg = {}
for theme, st, raw in con.execute("SELECT theme,source_type,raw FROM signals").fetchall():
    c = canon(theme)
    d = agg.setdefault(c, {"srcs": set(), "ev": []})
    d["srcs"].add(st); d["ev"].append(f"{st}:{raw[:60]}")

rows = []
for c, d in agg.items():
    rows.append((c, LAYER.get(c, "foresight"), len(d["srcs"]), sorted(d["srcs"])))
rows.sort(key=lambda r: ({"foresight":0,"research":1,"meta":2,"baseline":3}[r[1]], -r[2], r[0]))

# 存本体表 + 快照
con.execute("CREATE TABLE IF NOT EXISTS ontology(canonical TEXT PRIMARY KEY, layer TEXT, n_src INT, srcs TEXT)")
con.execute("DELETE FROM ontology")
for c, lay, n, srcs in rows:
    con.execute("INSERT OR REPLACE INTO ontology VALUES(?,?,?,?)", (c, lay, n, ",".join(srcs)))
RUN = datetime.datetime.now().isoformat(timespec="seconds")
con.execute("INSERT INTO snapshots(run_ts,kind,payload_json) VALUES(?,?,?)",
            (RUN, "w3-ontology", json.dumps({c:{"layer":l,"n":n,"srcs":s} for c,l,n,s in rows}, ensure_ascii=False)))
con.commit(); con.close()

print("=== 前瞻信号（按命中源数排序，≥2 源=可信进 F-3）===")
for c, lay, n, srcs in rows:
    if lay in ("foresight","research","meta"):
        tag = "🟢🟢强(≥3源)" if n>=3 else ("🟢双源" if n==2 else "⚪单源待验")
        print(f"  [{n}源]{tag:<11} {c:<26} {lay:<9} <= {','.join(srcs)}")
print("\n=== 基础技能（普遍必备，不参与'新该学什么'排序，单源 jobs 是正常的）===")
print("  " + " / ".join(c for c,l,n,s in rows if l=="baseline"))
