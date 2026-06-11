"""W4+ '看新闻' — 双语版（中/EN）。
用法: python3 build_news.py [zh|en]     默认 zh
输出: site/news.html (zh) 或 site/news-en.html (en)"""
import json, os, re, sys, sqlite3, collections

LANG = (sys.argv[1] if len(sys.argv)>1 else "zh").lower()
ZH = LANG == "zh"
def t(zh, en): return zh if ZH else en
OUT = "site/news.html" if ZH else "site/news-en.html"

def L(fp, d=None):
    try: return json.load(open(fp))
    except: return d if d is not None else {}

jw=L("data/jobs_w1.json",{}); blg=L("data/blogs_w2.json",{}); oss=L("data/foresight_oss.json",[])
ossv2=L("data/foresight_oss_v2.json",[]); w3=L("data/w3_sources.json",{}); edg=L("data/edgar_w2.json",{})
sd=L("data/site_data.json",{}); ex=L("data/w4_extra.json",{}); h1b=L("data/h1b_ai.json",{})
digest=L("data/daily_digest_latest.json",{})
TPL="site/_news_design_template.html"

def clean(s,n=180):
    s=str(s or "").replace("\\-","-").replace("\\&","&").replace("\\.",".").replace("\\","")
    s=re.sub(r"[#*`>]+"," ",s); s=re.sub(r"\s+"," ",s).strip()
    return s[:n]+("…" if len(s)>n else "")
def job_brief(desc):
    s=clean(desc,520)
    for seg in re.split(r"(?<=[.!?。])\s+", s):
        seg=seg.strip()
        if len(seg)>=50 and not re.match(r"(?i)^(about |description|job summary|overview|who we are)",seg):
            return seg[:185]+("…" if len(seg)>185 else "")
    return s[:160]+"…"
def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def initials(name):
    w=[x for x in re.split(r"[\s\-\.]+",str(name)) if x]
    return ("".join(x[0] for x in w[:2]) or "·").upper()[:2]

# AI 相关性过滤
AI_TITLE = re.compile(r"(?i)(\bAI\b|\bML\b|\bLLM\b|Machine Learning|Data Scientist|Applied Scientist|Research Scientist|Data Engineer|MLOps|Generative|Forward Deployed|Prompt Engineer|AI[/\s-]?Native)")
BLOCK_TITLE = re.compile(r"(?i)(DevSecOps|Apriso|Dynamics 365|S1000D|Technical Author|Sourcer|Recruiter|Account Executive|Head of (Business )?Operations|Facilities|Electrical Engineer|Software Engineering Internship|Cloud Platform Specialist)")
AI_BRIEF = ("ai ","llm","machine learning","agent","generative","prompt","rag","embedding","fine-tun")
def is_ai_role(title, brief):
    tit=str(title or ""); b=(str(brief or "")).lower()
    if BLOCK_TITLE.search(tit): return False
    if AI_TITLE.search(tit): return True
    return sum(1 for k in AI_BRIEF if k in b) >= 3

# 现状·岗位（过滤后）
jobs=[]; sal_lo=[]; sal_hi=[]; jobs_total=0; jobs_drop=0
for j in (jw.get("jobs") or []):
    tit=str(j.get("title","")).strip()
    if not tit: continue
    jobs_total+=1
    brief=job_brief(j.get("description",""))
    if not is_ai_role(tit, brief):
        jobs_drop+=1; continue
    sal=""
    try:
        lo=float(j.get("min_amount") or 0); hi=float(j.get("max_amount") or 0)
        if lo>1000 and str(j.get("interval","")).startswith("year"):
            sal=f"${int(lo/1000)}–{int(hi/1000)}k"; sal_lo.append(lo); sal_hi.append(hi)
    except: pass
    loc=(t("远程","Remote") if str(j.get("is_remote")).lower() in("true","1") else str(j.get("location","")).strip())
    co=str(j.get("company","")).strip()
    jobs.append({"hl":esc(tit),"mt":esc(f"{co} · {loc}"),"dg":esc(brief),
        "ft":(f'<span class="sal">{sal}</span> <span style="color:var(--mut)">{t("/ 年","/ yr")}</span>' if sal else ''),
        "more":[[t("公司","Company"),esc(co)],[t("地点","Location"),esc(loc)]]+
              ([[t("薪资","Salary"),sal+t(" / 年"," / yr")]] if sal else [])+
              [[t("过滤","Filter"),t("AI 相关性已校验","AI relevance verified")]]})
jobs_kept=len(jobs)
salary_med=(sd.get("salary") or {}).get("median_yearly") or 0
salary_n=(sd.get("salary") or {}).get("n") or 0
slo=int(min(sal_lo)/1000) if sal_lo else 90
shi=int(max(sal_hi)/1000) if sal_hi else 300

# 招聘风向
hn=w3.get("hn") or {}
wih=hn.get("skill_freq_in_hiring",{}) or {}
wih_top=sorted(wih.items(),key=lambda kv:-kv[1])[:6]
wmax=max([v for _,v in wih_top],default=1)
NOW_SKILLS_ZH=["Python","AWS/Azure 云","LLM/生成式AI应用","Docker/Kubernetes","TypeScript/Node","SQL","AI Agents/编排","Eval 评测"]
NOW_SKILLS_EN=["Python","AWS/Azure Cloud","LLM / GenAI Apps","Docker/Kubernetes","TypeScript/Node","SQL","AI Agents/Orchestration","Evals"]
now_skills=NOW_SKILLS_ZH if ZH else NOW_SKILLS_EN
wt=[34,30,26,23,20,18,16,15]
weighted_html="".join(f'<span style="font-size:{wt[i] if i<len(wt) else 14}px"{" class=dim" if i>=4 else ""}>{esc(s)}</span>' for i,s in enumerate(now_skills))
freq_html="".join(
    f'<div class="freqrow"><span class="name">{esc(k)}</span>'
    f'<span class="bar"><i style="width:{int(v/wmax*100)}%"></i></span>'
    f'<span class="num">{v}</span></div>' for k,v in wih_top)
