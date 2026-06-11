"""W2 数据层 — SQLite signals 表 + append-only 留痕快照层（可证伪命门）
本脚本只装"确定性"信号：OSS 动量(来自 foresight_oss.json) + W1 招聘技能(W1 已人工抽取定稿)。
企业(edgar)/博客(blog) 信号由 add_llm_signals.py 在 LLM 抽取后写入。"""
import sqlite3, json, datetime, hashlib, os

DB = "data/signals.db"
con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE IF NOT EXISTS signals(
  id TEXT PRIMARY KEY, theme TEXT, raw TEXT, source_type TEXT,
  source_name TEXT, momentum TEXT, ts TEXT, link TEXT, run_ts TEXT);
CREATE TABLE IF NOT EXISTS snapshots(
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_ts TEXT, kind TEXT, payload_json TEXT);
""")
RUN = datetime.datetime.now().isoformat(timespec="seconds")

def put(theme, raw, st, sn, momentum="", ts="", link=""):
    sid = hashlib.md5(f"{theme}|{st}|{sn}|{raw[:60]}".encode()).hexdigest()[:16]
    con.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?,?,?)",
                (sid, theme, raw[:400], st, sn, momentum, ts, link, RUN))

# --- 前瞻·开源动量（来自 W1 拉的 foresight_oss.json，commit 活跃度代理）---
oss = json.load(open("data/foresight_oss.json"))
DIRMAP = {"langchain-ai/langgraph":"AI Agents/编排","run-llama/llama_index":"RAG",
 "modelcontextprotocol/servers":"MCP 协议","haotian-liu/LLaVA":"多模态",
 "confident-ai/deepeval":"Eval 评测","vllm-project/vllm":"Serving 推理"}
for r in oss:
    fn=r.get("full_name");
    if not fn or "error" in r: continue
    c4=r.get("commits_4w",0) or 0
    mom = "🔥猛" if c4>=200 else ("🟢活跃" if c4>=30 else ("🔴停滞" if c4==0 else "🟡平"))
    put(DIRMAP.get(fn,fn), f"{fn} ★{r.get('stars')} commit4w={c4}", "oss", fn, mom,
        str(r.get("pushed_at",""))[:10], r.get("url",""))

# --- 现状·招聘技能（W1 已人工(LLM)抽取定稿，剔除38%噪声后）---
W1_SKILLS = [
 ("Python","第一梯队·几乎必备"),("AWS/Azure 云","第一梯队"),("LLM/生成式AI应用","第一梯队"),
 ("Docker/Kubernetes","第一梯队"),("TypeScript/Node","第一梯队"),("SQL","第一梯队"),
 ("AI Agents/编排","第二梯队·在涨"),("Prompt engineering","第二梯队"),
 ("Eval 评测","第二梯队·高级岗标志"),("RAG","第二梯队"),
 ("AI系统可观测性","第二梯队"),("MLOps/LLMOps","第二梯队"),
 ("AI编码agent(Claude Code/Cursor)当必备技能","第三梯队·新兴"),
 ("Token/成本可观测","第三梯队·新兴"),("Prompt injection/AI安全","第三梯队·新兴"),
]
for sk,tier in W1_SKILLS:
    put(sk, f"W1 JD 抽取: {tier}", "jobs", "JobSpy(63岗/29JD)", tier)

# --- append-only 留痕快照（可证伪：日后回看"当时输入长啥样"）---
snap = {"oss": oss,
        "jobs_meta": json.load(open("data/jobs_w1.json")).get("site_breakdown") if os.path.exists("data/jobs_w1.json") else {},
        "w1_skills": W1_SKILLS}
con.execute("INSERT INTO snapshots(run_ts,kind,payload_json) VALUES(?,?,?)",
            (RUN,"w2-deterministic", json.dumps(snap, ensure_ascii=False)))
con.commit()
n=con.execute("SELECT count(*),source_type FROM signals GROUP BY source_type").fetchall()
ns=con.execute("SELECT count(*) FROM snapshots").fetchone()[0]
print("signals by type:", n, "| snapshots:", ns, "| db:", os.path.getsize(DB), "bytes")
con.close()
