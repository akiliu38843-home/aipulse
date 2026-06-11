"""W2 交叉印证 v1 — 加主题别名归一（LLM 层职责），再按 canonical theme 跨源计数"""
import sqlite3
con = sqlite3.connect("data/signals.db")

# 别名 → canonical（LLM 归一；v0 暴露的真问题：exact-match 太脆）
ALIAS = {
 "AI编码agent(Claude Code/Cursor)当必备技能":"AI编码agent当硬技能",
 "AI编码agent(Codex/Claude Code/Cursor)当技能":"AI编码agent当硬技能",
 "Prompt injection/AI安全":"AI安全/Responsible AI",
 "Token/成本可观测":"AI系统可观测性/成本",
 "AI系统可观测性":"AI系统可观测性/成本",
 "企业数据上的应用LLM":"AI Agents/编排",
 "LLM/生成式AI应用":"LLM/生成式AI应用",
}
def canon(t): return ALIAS.get(t, t)

agg={}
for theme, st in con.execute("SELECT theme, source_type FROM signals").fetchall():
    c=canon(theme); agg.setdefault(c,set()).add(st)
con.close()

rows=sorted(agg.items(), key=lambda kv:(-len(kv[1]), kv[0]))
print("=== 交叉印证 v1（别名归一后，theme × 源类型数）===\n")
for theme, sts in rows:
    n=len(sts)
    tag = "🟢🟢强确认(≥3源)" if n>=3 else ("🟢双源确认" if n==2 else "⚪单源·待验")
    print(f"[{n}源] {tag:<14} {theme:<28} <= {','.join(sorted(sts))}")