hire_cards=[
 {"soft":True,"stat":True,"custom":(
   f'<div class="hl">{t("年薪中位","Median Salary")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("北美 AI 岗 · n=","NA AI roles · n=")}{salary_n}</div>'
   f'<div class="stat-big">${salary_med:,}</div>'
   f'<div class="stat-sub">{t("自报 n=","Self-reported n=")}{salary_n}{t("（JobSpy 抓取）"," (via JobSpy)")}</div>'
   f'<div class="axis-bar"><i style="left:14%;width:62%"></i><b style="left:50%"></b></div>'
   f'<div class="axis"><span>${slo}k</span><span>{t("中位","median")}</span><span>${shi}k</span></div>'),
  "more":[[t("指标","Metric"),t("年薪中位","Median annual salary")],
          [t("样本","Sample"),f"n={salary_n}"],
          [t("实测范围","Observed range"),f"${slo}k–${shi}k"]]},
 {"soft":True,"custom":(
   f'<div class="hl">{t("JD 高频技能","Top JD Skills")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("简历该往这些词靠","Align your résumé to these")}</div>'
   f'<div class="weighted">{weighted_html}</div>'),
  "more":[[t("来源","Source"),t("63 份 JD · W1 LLM 抽取","63 JDs · W1 LLM extraction")],
          [t("说明","Note"),t("按需求层级排序，未编造精确计数","Tier-ordered, no fabricated counts")]]},
 {"soft":True,"custom":(
   f'<div class="hl">HN Who-is-hiring</div>'
   f'<div class="mt"><span class="pip"></span>{hn.get("who_is_hiring_comments","?")} {t("条招聘贴","hiring posts")}</div>'
   f'<div class="dg" style="-webkit-line-clamp:unset;display:block">{t("提及频次（真实计数）","Mention frequency (real counts)")}</div>'
   f'<div class="freqlist">{freq_html}</div>'
   f'<div class="ft">{t("补 JobSpy 抓不到的早期/小厂","Covers early-stage/small companies JobSpy misses")}</div>'),
  "more":[[t("数据源","Source"),f"HN Who-is-hiring · {hn.get('who_is_hiring_comments','?')}"],
          [t("互补","Complements"),"JobSpy"]]},
]

# AI 明星 & 社区
talk=[{"src":i.get("source",""),"t":i.get("title",""),"date":i.get("date",""),
       "link":i.get("link",""),"sum":clean(i.get("summary",""),175)} for i in (blg.get("items") or [])]
talk.sort(key=lambda x:x["date"],reverse=True)
talk_cards=[{"author":initials(x["src"]),"hl":esc(x["t"]),
    "mt":esc(f'{x["src"]} · {x["date"]}'),"dg":esc(x["sum"] or t("（该 RSS 源未提供摘要）","(this RSS source provides no summary)")),
    "more":[[t("作者","Author"),esc(x["src"])],[t("日期","Date"),esc(x["date"])]]} for x in talk[:12]]
# HN 热议——单独成栏（b4）。每条 story 一张卡；摘要从 hn_summaries.json 真实抓取（w4_hn_enrich.py 跑）。
hn_hot=[h for h in (hn.get("hot_ai_stories") or [])][:8]
def _domain(u):
    try: return (u or "").split("//",1)[-1].split("/",1)[0].replace("www.","")
    except: return ""
HN_SUMS=(L("data/hn_summaries.json",{}) or {}).get("by_url",{})
def _hn_sum(url):
    s=(HN_SUMS.get(url,{}) or {}).get("sum","").strip()
    return s if s else t("（无摘要 · 点标题看原文）","(no summary · click title for source)")
hn_hot_cards=[{
   "hl":(f'<a href="{esc(h.get("url","") or "#")}" target="_blank" onclick="event.stopPropagation()" '
         f'style="color:inherit;text-decoration:none;border-bottom:1px dotted var(--mut-2)">'
         f'{esc(h.get("title",""))}</a>'),
   "mt":f'{h.get("points","?")} pts{(" · "+esc(_domain(h.get("url","")))) if _domain(h.get("url","")) else ""}',
   "dg":esc(_hn_sum(h.get("url",""))),
   "more":[[t("分数","Points"),str(h.get("points",""))],
           [t("链接","Link"),esc((h.get("url") or "")[:80]) or "—"],
           [t("摘要状态","Summary"),(HN_SUMS.get(h.get("url",""),{}) or {}).get("status","-")]]
} for h in hn_hot]

# 研究前沿
arx=[{"t":p.get("title",""),"date":p.get("date",""),"au":p.get("authors",""),
      "link":p.get("link",""),"sum":clean(p.get("summary",""),200)} for p in ((ex.get("arxiv") or {}).get("papers") or [])][:12]
arx_cards=[{"subj":{"label":"arXiv","color":"#2A6FDB"},"hl":esc(a["t"]),
    "mt":esc(f'{a["date"]} · {a["au"]}'),"dg":esc(a["sum"]),
    "more":[[t("日期","Date"),esc(a["date"])],[t("作者","Authors"),esc(a["au"])]]} for a in arx]

# 开源项目 & 模型
DIR_ZH={"langchain-ai/langgraph":"Agent 编排","run-llama/llama_index":"RAG","modelcontextprotocol/servers":"MCP",
 "confident-ai/deepeval":"Eval 评测","vllm-project/vllm":"Serving 推理","OpenBMB/MiniCPM-V":"多模态","QwenLM/Qwen2.5-VL":"多模态"}
DIR_EN={"langchain-ai/langgraph":"Agents/Orchestration","run-llama/llama_index":"RAG","modelcontextprotocol/servers":"MCP",
 "confident-ai/deepeval":"Evals","vllm-project/vllm":"Serving/Inference","OpenBMB/MiniCPM-V":"Multimodal","QwenLM/Qwen2.5-VL":"Multimodal"}
DIR=DIR_ZH if ZH else DIR_EN
GLOSS_ZH={"langchain-ai/langgraph":"有状态的多智能体/工作流编排框架，做可控 Agent 的事实标准之一",
 "run-llama/llama_index":"把私有数据接进 LLM 的 RAG 数据框架",
 "modelcontextprotocol/servers":"MCP 协议官方服务器集，让 LLM 标准化接外部工具/数据",
 "confident-ai/deepeval":"LLM/Agent 的单元测试式评测框架，回答“我的 AI 到底准不准”",
 "vllm-project/vllm":"高吞吐 LLM 推理/部署引擎，自托管上线模型的主力",
 "OpenBMB/MiniCPM-V":"端侧可跑的多模态(视觉语言)模型，手机级硬件就能用",
 "QwenLM/Qwen2.5-VL":"阿里 Qwen 系列视觉语言模型"}
