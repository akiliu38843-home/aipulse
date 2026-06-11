"""W2 — LLM(我)从 edgar/blog 抽取的主题写入 signals 表，并跑交叉印证 v0。
canonical theme 用统一键，使 jobs/oss/enterprise/blog 四源能对齐计数。"""
import sqlite3, json, datetime, hashlib

con = sqlite3.connect("data/signals.db")
RUN = datetime.datetime.now().isoformat(timespec="seconds")
def put(theme, raw, st, sn):
    sid = hashlib.md5(f"{theme}|{st}|{sn}|{raw[:60]}".encode()).hexdigest()[:16]
    con.execute("INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?,?,?)",
                (sid, theme, raw[:400], st, sn, "", "", "", RUN))

# --- 企业战略主题（LLM 读 4 家 10-K 抽取）---
ENT = [
 ("AI Agents/编排","PLTR: AIP 把平台+生成式LLM带到每个决策; MSFT: AI跨全栈","PLTR/MSFT 10-K"),
 ("Serving 推理","NVDA: data-center-scale AI 基础设施/加速计算/Blackwell 互联","NVDA 10-K"),
 ("AI安全/Responsible AI","MSFT: 安全优先+负责任AI+AI驱动安全合规身份产品","MSFT 10-K"),
 ("多模态","META: Meta AI 助手+AI眼镜+排序推荐生成式广告","META 10-K"),
 ("企业数据上的应用LLM","PLTR Ontology: 数据→语境→AI 实时连接运营","PLTR 10-K"),
]
for t,r,s in ENT: put(t,r,"enterprise",s)

# --- 博客新兴主题（LLM 读 42 篇抽取，标注命中篇数强度）---
BLOG = [
 ("AI编码agent(Codex/Claude Code/Cursor)当技能","OpenAI Codex 企业化系列(Dell/Databricks/各团队怎么用Codex) + Raschka 'Components of a Coding Agent' + Willison LLM 半年回顾——博客最热主题","OpenAI/Raschka/Willison"),
 ("AI Agents/编排","HF Open Agent Leaderboard + Google ReasoningBank(agent从经验学习)","HF/Google Research"),
 ("Serving 推理","Berkeley 自适应并行推理 + HF 连续批处理异步 + vLLM V0→V1 + HF 'FM训练推理on AWS'","HF/Berkeley"),
 ("Eval 评测","HF Open Agent Leaderboard / benchmark / Google ReasoningBank 评测","HF/Google"),
 ("开放权重/微调(LoRA/DoRA)","HF Cosmos LoRA/DoRA + Granite embeddings + Raschka 开放权重架构","HuggingFace"),
 ("LLM架构(attention/MoE)","Raschka KV共享/注意力变体/MoE 系列(偏研究者)","Sebastian Raschka"),
 ("与AI协作的工作方式","Eugene Yan 'Work and Compound with AI' + Google 'future-ready skills'","Eugene Yan/Google"),
]
for t,r,s in BLOG: put(t,r,"blog",s)

# 留痕快照（edgar+blog 原始输入，可证伪回看）
snap = {"edgar": json.load(open("data/edgar_w2.json")),
        "blogs_status": json.load(open("data/blogs_w2.json"))["source_status"],
        "blogs_titles": [f"{i['source']}|{i['date']}|{i['title']}" for i in json.load(open("data/blogs_w2.json"))["items"]]}
con.execute("INSERT INTO snapshots(run_ts,kind,payload_json) VALUES(?,?,?)",
            (RUN,"w2-llm-extracted", json.dumps(snap, ensure_ascii=False)))
con.commit()

# --- 交叉印证 v0：按 theme 统计跨了几个 source_type ---
print("\n=== 交叉印证 v0（theme × 命中 source_type 数）===")
rows = con.execute("""
  SELECT theme, GROUP_CONCAT(DISTINCT source_type) st, COUNT(DISTINCT source_type) n
  FROM signals GROUP BY theme ORDER BY n DESC, theme""").fetchall()
for theme, st, n in rows:
    tag = "🟢🟢强确认" if n>=3 else ("🟢双源确认" if n==2 else "⚪单源·待验")
    print(f"  [{n}源] {tag:<10} {theme}  <= {st}")
con.close()