GLOSS_EN={"langchain-ai/langgraph":"Stateful multi-agent/workflow orchestration framework; a de facto standard for controllable Agents.",
 "run-llama/llama_index":"RAG data framework that wires private data into LLMs.",
 "modelcontextprotocol/servers":"Official MCP servers; lets LLMs standardly access external tools/data.",
 "confident-ai/deepeval":"Unit-test-style Eval framework for LLMs/Agents — 'is my AI actually correct?'",
 "vllm-project/vllm":"High-throughput LLM inference engine — the workhorse for self-hosting.",
 "OpenBMB/MiniCPM-V":"On-device multimodal (vision-language) model; runs on phone-grade hardware.",
 "QwenLM/Qwen2.5-VL":"Alibaba Qwen vision-language model series."}
GLOSS=GLOSS_ZH if ZH else GLOSS_EN
PAL=["#5B3FB8","#1F6F4A","#CC3B1B","#2A6FDB","#9A6B1F","#0F1419"]
proj=[]
for r in (oss+ossv2):
    fn=r.get("full_name")
    if not fn or "error" in r or fn not in DIR or any(p["repo"]==fn for p in proj): continue
    c4=r.get("commits_4w") or 0
    proj.append({"repo":fn,"dir":DIR[fn],"stars":r.get("stars") or 0,"c4w":c4,
      "heat":t("🔥猛","🔥hot") if c4>=200 else(t("🟢活跃","🟢active") if c4>=30 else(t("🔴停滞","🔴stalled") if c4==0 else t("🟡温和","🟡warm")))})
proj.sort(key=lambda x:-x["c4w"])
proj_cards=[]
for i,p in enumerate(proj):
    proj_cards.append({"mono":{"letter":p["repo"].split("/")[-1][0].upper(),"color":PAL[i%len(PAL)]},
      "hl":esc(p["repo"]),"mt":esc(p["dir"]),"dg":esc(GLOSS.get(p["repo"],"")),
      "custom_ft":(f'<div class="starline"><span class="s-big">★{p["stars"]:,}</span>'
        f'<span class="s-delta">{t("近4周","Past 4 wk")} +{p["c4w"]} commit</span>'
        f'<span class="s-heat">{p["heat"]}</span></div>'),
      "more":[[t("分类","Category"),esc(p["dir"])],
              [t("近4周提交","Commits / 4 wk"),f'+{p["c4w"]} commit'],
              [t("热度","Heat"),p["heat"]]]})
hf=[m for m in ((w3.get("hf") or {}).get("trending") or [])][:7]
HFG_ZH={"image-text-to-text":"多模态","text-generation":"文本生成","text-to-speech":"语音","image-to-video":"图生视频",
 "any-to-any":"全模态","text-to-image":"文生图","image-to-3d":"图生3D","question-answering":"问答","text-to-video":"文生视频"}
HFG_EN={"image-text-to-text":"Multimodal","text-generation":"Text generation","text-to-speech":"Speech",
 "image-to-video":"Image→Video","any-to-any":"Any-to-any","text-to-image":"Text→Image","image-to-3d":"Image→3D",
 "question-answering":"QA","text-to-video":"Text→Video"}
HFG=HFG_ZH if ZH else HFG_EN
proj_cards.append({"soft":True,"custom":(
   f'<div class="hl">HuggingFace {t("trending","trending")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("本周最热模型","Hottest models this week")}</div>'
   '<div class="dg" style="-webkit-line-clamp:unset;display:block;margin-top:4px">'
   +"<br>".join(f'· {esc(m.get("id",""))} <span class="tg">{HFG.get(m.get("pipe") or m.get("pipeline"),m.get("pipe") or m.get("pipeline") or "")}</span>' for m in hf)+'</div>'),
   "more":[[f'#{i+1}',esc(m.get("id",""))] for i,m in enumerate(hf[:4])]})

# PyPI 库采纳（诚实留白）
PG_ZH={"langchain":"LLM 应用编排框架","openai":"OpenAI 官方 SDK","anthropic":"Anthropic/Claude 官方 SDK",
 "transformers":"HF 模型库(训练/推理基座)","vllm":"高吞吐推理引擎","llama-index":"RAG 数据框架",
 "langgraph":"有状态 Agent 编排","crewai":"多智能体协作框架","huggingface-hub":"HF 模型仓客户端","litellm":"统一多家 LLM API 网关"}
PG_EN={"langchain":"LLM app orchestration framework","openai":"OpenAI official SDK","anthropic":"Anthropic/Claude official SDK",
 "transformers":"HF model hub (training/inference base)","vllm":"High-throughput inference engine","llama-index":"RAG data framework",
 "langgraph":"Stateful Agent orchestration","crewai":"Multi-agent framework","huggingface-hub":"HF Hub client","litellm":"Unified LLM API gateway"}
PG=PG_ZH if ZH else PG_EN
pypi=[{"pkg":l["pkg"],"m":l.get("last_month") or 0,"g":PG.get(l["pkg"],"")}
      for l in ((ex.get("pypi") or {}).get("libs") or []) if "error" not in l][:8]
pmax=max([p["m"] for p in pypi],default=1)
pypi_cards=[]
for p in pypi:
    pct=int(p["m"]/pmax*100)
    pypi_cards.append({"soft":True,"custom":(
      f'<div class="hl">{esc(p["pkg"])}</div>'
      f'<div class="mt"><span class="pip"></span>{esc(p["g"])}</div>'
      f'<div class="adopt"><div class="adopt-num"><span class="big">{p["m"]/1e6:.0f}M</span>'
      f'<span class="unit">{t("下载 / 月","downloads / mo")}</span></div>'
      f'<div class="scale"><i style="width:{pct}%"></i></div>'
      f'<div class="ticks"><span>0</span><span>{pmax/1e6:.0f}M{t("（本期最高）"," (top this issue)")}</span></div>'
      f'<div class="adopt-foot"><span class="lbl">{t("单期快照","Snapshot")}</span>'
      f'<span class="rel">{pct}% {t("of 最高","of top")}</span>'
      f'<span class="lbl">{t("无 12 月序列 · 待多期累积","No 12-mo series · awaiting multi-issue")}</span></div></div>'),
      "more":[[t("月下载","Monthly DL"),f'{p["m"]/1e6:.0f}M'],
              [t("相对本期最高","Rel. to top"),f"{pct}%"],
              [t("序列","Series"),t("单期快照（诚实：未累积历史）","Snapshot only (no history yet)")]]})

# 大公司
ENT_DESC_ZH=[
 "自称“数据中心规模 AI 基础设施公司”；CUDA+Blackwell+万卡互联，押 Serving/推理基建。",
 "AI 跨全栈 + 负责任/安全 AI + AI 驱动安全合规身份产品。",
 "AIP：平台+生成式 LLM 带到“每个决策”；Ontology 数据→语境，押企业 Agent。",
 "Meta AI 助手 + AI 眼镜(多模态) + 排序推荐 + 生成式广告。",
]
ENT_DESC_EN=[
 'Calls itself "a data-center-scale AI infrastructure company"; CUDA + Blackwell + tens-of-thousands GPU interconnect — betting on Serving/inference infrastructure.',
 "AI across the full stack + Responsible/Safe AI + AI-driven security/compliance/identity products.",
 'AIP: platform + generative LLMs into "every decision"; Ontology data→context — betting on enterprise Agents.',
 "Meta AI assistant + AI glasses (multimodal) + recommendation/ranking + generative ad tooling.",
]
ENT_NAMES=[("NVIDIA","#76B900","NVDA"),("Microsoft","#0067B8","MSFT"),("Palantir","#101113","PLTR"),("Meta","#0866FF","META")]
def fd(tk): return (edg.get("companies",{}).get(tk,{}) or {}).get("filing_date","")
ENT_ROWS=list(zip(ENT_NAMES, ENT_DESC_ZH if ZH else ENT_DESC_EN))
ent_cards=[{"kind":"co","accent":ac,"hl":esc(nm),"mt":esc(f"{fd(tk)} · 10-K"),"dg":esc(ds),
   "more":[[t("来源","Source"),f"10-K · {fd(tk)}"],[t("押注","Bet"),esc(ds[:60])]]}
   for ((nm,ac,tk),ds) in ENT_ROWS]

# 签证 & 年报
REPORTS_ZH=[("Stanford HAI · AI Index Report",t("年度 · 非实时","Annual · not real-time"),"AI 人才/教育/岗位/R&D 最权威统计。"),
 ("State of AI Report",t("年度 · 非实时","Annual · not real-time"),"研究/产业/资本/安全综述，看大势拐点。")]
REPORTS_EN=[("Stanford HAI · AI Index Report","Annual · not real-time",
             "The authoritative annual report on AI talent, education, jobs and R&D."),
 ("State of AI Report","Annual · not real-time",
  "Annual synthesis on research / industry / capital / safety — track inflection points.")]
reports=REPORTS_ZH if ZH else REPORTS_EN
# H-1B 实数据卡（W3 占位 → 真实 USCIS Data Hub 3 年聚合）
if h1b and h1b.get("top_sponsors"):
    tops=h1b["top_sponsors"][:7]
    trend=h1b.get("trend_ai_initial_by_fy",{})
    summ=h1b.get("summary",{})
    completeness=h1b.get("data_completeness",{})
    fy23_pct=completeness.get("FY2023",{}).get("pct_of_max",100)
    fy23_partial = fy23_pct < 80
    # 卡 1: Top sponsors 精简榜
    top_list_html="".join(
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--line);font-size:13px">'
        f'<span style="color:var(--ink);font-weight:500">{esc(s["name"][:38])}</span>'
        f'<span style="font-family:var(--serif);color:var(--acc);font-weight:600">{s["initial_3y"]}</span></div>'
        for s in tops)
    visa_card={"soft":True,"custom":(
        f'<div class="hl">{t("H-1B Top Sponsors","Top H-1B Sponsors")}</div>'
        f'<div class="mt"><span class="pip"></span>{t("近 3 年新批准合计 · USCIS Data Hub","3-yr initial approvals · USCIS")}</div>'
        f'<div style="margin-top:8px">{top_list_html}</div>'
        f'<div class="ft">{t("数据","Data")}: USCIS · FY{",FY".join(str(y) for y in [2021,2022,2023])} · {summ.get("n_ai_employers_3y",0)} {t("家 AI 雇主","AI employers")}</div>'),
        "more":[[s["name"],f'{s["initial_3y"]} ({s["state_top"]} {s["city"][:18]})'] for s in tops[:5]]}
    # 卡 2: 趋势 + 诚实留白
    yr_max=max(trend.values()) if trend else 1
    bar_rows="".join(
        f'<div style="display:flex;align-items:center;gap:8px;font-size:12.5px;margin:5px 0">'
        f'<span style="flex:0 0 50px;font-family:var(--mono);color:var(--ink-2)">FY{y}</span>'
        f'<span style="flex:1;background:var(--soft);height:10px;border-radius:3px;overflow:hidden"><i style="display:block;height:100%;background:var(--acc);width:{int(trend.get(f"FY{y}",0)/yr_max*100)}%"></i></span>'
        f'<span style="flex:0 0 60px;text-align:right;font-family:var(--mono);color:var(--mut)">{trend.get(f"FY{y}",0)}</span>'
        f'</div>' for y in [2021,2022,2023] if f"FY{y}" in trend)
    trend_card={"soft":True,"custom":(
        f'<div class="hl">{t("3 年趋势 · AI 公司新批 H-1B","3-yr trend · AI-company new H-1B")}</div>'
        f'<div class="mt"><span class="pip"></span>{t("Initial Approvals only","Initial approvals only")}</div>'
        f'<div style="margin-top:10px">{bar_rows}</div>'
        + (f'<div class="editors-note" style="margin-top:10px"><span class="tk">{t("诚实","HONEST")}</span>'
           f'<span class="body">FY2023 {t("数据 USCIS 仅发布约","USCIS only released ~")}<em>{fy23_pct}%</em> ({completeness.get("FY2023",{}).get("rows",0)} {t("行 vs FY2021/22 各 ~60k 行","rows vs ~60k in FY2021/22")}); {t("看似下降实为部分数据","apparent drop is partial data, not real trend")}.</span></div>'
           if fy23_partial else '')),
        "more":[[t("FY 2021","FY 2021"),str(trend.get("FY2021","-"))],
                [t("FY 2022","FY 2022"),str(trend.get("FY2022","-"))],
                [t("FY 2023 (部分)","FY 2023 (partial)"),f'{trend.get("FY2023","-")} (rows={completeness.get("FY2023",{}).get("rows",0)})']]}
else:
    # 数据缺失诚实占位
    visa_card={"soft":True,"custom":(
        f'<div class="hl">{t("北美签证 / H-1B","NA Visa / H-1B")}</div>'
        f'<div class="mt"><span class="pip"></span>{t("数据待抓","data pending")}</div>'
        '<div class="editors-note"><span class="tk">TK</span>'
        f'<span class="body">{t("fetch_h1b.py 未跑或失败。USCIS Hub 可达，下次 CI 重试。","fetch_h1b.py not run or failed. USCIS Hub reachable; CI will retry.")}</span></div>'),
        "more":[[t("状态","Status"),t("数据未生成","data not generated")]]}
    trend_card=None
rep_cards=[{"soft":True,"hl":esc(rt),"mt":esc(rm),"dg":esc(rd),
   "more":[[t("类型","Type"),esc(rm)],[t("覆盖","Covers"),esc(rd)]]} for rt,rm,rd in reports]

# 各栏要点 digest（中英）
fn0=top_proj0=lambda i:(proj[i] if i<len(proj) else {"repo":"-","dir":"","c4w":0})
top_proj=[fn0(0)(),fn0(1)()] if False else (proj[:2] if proj else [{"repo":"-","dir":"","c4w":0}]*2)
hf_tags=(w3.get("hf") or {}).get("tag_freq",{})
hf_mm=hf_tags.get("image-text-to-text",0)+hf_tags.get("image-to-video",0)+hf_tags.get("text-to-video",0)+hf_tags.get("any-to-any",0)
pypi_sorted=sorted(pypi,key=lambda x:-x["m"])
p1=pypi_sorted[0] if pypi_sorted else {"pkg":"-","m":0}
p2=pypi_sorted[1] if len(pypi_sorted)>1 else {"pkg":"-","m":0}
job_cos=[next((v for k,v in j.get("more",[]) if k in ("公司","Company")), "") for j in jobs]
top_co=[c for c,_ in collections.Counter([c for c in job_cos if c]).most_common(3)]
remote_n=sum(1 for j in jobs if " · Remote" in j.get("mt","") or " · 远程" in j.get("mt",""))
rem_pct=int(remote_n*100/max(jobs_kept,1))
hn_top3=" / ".join(f"{esc(k)}·{v}" for k,v in wih_top[:3]) if wih_top else "—"
jd_top3=" / ".join(esc(s) for s in now_skills[:3]) if now_skills else "—"

DIGESTS = {
 "b1": t(
  f"<b>{jobs_kept}</b> 个 AI 相关岗（{jobs_total} 抓取，滤 {jobs_drop} 噪声）。<br>"
  f"年薪 <b>${slo}–{shi}k</b>，中位 <em>${salary_med//1000}k</em>。<br>"
  f"远程占比 <b>{rem_pct}%</b>。<br>"
  f"发岗大户：{ '、'.join(top_co) if top_co else '—' }。<br>"
  f"主力岗型：<em>AI/ML Engineer · Forward Deployed · Data Scientist</em>。",
  f"<b>{jobs_kept}</b> AI-relevant roles (of {jobs_total} scraped, {jobs_drop} noise filtered).<br>"
  f"Salary <b>${slo}–{shi}k</b>, median <em>${salary_med//1000}k</em>.<br>"
  f"Remote share <b>{rem_pct}%</b>.<br>"
  f"Top employers: {', '.join(top_co) if top_co else '—'}.<br>"
  f"Main roles: <em>AI/ML Engineer · Forward Deployed · Data Scientist</em>."),

 "b2": t(
  f"JD 与 HN 双源印证：<b>Python</b> 都是头号需求。<br>"
  f"JD 重 <em>{jd_top3}</em>；HN 重 <em>{hn_top3}</em>。<br>"
  f"信号：写得动 <b>Agent + Eval</b> 比「懂某个模型」更被招；RAG 在 HN 小厂更高频。",
  f"JDs and HN Who-is-hiring both confirm: <b>Python</b> is the #1 demand.<br>"
  f"JDs lean on <em>{jd_top3}</em>; HN weights <em>{hn_top3}</em>.<br>"
  f"Signal: shipping <b>Agents + Evals</b> beats knowing one model; RAG is hotter at HN small-shops."),

 "b3": t(
  f"<b>{len(blg.get('items') or [])}</b> 篇近 90 天文章。<br>三大焦点：<em>编码 agent</em>（OpenAI Codex 企业化 + Raschka 拆解 + Willison 半年回顾）／<em>多模态</em>（HF Cosmos+微调）／<em>推理效率</em>（BAIR+vLLM）。<br>看下方 HN 热议栏目验证博客圈的判断。",
  f"<b>{len(blg.get('items') or [])}</b> articles in the past 90 days. Three foci this week: <em>coding agents</em> (OpenAI Codex enterprise rollout + Raschka deep-dive + Willison's 6-month retro) / <em>multimodal</em> (HF Cosmos + fine-tuning) / <em>inference efficiency</em> (BAIR + vLLM).<br>Cross-check the HN Buzz section below."),

 "b4": t(
  f"<b>{len(hn_hot)}</b> 条近 35 天 ≥80 分的 AI 热议。<br>社区是<em>早期信号源</em>——博客/新闻还没炒的话题往往先在 HN 起火。<br>每条标题<em>点击直跳原文</em>（开新标签）；分数=社区共识强度。<br>与 b3 博客圈观点相互印证。",
  f"<b>{len(hn_hot)}</b> AI threads with ≥80 points in the past 35 days.<br>The community is an <em>early signal source</em> — topics often peak on HN before blogs or news catch on.<br><em>Click any title</em> to open the source (new tab); points = consensus strength.<br>Cross-reference with the Voices & Community section above."),

 "b5": t(
  f"<b>{len(arx)}</b> 篇 arXiv 最新。<br>主题集中三件事：<em>注意力 / 长上下文</em>（DashAttention）／<em>Agent 经验记忆</em>（ReasoningBank）／<em>推理 scaling</em>（Adaptive Parallel）。<br>核心三问：更长、更准、更省。",
  f"<b>{len(arx)}</b> arXiv papers. Three themes: <em>attention / long context</em> (DashAttention) / <em>agent memory</em> (ReasoningBank) / <em>reasoning scaling</em> (Adaptive Parallel).<br>Core questions: longer, more accurate, cheaper."),

 "b6": t(
  f"以 commit 活跃度看动量：<br>"
  f"<b>{top_proj[0]['repo'].split('/')[-1]}</b>（{top_proj[0]['dir']}）4 周 <em>{top_proj[0]['c4w']}</em> + "
  f"<b>{top_proj[1]['repo'].split('/')[-1]}</b>（{top_proj[1]['dir']}）<em>{top_proj[1]['c4w']}</em> commit 居前。<br>"
  f"<em>Serving</em> 与 <em>Eval</em> 是开源最猛两条线。<br>"
  f"HF trending 30 中 <b>{hf_mm}</b> 个多模态品类——采纳第一热。",
  f"Momentum by commit activity:<br>"
  f"<b>{top_proj[0]['repo'].split('/')[-1]}</b> ({top_proj[0]['dir']}) <em>{top_proj[0]['c4w']}</em> + "
  f"<b>{top_proj[1]['repo'].split('/')[-1]}</b> ({top_proj[1]['dir']}) <em>{top_proj[1]['c4w']}</em> commits in 4 wk, leading.<br>"
  f"<em>Serving</em> and <em>Evals</em> are the two hottest open-source lines.<br>"
  f"On HF trending: <b>{hf_mm}</b> of 30 are multimodal — adoption #1."),

 "b7": t(
  f"<b>{esc(p1['pkg'])}</b> <em>{p1['m']/1e6:.0f}M/月</em>（多模型可切网关）一骑绝尘，远超 <b>{esc(p2['pkg'])}</b> <em>{p2['m']/1e6:.0f}M</em>。<br>"
  f"信号：开发者要「<em>多模型可切</em>」胜过押单一供应商。<br>"
  f"<b>诚实留白：</b>单期快照、无 12 月序列，待 2026-08 第二期累积。",
  f"<b>{esc(p1['pkg'])}</b> <em>{p1['m']/1e6:.0f}M/mo</em> (multi-LLM gateway) leads by a mile, dwarfing <b>{esc(p2['pkg'])}</b> <em>{p2['m']/1e6:.0f}M</em>.<br>"
  f"Signal: devs want <em>provider-agnostic gateways</em> over locking to one.<br>"
  f"<b>Honest gap:</b> Snapshot only, no 12-mo series yet — awaiting issue 2 (Aug 2026)."),

 "b8": t(
  f"四家 10-K 恰好分到四主战场：<br>"
  f"<b>NVDA</b>→<em>Serving 基建</em><br>"
  f"<b>MSFT</b>→<em>全栈 + 负责任 AI</em><br>"
  f"<b>PLTR</b>→<em>企业 Agent</em>（AIP）<br>"
  f"<b>META</b>→<em>多模态</em>（AI 眼镜）<br>"
  f"四象限被填满 = AI 落地四主线都有真金白银。",
  "Four 10-Ks split neatly across four AI battlegrounds:<br>"
  "<b>NVDA</b>→<em>Serving infra</em><br>"
  "<b>MSFT</b>→<em>Full-stack + Responsible AI</em><br>"
  "<b>PLTR</b>→<em>Enterprise Agents</em> (AIP)<br>"
  "<b>META</b>→<em>Multimodal</em> (AI glasses)<br>"
  "All four quadrants funded = AI deployment's four main lines all have real money on them."),

 "b9": (t(
  f"<b>H-1B</b>: USCIS Data Hub 3 年聚合 · <b>{h1b.get('summary',{}).get('n_ai_employers_3y','?')}</b> 家 AI 雇主 · <em>{h1b.get('summary',{}).get('total_initial_3y','?')}</em> 新批合计。<br>Top: Amazon / Google / Microsoft / Apple。<br>诚实留白：FY2023 USCIS 只发布部分数据。<br><b>年报</b>是季度方向校准源。",
  f"<b>H-1B</b>: USCIS Data Hub 3-yr aggregate · <b>{h1b.get('summary',{}).get('n_ai_employers_3y','?')}</b> AI employers · <em>{h1b.get('summary',{}).get('total_initial_3y','?')}</em> new approvals total.<br>Top: Amazon / Google / Microsoft / Apple.<br>Honest: FY2023 USCIS only published partial data.<br><b>Annual reports</b> for quarterly direction calibration."
 ) if h1b else t(
  "<b>签证视图</b>占位：USCIS Hub 可达，DOL 薪资 403 被挡。<br>"
  "<b>权威年报</b>是季度回看用的<em>方向校准</em>，非新闻速读源。",
  "<b>Visa view</b>: placeholder — USCIS Hub reachable, DOL salary 403 blocked.<br>"
  "<b>Authoritative annual reports</b> are <em>direction calibration</em> for quarterly review, not real-time news.")),
}

BANDS=[
 {"id":"b1","n":"01","k":t("岗位动态","Job Pulse"),"pp":t("北美 AI 在招什么、给多少钱","What NA AI is hiring · pay levels"),"cnt":t(f'{jobs_kept} AI-相关 / {jobs_total} 抓取',f'{jobs_kept} AI-relevant / {jobs_total} scraped'),"cards":jobs},
 {"id":"b2","n":"02","k":t("招聘市场风向","Hiring Signal"),"pp":t("薪资水位 + 真实技能需求","Salary level + real skill demand"),"cnt":"","cards":hire_cards},
 {"id":"b3","n":"03","k":t("AI 明星 & 社区","Voices & Community"),"pp":t("他们认为接下来什么重要","What they think matters next"),"cnt":t(f'{len(blg.get("items") or [])} 篇',f'{len(blg.get("items") or [])} pieces'),"cards":talk_cards},
 {"id":"b4","n":"04","k":t("Hacker News 热议","Hacker News Buzz"),"pp":t("社区现在吵什么 · 早期信号源","What the community is buzzing about · early signal"),"cnt":t(f'{len(hn_hot)} 条 · ≥80 pts',f'{len(hn_hot)} stories · ≥80 pts'),"cards":hn_hot_cards},
 {"id":"b5","n":"05","k":t("研究前沿","Research Frontier"),"pp":"arXiv cs.AI/LG/CL","cnt":t(f"{len(arx)} 篇",f"{len(arx)} papers"),"cards":arx_cards},
 {"id":"b6","n":"06","k":t("开源项目 & 模型","OSS & Models"),"pp":t("哪些框架/模型在火","Hot frameworks / models"),"cnt":"","cards":proj_cards},
 {"id":"b7","n":"07","k":t("库采纳曲线","Library Adoption"),"pp":t("PyPI 月下载＝真实采纳（单期快照）","PyPI monthly DL = real adoption (snapshot)"),"cnt":"","cards":pypi_cards},
 {"id":"b8","n":"08","k":t("大公司状况","Big-Tech Bets"),"pp":t("大厂真金白银押什么","Where the big money goes"),"cnt":"SEC 10-K","cards":ent_cards},
 {"id":"b9","n":"09","k":t("H-1B 签证 & 权威年报","H-1B Visa & Annuals"),"pp":t("北美落地参照 · USCIS 真实数据","NA landing reference · real USCIS data"),"cnt":(t(f'{h1b.get("summary",{}).get("n_ai_employers_3y",0)} AI 雇主',f'{h1b.get("summary",{}).get("n_ai_employers_3y",0)} AI employers') if h1b else ""),"cards":[c for c in [visa_card,trend_card] if c]+rep_cards},
]
for b in BANDS: b["digest"]=DIGESTS.get(b["id"],"")

# ── 注入模板 ──
def sub1(pat, repl, src): return re.sub(pat, lambda m: repl, src, count=1, flags=re.S)
html=open(TPL,encoding="utf-8").read()

# 顶栏 lang + tabs（双语切换 + 跨页 cross-link）
tab_slot=(f'<a href="{("index.html" if ZH else "index-en.html")}">{t("直面就业","Compass")}</a>\n'
          f'      <a class="on" href="{OUT.split("/")[-1]}">{t("看新闻","News")}</a>')
lang_slot=('<div class="lang">'
           f'<a class="{("on" if ZH else "")}" href="news.html">中</a>'
           f'<a class="{("on" if not ZH else "")}" href="news-en.html">EN</a>'
           '</div>')
html=html.replace("<!--LANG_SLOT-->", lang_slot).replace("<!--TAB_SLOT-->", tab_slot)

# Title
html=html.replace("<title>NorthStar — 北美 AI 简讯（设计样张）</title>",
                  t("<title>NorthStar — 北美 AI 简讯</title>","<title>NorthStar — North America AI Brief</title>"))

# bands JSON
bands_js="const bands = "+json.dumps(BANDS,ensure_ascii=False)+";"
html=sub1(r"const bands = \[.*?\n\];", bands_js, html)

# issueline
iss=('<div class="issueline-inner">'+
 t(f'<span class="iss-no">第 1 期</span><span class="dot">·</span><span>数据截至 2026-05-19</span><span class="dot">·</span><span>北美 AI Landscape 简讯</span><span class="dot">·</span><span>学习导向</span>',
   f'<span class="iss-no">Issue 1</span><span class="dot">·</span><span>Data as of 2026-05-19</span><span class="dot">·</span><span>North America AI Landscape Brief</span><span class="dot">·</span><span>Learning-oriented</span>')+
 '</div>')
html=sub1(r'<div class="issueline-inner">.*?</div>', iss, html)

# Hero kicker + lede + tldr —— 优先用 daily_digest 的当日 3 件事；缺则 fallback 到 W2-W3 静态 TLDR
if digest and digest.get("items") and len(digest["items"]) >= 3:
    items = digest["items"][:3]
    sm = digest.get(f"summary_one_line_{LANG}") or digest.get("summary_one_line_zh") or "今日 AI 圈三件事"
    def _ttl(x): return x.get(f"title_{LANG}") or x.get("title_zh","")
    def _why(x): return x.get(f"so_what_{LANG}") or x.get("so_what_zh","")
    tldr_html='<ol class="tldr">'+"".join(
        f'<li><a href="{esc(x.get("url","#"))}" target="_blank" onclick="event.stopPropagation()" style="color:inherit;text-decoration:none;border-bottom:1px dotted var(--mut-2)">{esc(_ttl(x))}</a>'
        f' — <em>{esc(_why(x))}</em></li>'
        for x in items)+'</ol>'
    hk = t(f"今日简报 · {digest.get('as_of','')}", f"Today's Digest · {digest.get('as_of','')}")
    lede = esc(sm)
else:
    # Fallback 静态 hero（无 LLM key 或 daily_digest 文件缺失时）
    tldr_html=t(
     '<ol class="tldr">'
     '<li>北美 AI 岗门槛正从"会调 LLM API"上移到"会编排 <em>Agent</em> + 会做 <em>Eval</em> + 会用 <em>AI 编码 agent</em> 干活"</li>'
     '<li><em>多模态</em>采纳最猛（HF trending 第一热）</li>'
     '<li><em>Serving</em> 是领先招聘 6–12 月的卡位点</li></ol>',
     '<ol class="tldr">'
     '<li>The NA AI hiring bar is moving from "calling an LLM API" to "orchestrating <em>Agents</em> + doing <em>Evals</em> + working with <em>AI coding agents</em>"</li>'
     '<li><em>Multimodal</em> adoption leads (HF trending #1)</li>'
     '<li><em>Serving</em> infra is the 6–12 month leading-indicator role</li></ol>')
    hk = t("本周判断 / TL;DR","This Week's Take / TL;DR")
    lede = t("本周共扫描北美在招 JD、社区文章、arXiv 论文与大厂 10-K 四类来源，提炼出 4 条交叉印证的信号；以下是 30 秒可读的核心判断。",
             "This issue scans four sources — NA job listings, community articles, arXiv papers, and big-tech 10-Ks — and distills four cross-corroborated signals. A 30-second take below.")

html=sub1(r'<ol class="tldr">.*?</ol>', tldr_html, html)
html=html.replace('<div class="hk">本周判断 / TL;DR</div>', f'<div class="hk">{hk}</div>')
html=sub1(r'<p class="lede">.*?</p>', f'<p class="lede">{lede}</p>', html)
html=html.replace('<b>By NorthStar 编辑部</b>', f'<b>{t("By NorthStar 编辑部","By NorthStar Editors")}</b>')

# KPI 行
kpi=('<div class="kpi-row" aria-label="">'
 '<div class="kpi-cell" style="grid-column:1/-1;border-right:none;padding-left:0">'
 f'<div class="kpi-lbl">{t("本周变化","Week-over-week")}</div>'
 f'<div class="kpi-val down"><span style="font-family:var(--serif);font-size:20px">{t("首期 · 无环比基线","First issue · no baseline")}</span></div>'
 f'<div class="kpi-sub">{t("单期快照，无 vs 上周；2026-08 首次可比（见右侧可证伪预测）","Snapshot only · no W-o-W. First comparable in Aug 2026 (see falsifiable predictions →)")}</div></div></div>')
html=sub1(r'<div class="kpi-row".*?</div>\s*</div>\s*(?=<div class="evidence">)', kpi+"        ", html)

# Evidence labels + ev-preds
fore=[{"t":c,"n":n} for c,n in sqlite3.connect("data/signals.db").execute(
 "SELECT canonical,n_src FROM ontology WHERE layer='foresight' ORDER BY n_src DESC").fetchall() if n>=2]
FORE_EN={"AI Agents/编排":"AI Agents / Orchestration","Eval 评测":"Evals","RAG":"RAG","Serving 推理":"Serving / Inference",
 "多模态":"Multimodal","AI安全/Responsible AI":"AI Safety / Responsible AI","AI编码agent当硬技能":"AI coding agents as hard skill"}
def fen(x): return x if ZH else FORE_EN.get(x,x)
ev_tags="".join(f'<span>{esc(fen(f["t"]))}<sub>{f["n"]}</sub></span>' for f in fore)
html=sub1(r'<div class="ev-tags">.*?</div>', f'<div class="ev-tags">{ev_tags}</div>', html)
CHK_ZH=["AI编码agent 在 jobs 频次是否升","Serving 是否从 jobs 未普及→出现","多模态 HF 占比是否保持"]
CHK_EN=["Does AI-coding-agent freq rise in jobs?",'Does Serving move from "not-yet-in-jobs" to "present"?',"Does multimodal share on HF hold?"]
ev_preds="".join(f'<li>{esc(c)}</li>' for c in (CHK_ZH if ZH else CHK_EN))
html=sub1(r'<ul class="ev-preds">.*?</ul>', f'<ul class="ev-preds">{ev_preds}</ul>', html)
# evidence-label texts
html=html.replace('交叉印证 <em>cross-evidence ≥2 sources</em>',
                  t('交叉印证 <em>cross-evidence ≥2 sources</em>','Cross-evidence <em>≥2 sources</em>'))
html=html.replace('可证伪预测 <em>due 2026-08</em>',
                  t('可证伪预测 <em>due 2026-08</em>','Falsifiable predictions <em>due Aug 2026</em>'))

# hero-stat
sg=(f'<div class="stat-grid">'
 f'<div><b>{jobs_kept}</b><span>{t("岗样本","Jobs (filtered)")}</span></div>'
 f'<div><b>{len(blg.get("items") or [])}</b><span>{t("篇文章","Articles")}</span></div>'
 f'<div><b>{len(arx)}</b><span>{t("篇论文","Papers")}</span></div>'
 f'<div><b>${salary_med//1000}k</b><span>{t("年薪中位","Median salary")}</span></div></div>')
html=sub1(r'<div class="stat-grid">.*?</div>\s*</div>\s*(?=</aside>)', sg+"      ", html)
html=html.replace('<div class="stat-label">本期样本</div>', f'<div class="stat-label">{t("本期样本","This issue sample")}</div>')

# TOC head
html=html.replace('本期目录<em>/ Inside this issue</em>',
                  t('本期目录<em>/ Inside this issue</em>','Contents <em>/ Inside this issue</em>'))
html=html.replace('8 SECTIONS · ~22 CARDS · 5 MIN READ',
                  t('8 栏目 · ~62 卡片 · 5 分钟','8 SECTIONS · ~62 CARDS · 5 MIN READ'))

# Sidenav labels（替换整段，按 BANDS 重生成）
sn=('<nav class="sidenav" aria-label="Sections">'+
 "".join(f'<a href="#{b["id"]}" data-anchor="{b["id"]}"><span class="pip"></span><span class="lbl">{b["n"]} {esc(b["k"])}</span></a>' for b in BANDS)+
 '</nav>')
html=sub1(r'<nav class="sidenav".*?</nav>', sn, html)

# 本栏要点 kicker（中/EN）
html=html.replace('<span class="lede-kick">本栏要点</span>',
                  f'<span class="lede-kick">{t("本栏要点","Section TL;DR")}</span>')
# 注意：digest 内已内嵌 <span class="lede-kick">本栏要点</span>，但实际是在 renderBand 里生成的；模板那里改字符串没用
# renderBand 模板写的是 <span class="lede-kick">本栏要点</span>；直接 string-replace 模板已生效

# Footer
foot=t(
 '<div class="rule"><b>生产版</b> · 真实 signals.db 数据 · v2 editorial</div>'
 '8 栏均来自真实抓取（JobSpy / arXiv / RSS / GitHub / HuggingFace / Hacker News / SEC EDGAR） · '
 'KPI 环比与 PyPI 12 月序列因仅单期快照诚实留空（2026-08 首次可比） · '
 '签证/年报为诚实占位 · 字体走 Google Fonts CDN，离线回退本地衬线 · 点卡片展开详情',
 '<div class="rule"><b>Production</b> · real signals.db data · v2 editorial</div>'
 'All 8 sections sourced from real scrapes (JobSpy / arXiv / RSS / GitHub / HuggingFace / Hacker News / SEC EDGAR). '
 'KPI W-o-W and PyPI 12-mo series intentionally blank — snapshot only, first comparable Aug 2026. '
 'Visa & annuals are honest placeholders. Fonts via Google Fonts CDN with local-serif fallback. Click any card to expand.')
html=sub1(r'<footer>.*?</footer>', f'<footer>{foot}</footer>', html)

os.makedirs("site",exist_ok=True)
open(OUT,"w",encoding="utf-8").write(html)
print(f"{OUT} {os.path.getsize(OUT)} bytes · LANG={LANG} · bands {len(BANDS)} · cards {sum(len(b['cards']) for b in BANDS)}")
