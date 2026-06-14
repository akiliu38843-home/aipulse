"""W4+ '看新闻' — 双语版（中/EN）。
用法: python3 build_news.py [zh|en]     默认 zh
输出: site/news.html (zh) 或 site/news-en.html (en)"""
import json, os, re, sys, sqlite3, collections
from translate import translate_to_zh, classify_article

LANG = (sys.argv[1] if len(sys.argv)>1 else "zh").lower()
ZH = LANG == "zh"
def t(zh, en):
    if ZH:
        return translate_to_zh(en, "AI news") if (not zh or not zh.strip()) else zh
    else:
        return en if en else en
OUT = "site/news.html" if ZH else "site/news-en.html"
OUT_FEEDS = "site/news-feeds.html" if ZH else "site/news-feeds-en.html"

def L(fp, d=None):
    try: return json.load(open(fp))
    except: return d if d is not None else {}

jw=L("data/jobs_w1.json",{}); blg=L("data/blogs_w2.json",{}); oss=L("data/foresight_oss.json",[])
ossv2=L("data/foresight_oss_v2.json",[]); w3=L("data/w3_sources.json",{}); edg=L("data/edgar_w2.json",{})
sd=L("data/site_data.json",{}); ex=L("data/w4_extra.json",{}); h1b=L("data/h1b_ai.json",{})
digest=L("data/daily_digest_latest.json",{})
nl_data=L("data/newsletters.json",{"sources":[]})
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
    jobs.append({"hl":esc(t("", tit)),"mt":esc(f"{co} · {loc}"),"dg":esc(t("", brief)),
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
talk_cards=[{"author":initials(x["src"]),"hl":esc(t("", x["t"])),
    "mt":esc(f'{x["src"]} · {x["date"]}'),"dg":esc(t("", x["sum"]) if x["sum"] else t("（该 RSS 源未提供摘要）","(this RSS source provides no summary)")),
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
         f'{esc(t("", h.get("title","")))}</a>'),
   "mt":f'{h.get("points","?")} pts{(" · "+esc(_domain(h.get("url","")))) if _domain(h.get("url","")) else ""}',
   "dg":esc(t("", _hn_sum(h.get("url","")))),
   "more":[[t("分数","Points"),str(h.get("points",""))],
           [t("链接","Link"),esc((h.get("url") or "")[:80]) or "—"],
           [t("摘要状态","Summary"),(HN_SUMS.get(h.get("url",""),{}) or {}).get("status","-")]]
} for h in hn_hot]

# 研究前沿
arx=[{"t":p.get("title",""),"date":p.get("date",""),"au":p.get("authors",""),
      "link":p.get("link",""),"sum":clean(p.get("summary",""),200)} for p in ((ex.get("arxiv") or {}).get("papers") or [])][:12]
arx_cards=[{"subj":{"label":"arXiv","color":"#2A6FDB"},"hl":esc(t("", a["t"])),
    "mt":esc(f'{a["date"]} · {a["au"]}'),"dg":esc(t("", a["sum"])),
    "more":[[t("日期","Date"),esc(a["date"])],[t("作者","Authors"),esc(a["au"])]]} for a in arx]

# 开源项目 & 模型 — 动态读 GitHub Trending（来自 fetch_newsletters.py 抓的当日数据）
import re as _re2

def _gh_cat(repo, desc):
    """Auto-label repo by name + description"""
    s = (repo + " " + desc).lower()
    if any(x in s for x in ["agent","agentic","multi-agent","mcp","langchain","langgraph","crewai","autogen"]): return t("AI Agent","AI Agent")
    if any(x in s for x in ["rag","retrieval","vector","embedding","llama_index","llamaindex"]): return t("RAG","RAG")
    if any(x in s for x in ["inference","serving","deploy","vllm","lmcache","kv cache","throughput"]): return t("推理/部署","Inference")
    if any(x in s for x in ["train","fine-tun","finetun","lora","rlhf","sft","pretraining","from scratch"]): return t("训练","Training")
    if any(x in s for x in ["diffusion","stable diffusion","image gen","text-to-image","comfyui","webui"]): return t("图像生成","Image Gen")
    if any(x in s for x in ["vision","multimodal","multi-modal","vlm","video","image-text"]): return t("多模态","Multimodal")
    if any(x in s for x in ["eval","benchmark","test","measure","hallucin"]): return t("Eval 评测","Evals")
    if any(x in s for x in ["security","safe","vulnerability","scan","scanner","red team"]): return t("安全","Security")
    if any(x in s for x in ["voice","speech","audio","tts","whisper","asr"]): return t("语音","Speech")
    if any(x in s for x in ["code","coding","copilot","program","interpreter","devtools"]): return t("编程工具","Coding")
    if any(x in s for x in ["knowledge","wiki","note","obsidian","document","search"]): return t("知识管理","Knowledge")
    return t("AI 工具","AI Tool")

PAL=["#5B3FB8","#1F6F4A","#CC3B1B","#2A6FDB","#9A6B1F","#0F1419"]

# 从 newsletters.json 提取 GitHub Trending 数据
_nl_data = L("data/newsletters.json", {})
_gh_trending = []
for _src in _nl_data.get("sources", []):
    if "GitHub" in _src.get("name", "") and "Trending" in _src.get("name", ""):
        for _it in _src.get("items", []):
            _title = _it.get("title", "")
            _summary_en = _it.get("summary", "")
            _summary = (_it.get("summary_zh") or _summary_en) if ZH else _summary_en
            _link = _it.get("link", "")
            # 解析今日星数：'🔥 owner/repo · ⭐N today'
            _mstars = _re2.search(r'⭐([\d,]+)', _title)
            _stars_today = int(_mstars.group(1).replace(",","")) if _mstars else 0
            # 解析仓库名
            _mrepo = _re2.search(r'[\U0001F300-\U0001FFFF☀-➿]\s*([\w.-]+/[\w.-]+)', _title)
            if not _mrepo: _mrepo = _re2.search(r'([\w.-]+/[\w.-]+)', _title)
            _repo = _mrepo.group(1) if _mrepo else ""
            if not _repo: continue
            _gh_trending.append({
                "repo": _repo, "stars_today": _stars_today,
                "desc": _summary, "link": _link,
                "cat": _gh_cat(_repo, _summary_en),  # 分类用英文 summary 更准
            })

# 按今日涨星排序
_gh_trending.sort(key=lambda x: -x["stars_today"])

proj_cards=[]
if _gh_trending:
    # 用 GitHub Trending 动态数据填卡片
    for i, p in enumerate(_gh_trending[:8]):
        _stars_label = f'⭐{p["stars_today"]:,} {t("今日新增","stars today")}'
        proj_cards.append({
            "mono": {"letter": p["repo"].split("/")[-1][0].upper(), "color": PAL[i%len(PAL)]},
            "hl": esc(p["repo"]), "link": p["link"],
            "mt": esc(p["cat"]), "dg": esc(p["desc"]),
            "custom_ft": (
                f'<div class="starline">'
                f'<span class="s-big">{_stars_label}</span>'
                f'<span class="s-heat">🔥 {t("今日 GitHub 热榜","GitHub Trending Today")}</span>'
                f'</div>'
            ),
            "more": [
                [t("分类","Category"), esc(p["cat"])],
                [t("今日涨星","Stars Today"), _stars_label],
                [t("来源","Source"), "GitHub Trending"],
            ]
        })
else:
    # Fallback：静态名单（无 Trending 数据时兜底）
    _FALLBACK = [
        ("vllm-project/vllm", t("推理/部署","Inference"), t("高吞吐 LLM 推理引擎","High-throughput LLM inference engine")),
        ("langchain-ai/langgraph", t("AI Agent","AI Agent"), t("有状态多智能体编排框架","Stateful multi-agent orchestration")),
        ("confident-ai/deepeval", t("Eval 评测","Evals"), t("LLM/Agent 单元测试评测框架","Unit-test eval framework for LLMs")),
    ]
    for i, (repo, cat, desc) in enumerate(_FALLBACK):
        proj_cards.append({
            "mono": {"letter": repo.split("/")[-1][0].upper(), "color": PAL[i%len(PAL)]},
            "hl": esc(repo), "mt": esc(cat), "dg": esc(desc),
            "custom_ft": f'<div class="starline"><span class="s-heat">⚠️ {t("暂无今日数据","No trending data today")}</span></div>',
            "more": [[t("分类","Category"), esc(cat)]],
        })
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
# top_proj：兼容旧字段（dir/c4w），从 _gh_trending 派生
def _tp(i):
    if i < len(_gh_trending):
        r = _gh_trending[i]
        return {"repo": r["repo"], "dir": r["cat"], "c4w": r["stars_today"]}
    return {"repo": "-", "dir": "", "c4w": 0}
top_proj = [_tp(0), _tp(1)]
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
  f"今日 GitHub Trending AI 热榜：<br>"
  f"<b>{top_proj[0]['repo'].split('/')[-1]}</b>（{top_proj[0]['dir']}）今日 +⭐<em>{top_proj[0]['c4w']:,}</em>、"
  f"<b>{top_proj[1]['repo'].split('/')[-1]}</b>（{top_proj[1]['dir']}）+⭐<em>{top_proj[1]['c4w']:,}</em> 居前。<br>"
  f"共 <b>{len(_gh_trending)}</b> 个 AI 仓上榜。HF trending 中 <b>{hf_mm}</b> 个多模态品类。",
  f"GitHub Trending AI today:<br>"
  f"<b>{top_proj[0]['repo'].split('/')[-1]}</b> ({top_proj[0]['dir']}) +⭐<em>{top_proj[0]['c4w']:,}</em>, "
  f"<b>{top_proj[1]['repo'].split('/')[-1]}</b> ({top_proj[1]['dir']}) +⭐<em>{top_proj[1]['c4w']:,}</em> lead.<br>"
  f"<b>{len(_gh_trending)}</b> AI repos trending. HF has <b>{hf_mm}</b> multimodal models."),

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

# ── 简报文章按类型分类（打散全部信源，按内容重组）──
# 类型定义：(中文名, band-id, 英文关键词列表, 中文描述, 英文描述)
NL_CATS=[
 ("产品 & 发布","nl-cat-product",
  ["release","launch","announced","introduces","rolls out","unveils","ships","available","new model","update","gpt","claude","gemini","llama","mistral","grok","copilot","assistant"],
  "新模型发布 · 产品上线 · 功能更新","New model releases · product launches · feature updates"),
 ("研究 & 论文","nl-cat-research",
  ["paper","research","study","arxiv","benchmark","training","algorithm","dataset","evaluation","we propose","experiment","architecture","pretraining","fine-tun","reasoning","scaling"],
  "学术论文 · 基准测试 · 技术深挖","Academic papers · benchmarks · technical deep-dives"),
 ("开源 & 工具","nl-cat-oss",
  ["open source","open-source","github","huggingface","framework","library","sdk","weights","developer","tool","open weight","open model","langchain","llamaindex","vllm","ollama"],
  "开源框架 · HuggingFace 新项目 · 开发者工具","Open-source frameworks · HuggingFace · dev tools"),
 ("商业 & 产业","nl-cat-biz",
  ["funding","investment","enterprise","revenue","deal","acquisition","startup","valuation","billion","million","raises","Series","venture","partnership","customer","contract"],
  "融资动态 · 企业采购 · 产业格局","Funding · enterprise deals · industry landscape"),
 ("政策 & 安全","nl-cat-safety",
  ["regulation","safety","policy","ethics","copyright","government","law","risk","alignment","responsible","bias","harm","governance","privacy","trust","misinformation","copyright"],
  "AI 安全 · 监管政策 · 伦理责任","AI safety · regulation · ethics & governance"),
 ("观点 & 分析","nl-cat-opinion",
  ["opinion","analysis","why","how to","review","perspective","lessons","thoughts","reflections","deep dive","explained","guide","commentary","insights","predictions","future of","what"],
  "深度分析 · 观点评论 · 趋势解读","Analysis · opinions · trend interpretation"),
]
NL_CAT_OTHER=("其他资讯","nl-cat-other",[],"其他 AI 相关动态","Other AI news")

def _nl_classify(title,summary):
    # P1-2: 先用 DeepSeek AI 分类（ZH 模式且有 key 时）
    if ZH:
        ai_id = classify_article(title, summary)
        if ai_id:
            for cat_name, cat_id, *_ in NL_CATS:
                if cat_id == ai_id: return (cat_name, cat_id)
            if ai_id == NL_CAT_OTHER[1]: return (NL_CAT_OTHER[0], NL_CAT_OTHER[1])
    # 降级：关键词匹配
    text=(title+" "+summary).lower()
    best,best_n=None,0
    for cat_name,cat_id,kws,_,_ in NL_CATS:
        score=sum(1 for kw in kws if kw in text)
        if score>best_n: best_n=score; best=(cat_name,cat_id)
    return best if best else (NL_CAT_OTHER[0],NL_CAT_OTHER[1])

# 扁平化所有文章
_nl_all=[]
for _src in (nl_data.get("sources",[]) or []):
    for _item in (_src.get("items") or []):
        _nl_all.append({**_item,"_src_name":_src["name"],"_src_id":_src["id"]})

# ── P0-1 去重聚类：全局把"同一条新闻被多家报道"并成一个簇 ──
import re as _re
_NL_STOP={"this","that","with","from","your","what","which","have","will","about","they",
 "their","more","than","into","when","some","these","could","would","should","being","there",
 "here","just","like","over","after","before","while","first","also","most","much","such",
 "make","made","using","used","still","even","other","every","says","said","gets","new","now"}
_NL_ENT=_re.compile(r'\b(OpenAI|Anthropic|Claude|GPT|Gemini|Google|DeepMind|Meta|Llama|Mistral|'
 r'DeepSeek|Grok|ChatGPT|Sora|Nvidia|xAI|Apple|Microsoft|Qwen|Amazon|Cohere|Perplexity|'
 r'Mythos|Fable|Codex|Copilot|HuggingFace)\b', _re.I)
def _nl_kw(t):
    return set(w for w in _re.findall(r'[a-zA-Z]{4,}', (t or "").lower()) if w not in _NL_STOP)
def _nl_ent(t):
    return set(e.lower() for e in _NL_ENT.findall(t or ""))

# 预计算每篇的关键词/实体（仅用标题，避免摘要噪声）
for _a in _nl_all:
    _ttl=_a.get("title","")
    _a["_kw"]=_nl_kw(_ttl)
    _a["_ent"]=_nl_ent(_ttl+" "+_a.get("summary",""))
    # 摘要型标题检测：逗号≥2 或 标题里实体≥3 = 多话题拼接，不能当合并桥（否则错连一堆不相关新闻）
    _a["_digest"]=(_ttl.count(",")>=2 or _ttl.count("，")>=2 or len(_nl_ent(_ttl))>=3)

# 并查集
_parent=list(range(len(_nl_all)))
def _find(x):
    while _parent[x]!=x: _parent[x]=_parent[_parent[x]]; x=_parent[x]
    return x
def _union(a,b):
    ra,rb=_find(a),_find(b)
    if ra!=rb: _parent[ra]=rb

# 两两判定（保守阈值：共享实词≥3，或 共享实体≥1 且 共享实词≥2）
for _i in range(len(_nl_all)):
    if _nl_all[_i]["_digest"]: continue          # 摘要型不当桥
    for _j in range(_i+1,len(_nl_all)):
        if _nl_all[_j]["_digest"]: continue
        if _nl_all[_i]["_src_name"]==_nl_all[_j]["_src_name"]: continue
        _ck=_nl_all[_i]["_kw"]&_nl_all[_j]["_kw"]
        _ce=_nl_all[_i]["_ent"]&_nl_all[_j]["_ent"]
        if len(_ck)>=3 or (len(_ce)>=1 and len(_ck)>=2):
            _union(_i,_j)

# 收簇
_clusters={}
for _i in range(len(_nl_all)):
    _clusters.setdefault(_find(_i),[]).append(_nl_all[_i])

# 选代表：① 新闻媒体源优先（标题最像新闻）② 最"中心"成员（与其他成员词重叠最多）
#         ③ 避开营销/CTA 标题 ④ 非摘要型、逗号少、长度适中
_DIGEST_SRC={"TLDR AI","Last Week in AI","Hacker News AI 热议"}
_NEWS_SRC={"The Decoder","VentureBeat AI","TechCrunch AI","The Verge AI",
           "MIT Technology Review AI","The Sequence","Interconnects","Synced AI"}
_MKT_PAT=_re.compile(r'(?i)(access |through your|get started|available now|sign up|'
                     r'commitment|pricing|buy now|introducing your|now available)')
def _src_tier(name):
    if name in _NEWS_SRC: return 2      # 新闻媒体，最适合当头条
    if name in _DIGEST_SRC: return 0    # 摘要/聚合源，最差
    return 1                            # 官博/个人博客，居中
def _make_cluster(members):
    # 中心度：每个成员标题词 与 其他成员标题词并集 的重叠数
    def centroid(m):
        others=set()
        for o in members:
            if o is not m: others|=o.get("_kw",set())
        return len(m.get("_kw",set()) & others)
    def rep_key(m):
        tit=m.get("title","")
        return (_src_tier(m["_src_name"]),                 # 新闻源优先
                centroid(m),                               # 最中心（多数家的说法）
                0 if _MKT_PAT.search(tit) else 1,          # 非营销标题优先
                -tit.count(","),                           # 逗号少
                -abs(len(tit)-65))                         # 长度适中
    members=sorted(members,key=rep_key,reverse=True)
    rep=members[0]
    srcs=[]
    for m in members:
        if m["_src_name"] not in srcs: srcs.append(m["_src_name"])
    return {"rep":rep,"members":members,"srcs":srcs,"size":len(srcs)}
_nl_clusters=[_make_cluster(ms) for ms in _clusters.values()]

# 分类（按代表标题+摘要）
for _c in _nl_clusters:
    _cname,_cid=_nl_classify(_c["rep"].get("title",""),_c["rep"].get("summary",""))
    _c["cat_id"]=_cid; _c["cat_name"]=_cname

# P0-2 今日头条：被最多家报道的 Top 簇（仅取多源簇）
_nl_top=sorted([c for c in _nl_clusters if c["size"]>=2],key=lambda c:(-c["size"],c["rep"].get("date","")))[:3]

# 把簇渲染成一张卡
def _cluster_card(c,rank=None):
    rep=c["rep"]; _link=rep.get("link","") or "#"
    _title=t("", rep.get("title",""))
    _sum=t("", clean(rep.get("summary",""),200)) if rep.get("summary","") else t("（未提供摘要）","(no summary)")
    _badge=(f'<span style="display:inline-block;font:600 11px var(--mono);color:var(--acc);'
            f'background:#FBEAE4;padding:1px 7px;border-radius:20px;margin-right:6px">'
            f'🔗 {c["size"]} {t("家在报道","sources")}</span>') if c["size"]>=2 else ""
    _hl=(f'{_badge}<a href="{esc(_link)}" target="_blank" onclick="event.stopPropagation()" '
         f'style="color:inherit;text-decoration:none;border-bottom:1px dotted var(--mut-2)">'
         f'{esc(_title)}</a>')
    _mt=esc(f'{rep["_src_name"]} · {rep.get("date","")}')
    if c["size"]>=2:
        _mt+=esc(f' · +{c["size"]-1} '+t("家","more"))
    # more: 列出每家的标题+链接
    _more=[[t("分类","Category"),esc(t(c["cat_name"],c["cat_name"]))],
           [t("报道家数","Coverage"),f'{c["size"]} '+t("家","sources")]]
    for m in c["members"][:8]:
        _ml=m.get("link","") or "#"
        _more.append([esc(m["_src_name"]),
            f'<a href="{esc(_ml)}" target="_blank" style="color:var(--acc)">{esc(t("",m.get("title",""))[:50])}</a>'])
    return {"hl":_hl,"mt":_mt,"dg":esc(_sum),"more":_more}

# 按分类分组（簇为单位）
_nl_groups={cat_id:[] for _,cat_id,*_ in NL_CATS}
_nl_groups[NL_CAT_OTHER[1]]=[]
for _c in _nl_clusters:
    _nl_groups[_c["cat_id"]].append(_c)
# 每组内：多源簇优先（被报道越多越靠前），再按日期
for _cid in _nl_groups:
    _nl_groups[_cid].sort(key=lambda c:(-c["size"],c["rep"].get("date","")),reverse=False)
    _nl_groups[_cid].sort(key=lambda c:(c["size"],c["rep"].get("date","")),reverse=True)

# 构建 nl_bands（每个类型→一行）
nl_bands=[]
for cat_name,cat_id,_kws,desc_zh,desc_en in NL_CATS+[NL_CAT_OTHER]:
    _cs=_nl_groups.get(cat_id,[])
    if not _cs: continue
    _src_set=set(s for c in _cs for s in c["srcs"])
    _art_n=sum(len(c["members"]) for c in _cs)
    _nl_cards=[_cluster_card(c) for c in _cs]
    nl_bands.append({
        "id":cat_id,
        "n":f"{len(nl_bands)+1:02d}",
        "k":t(cat_name,cat_name),
        "pp":t(desc_zh,desc_en),
        "cnt":t(f'{len(_cs)} 条 · {_art_n} 篇 · {len(_src_set)} 家',
                f'{len(_cs)} stories · {_art_n} articles · {len(_src_set)} sources'),
        "cards":_nl_cards,
        "digest":"",
    })

# ── P1-1 今日热度榜：全部簇按「被报道家数 × 信源层级」排序 ──
_hot_clusters=sorted(_nl_clusters,
    key=lambda c:(c["size"]*10+_src_tier(c["rep"]["_src_name"]), c["rep"].get("date","")),
    reverse=True)[:15]

def _ranked_card(c, rank):
    """在 _cluster_card 基础上加排名前缀"""
    card=_cluster_card(c)
    _rk=(f'<span style="display:inline-block;min-width:26px;font:700 12px var(--mono);'
         f'color:var(--mut-2);margin-right:4px">#{rank}</span>')
    card["hl"]=_rk+card["hl"]
    return card

_hot_cards=[_ranked_card(c,i+1) for i,c in enumerate(_hot_clusters)]
_hot_multi=sum(1 for c in _hot_clusters if c["size"]>=2)
_hot_band={
    "id":"nl-hot",
    "n":"🔥",
    "k":t("今日热度榜","Hot Today"),
    "pp":t("按「被多家媒体同时报道」排序 · 越靠前越重要",
           "Ranked by cross-source coverage · more outlets = more important"),
    "cnt":t(f'前 {len(_hot_clusters)} 条 · 其中 {_hot_multi} 条多源',
            f'Top {len(_hot_clusters)} · {_hot_multi} multi-source'),
    "cards":_hot_cards,
    "digest":t(
        f"这 {len(_hot_clusters)} 条是当前最值得关注的 AI 新闻，热度 = 「被几家媒体同时报道」。🔗 多源报道排在前面——同一件事被越多家写到，说明圈子里公认它重要。时间有限时从第 1 条读起。",
        f"These {len(_hot_clusters)} stories are ranked by cross-source coverage. 🔗 Multi-source stories rank first — the more outlets cover a story, the more the AI community considers it important. Read top-to-bottom when time is short."),
}
# 热度榜置顶（其他分类 band 在后）
nl_bands.insert(0, _hot_band)

BANDS=[
 {"id":"b1","n":"01","k":t("岗位动态","Job Pulse"),"pp":t("北美 AI 在招什么、给多少钱","What NA AI is hiring · pay levels"),"cnt":t(f'{jobs_kept} AI-相关 / {jobs_total} 抓取',f'{jobs_kept} AI-relevant / {jobs_total} scraped'),"cards":jobs},
 {"id":"b2","n":"02","k":t("招聘市场风向","Hiring Signal"),"pp":t("薪资水位 + 真实技能需求","Salary level + real skill demand"),"cnt":"","cards":hire_cards},
 {"id":"b3","n":"03","k":t("AI 明星 & 社区","Voices & Community"),"pp":t("他们认为接下来什么重要","What they think matters next"),"cnt":t(f'{len(blg.get("items") or [])} 篇',f'{len(blg.get("items") or [])} pieces'),"cards":talk_cards},
 {"id":"b4","n":"04","k":t("Hacker News 热议","Hacker News Buzz"),"pp":t("社区现在吵什么 · 早期信号源","What the community is buzzing about · early signal"),"cnt":t(f'{len(hn_hot)} 条 · ≥80 pts',f'{len(hn_hot)} stories · ≥80 pts'),"cards":hn_hot_cards},
 {"id":"b5","n":"05","k":t("研究前沿","Research Frontier"),"pp":"arXiv cs.AI/LG/CL","cnt":t(f"{len(arx)} 篇",f"{len(arx)} papers"),"cards":arx_cards},
 {"id":"b6","n":"06","k":t("开源项目 & 模型","OSS & Models"),"pp":t("今日 GitHub 热榜","GitHub Trending Today"),"cnt":t(f'{len(_gh_trending)} 个',f'{len(_gh_trending)} repos') if _gh_trending else "","cards":proj_cards},
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
          f'      <a class="on" href="{OUT.split("/")[-1]}">{t("定制新闻","Custom News")}</a>\n'
          f'      <a href="{OUT_FEEDS.split("/")[-1]}">{t("常规新闻","Latest Feeds")}</a>')
lang_slot=('<div class="lang">'
           f'<a class="{("on" if ZH else "")}" href="news.html">中</a>'
           f'<a class="{("on" if not ZH else "")}" href="news-en.html">EN</a>'
           '</div>')
html=html.replace("<!--LANG_SLOT-->", lang_slot).replace("<!--TAB_SLOT-->", tab_slot)

# Title
html=html.replace("<title>AIPulse — 北美 AI 简讯（设计样张）</title>",
                  t("<title>AIPulse — 北美 AI 简讯</title>","<title>AIPulse — North America AI Brief</title>"))

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
html=html.replace('<b>By AIPulse 编辑部</b>', f'<b>{t("By AIPulse 编辑部","By AIPulse Editors")}</b>')

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
_total_cards=sum(len(b['cards']) for b in BANDS)
html=html.replace('8 SECTIONS · ~22 CARDS · 5 MIN READ',
                  t(f'{len(BANDS)} 栏目 · ~{_total_cards} 卡片 · 5 分钟',
                    f'{len(BANDS)} SECTIONS · ~{_total_cards} CARDS · 5 MIN READ'))

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
 f'<div class="rule"><b>定制新闻</b> · 真实 signals.db 数据 · v2 editorial</div>'
 f'{len(BANDS)} 栏均来自真实抓取（JobSpy / arXiv / RSS / GitHub / HuggingFace / Hacker News / SEC EDGAR） · '
 'KPI 环比与 PyPI 12 月序列因仅单期快照诚实留空（2026-08 首次可比） · '
 '签证/年报为诚实占位 · 字体走 Google Fonts CDN，离线回退本地衬线 · 点卡片展开详情',
 f'<div class="rule"><b>Custom News</b> · real signals.db data · v2 editorial</div>'
 f'All {len(BANDS)} sections sourced from real scrapes (JobSpy / arXiv / RSS / GitHub / HuggingFace / Hacker News / SEC EDGAR). '
 'KPI W-o-W and PyPI 12-mo series intentionally blank — snapshot only, first comparable Aug 2026. '
 'Visa & annuals are honest placeholders. Fonts via Google Fonts CDN with local-serif fallback. Click any card to expand.')
html=sub1(r'<footer>.*?</footer>', f'<footer>{foot}</footer>', html)

os.makedirs("site",exist_ok=True)
open(OUT,"w",encoding="utf-8").write(html)
print(f"{OUT} {os.path.getsize(OUT)} bytes · LANG={LANG} · bands {len(BANDS)} · cards {sum(len(b['cards']) for b in BANDS)}")

# ══════════════════════════════════════════════════════
# 常规新闻页（news-feeds.html）—— 12 家 AI 简报信源
# ══════════════════════════════════════════════════════
if nl_bands:
    # 给简报页重新从 01 编号
    for _fi, _fb in enumerate(nl_bands):
        _fb["n"] = f"{_fi+1:02d}"
    _fc = sum(len(b["cards"]) for b in nl_bands)
    _src_total = len(nl_data.get("sources", []) or [])  # 实际信源家数（供 issueline 用）

    # ── P2-3 信源健康：计算「上次抓取距现在多久」──
    import datetime as _dt
    _collected_at = nl_data.get("collected_at","")
    try:
        _cdt = _dt.datetime.fromisoformat(_collected_at)
        _delta = _dt.datetime.now() - _cdt
        _h = int(_delta.total_seconds()//3600)
        _m = int((_delta.total_seconds()%3600)//60)
        if _delta.days >= 1:
            _feeds_ago = t(f"{_delta.days} 天前", f"{_delta.days}d ago")
        elif _h >= 1:
            _feeds_ago = t(f"{_h} 小时前", f"{_h}h ago")
        else:
            _feeds_ago = t(f"{_m} 分钟前", f"{_m}min ago")
        _health_icon = "🟢" if _h < 12 else ("🟡" if _h < 24 else "🔴")
    except:
        _feeds_ago = t("时间未知","unknown"); _health_icon = "⚪"
    # 失败/空信源统计
    _err_srcs = [s["name"] for s in (nl_data.get("sources",[]) or [])
                 if not s.get("items") or str(s.get("status","")).startswith("err")]
    _health_tip = (t(f"⚠️ {len(_err_srcs)} 家无数据: {', '.join(_err_srcs[:3])}",
                     f"⚠️ {len(_err_srcs)} sources empty: {', '.join(_err_srcs[:3])}")
                   if _err_srcs else "")

    html_f = open(TPL, encoding="utf-8").read()

    # lang slot（指向 news-feeds.html / news-feeds-en.html）
    lang_slot_f = ('<div class="lang">'
                   f'<a class="{("on" if ZH else "")}" href="news-feeds.html">中</a>'
                   f'<a class="{("on" if not ZH else "")}" href="news-feeds-en.html">EN</a>'
                   '</div>')

    # tab slot（常规新闻 active）
    tab_slot_f = (f'<a href="{("index.html" if ZH else "index-en.html")}">{t("直面就业","Compass")}</a>\n'
                  f'      <a href="{OUT.split("/")[-1]}">{t("定制新闻","Custom News")}</a>\n'
                  f'      <a class="on" href="{OUT_FEEDS.split("/")[-1]}">{t("常规新闻","Latest Feeds")}</a>')
    html_f = html_f.replace("<!--LANG_SLOT-->", lang_slot_f).replace("<!--TAB_SLOT-->", tab_slot_f)

    # title
    html_f = html_f.replace("<title>AIPulse — 北美 AI 简讯（设计样张）</title>",
                            t("<title>AIPulse — 常规新闻</title>",
                              "<title>AIPulse — Latest AI Feeds</title>"))

    # bands JSON
    bands_js_f = "const bands = " + json.dumps(nl_bands, ensure_ascii=False) + ";"
    html_f = sub1(r"const bands = \[.*?\n\];", bands_js_f, html_f)

    # issueline（P2-3：加健康徽章 + 更新时间）
    _health_span = (f'<span style="font-size:13px">{_health_icon} '
                    + t(f'更新于 {_feeds_ago}', f'updated {_feeds_ago}')
                    + (f' · {_health_tip}' if _health_tip else '') + '</span>')
    iss_f = ('<div class="issueline-inner">' +
             t(f'<span class="iss-no">常规新闻</span><span class="dot">·</span>'
               f'<span>{_src_total} 家 AI 专业媒体</span><span class="dot">·</span>'
               f'<span>RSS 自动抓取</span><span class="dot">·</span>{_health_span}',
               f'<span class="iss-no">Latest Feeds</span><span class="dot">·</span>'
               f'<span>{_src_total} AI media sources</span><span class="dot">·</span>'
               f'<span>RSS auto-fetch</span><span class="dot">·</span>{_health_span}') +
             '</div>')
    html_f = sub1(r'<div class="issueline-inner">.*?</div>', iss_f, html_f)

    # hero tldr — P0-2 今日头条：被最多家报道的 Top 3 簇
    if _nl_top:
        tldr_html_f = ('<ol class="tldr">' +
            "".join(
              f'<li><a href="{esc(c["rep"].get("link","#"))}" target="_blank" onclick="event.stopPropagation()" '
              f'style="color:inherit;text-decoration:none;border-bottom:1px dotted var(--mut-2)">'
              f'{esc(t("",c["rep"].get("title","")))}</a> '
              f'<em style="color:var(--acc);font-style:normal;font-weight:600">· {c["size"]} {t("家在报道","sources")}</em></li>'
              for c in _nl_top) +
            '</ol>')
    else:
        tldr_html_f = ('<ol class="tldr">' +
            "".join(f'<li><b>{esc(b["k"])}</b> — {esc(b["pp"])}</li>' for b in nl_bands[:5]) +
            '</ol>')
    _multi_n=len([c for c in _nl_clusters if c["size"]>=2])
    _nl_cat_n=len([b for b in nl_bands if b["id"]!="nl-hot"])  # 分类数（不含热度榜）
    hk_f = t("今日头条 · 多家共同报道", "Today's Headlines · cross-source")
    lede_f = t(f"已自动去重的 {len(_nl_clusters)} 条新闻，来自 {_src_total} 家 AI 专业信源，按 {_nl_cat_n} 类内容归类——其中 {_multi_n} 条被两家以上同时报道。⬆️ 热度榜在最前面，下方按分类浏览，点标题直跳原文。",
               f"Auto-deduplicated {len(_nl_clusters)} stories from {_src_total} AI sources across {_nl_cat_n} categories — {_multi_n} covered by 2+ sources. ⬆️ Hot Today ranking first; browse by category below.")
    html_f = sub1(r'<ol class="tldr">.*?</ol>', tldr_html_f, html_f)
    html_f = html_f.replace('<div class="hk">本周判断 / TL;DR</div>', f'<div class="hk">{hk_f}</div>')
    html_f = sub1(r'<p class="lede">.*?</p>', f'<p class="lede">{lede_f}</p>', html_f)
    html_f = html_f.replace('<b>By AIPulse 编辑部</b>',
                            f'<b>{t("By AIPulse · RSS 自动聚合","By AIPulse · RSS auto-aggregated")}</b>')

    # KPI 行（简化：显示信源数 / 文章数）
    kpi_f = ('<div class="kpi-row" aria-label="">'
             '<div class="kpi-cell" style="grid-column:1/-1;border-right:none;padding-left:0">'
             f'<div class="kpi-lbl">{t("本次抓取","This fetch")}</div>'
             f'<div class="kpi-val"><span style="font-family:var(--serif);font-size:20px">'
             f'{len(nl_bands)} {t("家信源","sources")} · {_fc} {t("篇","articles")}</span></div>'
             f'<div class="kpi-sub">{t("RSS 实时抓取，近 14–30 天内容，每次运行自动更新","RSS live fetch · past 14–30 days · auto-refreshed each run")}</div>'
             '</div></div>')
    html_f = sub1(r'<div class="kpi-row".*?</div>\s*</div>\s*(?=<div class="evidence">)', kpi_f + "        ", html_f)

    # evidence / ev-preds — 留空
    html_f = sub1(r'<div class="ev-tags">.*?</div>', '<div class="ev-tags"></div>', html_f)
    html_f = sub1(r'<ul class="ev-preds">.*?</ul>', '<ul class="ev-preds"></ul>', html_f)
    html_f = html_f.replace('交叉印证 <em>cross-evidence ≥2 sources</em>', t('信源列表','Feed index'))
    html_f = html_f.replace('可证伪预测 <em>due 2026-08</em>', t('近期更新','Recent updates'))

    # hero-stat
    sg_f = (f'<div class="stat-grid">'
            f'<div><b>{len(nl_bands)}</b><span>{t("家信源","Sources")}</span></div>'
            f'<div><b>{_fc}</b><span>{t("篇文章","Articles")}</span></div>'
            f'<div><b>{t("日报","Daily")}</b><span>{t("更新频率","Cadence")}</span></div>'
            f'<div><b>RSS</b><span>{t("直接抓取","Live fetch")}</span></div></div>')
    html_f = sub1(r'<div class="stat-grid">.*?</div>\s*</div>\s*(?=</aside>)', sg_f + "      ", html_f)
    html_f = html_f.replace('<div class="stat-label">本期样本</div>',
                            f'<div class="stat-label">{t("信源快照","Feed snapshot")}</div>')

    # TOC head + section count
    html_f = html_f.replace('本期目录<em>/ Inside this issue</em>',
                            t('信源目录<em>/ Feed index</em>', 'Feed index <em>/ Browse by source</em>'))
    html_f = html_f.replace('8 SECTIONS · ~22 CARDS · 5 MIN READ',
                            t(f'{len(nl_bands)} 家信源 · {_fc} 篇文章',
                              f'{len(nl_bands)} SOURCES · {_fc} ARTICLES'))

    # sidenav
    sn_f = ('<nav class="sidenav" aria-label="Sections">' +
            "".join(f'<a href="#{b["id"]}" data-anchor="{b["id"]}"><span class="pip"></span>'
                    f'<span class="lbl">{b["n"]} {esc(b["k"])}</span></a>' for b in nl_bands) +
            '</nav>')
    html_f = sub1(r'<nav class="sidenav".*?</nav>', sn_f, html_f)

    # section TL;DR label
    html_f = html_f.replace('<span class="lede-kick">本栏要点</span>',
                            f'<span class="lede-kick">{t("关于本刊","About")}</span>')

    # footer
    foot_f = t(
        f'<div class="rule"><b>常规新闻</b> · RSS 自动聚合 · 每日更新</div>'
        f'{_src_total} 家 AI 专业媒体信源 · 内容版权归各发布方所有 · 点标题跳原文 · 字体走 Google Fonts CDN',
        f'<div class="rule"><b>Latest Feeds</b> · RSS auto-aggregated · updated daily</div>'
        f'{_src_total} specialized AI media sources · content copyright belongs to respective publishers · click titles to read originals · fonts via Google Fonts CDN')
    html_f = sub1(r'<footer>.*?</footer>', f'<footer>{foot_f}</footer>', html_f)

    # ── P2-2 时间过滤条 + P2-2 JS（注入到 </style> 和 </body>）──
    _date_css = """
/* P2-2 时间过滤条 */
#date-filter-bar{display:flex;align-items:center;gap:8px;padding:10px 20px;
  background:var(--bg,#faf9f7);border-bottom:1.5px solid var(--line,#e8e4df);
  position:sticky;top:52px;z-index:50;flex-wrap:wrap}
#date-filter-bar .df-label{font:600 11px var(--mono,monospace);letter-spacing:.05em;
  color:var(--mut-2,#aaa);text-transform:uppercase;margin-right:4px}
#date-filter-bar button{font:600 12px var(--mono,monospace);letter-spacing:.03em;
  padding:3px 14px;border:1.5px solid var(--line,#e8e4df);border-radius:20px;
  background:transparent;color:var(--ink-2,#888);cursor:pointer;transition:all .15s}
#date-filter-bar button.df-active,#date-filter-bar button:hover{
  border-color:var(--acc,#CC3B1B);color:var(--acc,#CC3B1B);background:#FBEAE4}
article.rc.df-hidden{display:none!important}
"""
    _filter_bar_html = (
        f'<div id="date-filter-bar">'
        f'<span class="df-label">{t("时间","Period")}</span>'
        f'<button class="df-active" data-df="all">{t("全部","All")}</button>'
        f'<button data-df="today">{t("今天","Today")}</button>'
        f'<button data-df="week">{t("本周","This week")}</button>'
        f'</div>'
        f'<div id="bands">'
    )
    _date_js = r"""
<script>
(function(){
  // P2-2 日期过滤
  function getToday(){ return new Date().toISOString().slice(0,10); }
  function getWeekAgo(){
    var d=new Date(); d.setDate(d.getDate()-7); return d.toISOString().slice(0,10);
  }
  function tagCards(){
    document.querySelectorAll('article.rc').forEach(function(el){
      var mt=el.querySelector('.mt');
      if(!mt) return;
      var m=mt.textContent.match(/(\d{4}-\d{2}-\d{2})/);
      if(m) el.dataset.dfDate=m[1];
    });
  }
  function applyFilter(range){
    var today=getToday(), weekAgo=getWeekAgo();
    document.querySelectorAll('article.rc').forEach(function(el){
      var d=el.dataset.dfDate||'';
      var hide=(range==='today'&&d<today)||(range==='week'&&d<weekAgo);
      el.classList.toggle('df-hidden', hide);
    });
    // 隐藏全空的 band section
    document.querySelectorAll('section.band').forEach(function(sec){
      var cards=sec.querySelectorAll('article.rc');
      if(!cards.length) return;
      var visible=[].some.call(cards,function(c){return !c.classList.contains('df-hidden')});
      sec.style.display=visible?'':'none';
    });
  }
  function initFilter(){
    tagCards();
    document.querySelectorAll('#date-filter-bar button').forEach(function(btn){
      btn.addEventListener('click',function(){
        document.querySelectorAll('#date-filter-bar button').forEach(function(b){b.classList.remove('df-active')});
        this.classList.add('df-active');
        applyFilter(this.dataset.df);
      });
    });
  }
  // bands 由 JS 渲染，需等 DOMContentLoaded 后再延迟一帧
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',function(){setTimeout(initFilter,120)});
  } else {
    setTimeout(initFilter,120);
  }
})();
</script>
"""
    html_f = html_f.replace('</style>', _date_css + '</style>', 1)
    html_f = html_f.replace('<div id="bands"></div>', _filter_bar_html + '</div>', 1)
    html_f = html_f.replace('</body>', _date_js + '</body>', 1)

    # ── P3-1 主题订阅 + P3-2 已读/收藏 ──
    _p3_read_lbl  = t("✓ 已读", "✓ Read")
    _p3_bm_lbl    = t("★ 收藏", "★ Save")
    _p3_all_lbl   = t("全选",   "All")
    _p3_bm_view   = t("★ 收藏夹", "★ Saved")
    _p3_topic_lbl = t("主题",   "Topics")

    _topic_btns = "".join(
        f'<button class="tf-btn tf-active" data-section="{b["id"]}">{esc(b["k"])}</button>'
        for b in nl_bands if b["id"] != "nl-hot"
    )
    _p3_css = """
/* P3-1 主题订阅 */
#topic-filter-bar{display:flex;align-items:center;gap:6px;padding:8px 20px;
  background:var(--bg,#faf9f7);border-bottom:1px solid var(--line,#e8e4df);flex-wrap:wrap}
.tf-label{font:600 11px var(--mono,monospace);letter-spacing:.05em;color:var(--mut-2,#aaa);
  text-transform:uppercase;margin-right:2px;white-space:nowrap}
.tf-btn{font:500 11.5px var(--mono,monospace);padding:3px 11px;
  border:1.5px solid var(--ink,#333);border-radius:20px;
  background:transparent;color:var(--ink,#333);cursor:pointer;transition:all .15s}
.tf-btn:not(.tf-active){opacity:0.3;border-color:var(--line,#ddd)}
.tf-btn:hover{opacity:1!important;border-color:var(--acc,#CC3B1B)!important;
  color:var(--acc,#CC3B1B)!important}
.tf-all{font:600 11px var(--mono,monospace);padding:3px 10px;
  border:1.5px dashed var(--line,#ddd);border-radius:20px;background:transparent;
  color:var(--mut-2,#aaa);cursor:pointer}
.tf-all:hover{border-color:var(--acc,#CC3B1B);color:var(--acc,#CC3B1B)}
.tf-bm-view{font:600 11px var(--mono,monospace);padding:3px 11px;
  border:1.5px solid var(--line,#ddd);border-radius:20px;background:transparent;
  color:var(--mut-2,#aaa);cursor:pointer;margin-left:auto}
.tf-bm-view:hover{border-color:#CC3B1B;color:#CC3B1B}
.tf-bm-view.bm-on{border-color:#CC3B1B;color:#CC3B1B;background:#FBEAE4}
section.band.tf-hidden{display:none!important}

/* P3-2 已读/收藏 */
article.rc{position:relative}
.card-actions{position:absolute;bottom:8px;right:8px;display:none;gap:3px;z-index:2}
article.rc:hover .card-actions{display:flex}
.ca-btn{font:600 11px var(--mono,monospace);padding:2px 8px;
  border:1px solid var(--line,#ddd);border-radius:11px;
  background:var(--bg,#faf9f7);color:var(--mut-2,#aaa);cursor:pointer;
  transition:all .15s;white-space:nowrap;line-height:1.5}
.ca-btn:hover{border-color:var(--acc,#CC3B1B);color:var(--acc,#CC3B1B)}
article.rc.is-read{opacity:0.45}
article.rc.is-read .ca-read{color:var(--acc,#CC3B1B);border-color:var(--acc,#CC3B1B)}
article.rc.is-bookmarked .ca-bm{color:#CC3B1B;border-color:#CC3B1B;background:#FBEAE4}
article.rc.is-bookmarked::before{content:"★";position:absolute;top:7px;right:7px;
  font-size:11px;color:#CC3B1B;z-index:3;pointer-events:none}
article.rc.bm-hidden{display:none!important}
"""
    _p3_topic_bar = (
        f'<div id="topic-filter-bar">'
        f'<span class="tf-label">{_p3_topic_lbl}</span>'
        + _topic_btns +
        f'<button class="tf-all">{_p3_all_lbl}</button>'
        f'<button class="tf-bm-view">{_p3_bm_view}</button>'
        f'</div>\n'
    )
    _p3_js = f"""
<script>
(function(){{
  // P3-1 主题订阅
  var LS_TOPICS='aipulse-topics-hidden';
  function applyTopics(){{
    if(document.querySelector('.tf-bm-view.bm-on')) return;
    document.querySelectorAll('.tf-btn').forEach(function(btn){{
      var sec=document.getElementById(btn.dataset.section);
      if(sec) sec.classList.toggle('tf-hidden',!btn.classList.contains('tf-active'));
    }});
  }}
  function saveTopics(){{
    var h=[];
    document.querySelectorAll('.tf-btn:not(.tf-active)').forEach(function(b){{h.push(b.dataset.section)}});
    localStorage.setItem(LS_TOPICS,JSON.stringify(h));
  }}
  function initTopicFilter(){{
    var hidden=JSON.parse(localStorage.getItem(LS_TOPICS)||'[]');
    document.querySelectorAll('.tf-btn').forEach(function(btn){{
      if(hidden.indexOf(btn.dataset.section)>=0) btn.classList.remove('tf-active');
      btn.addEventListener('click',function(){{
        this.classList.toggle('tf-active');
        applyTopics(); saveTopics();
      }});
    }});
    var allBtn=document.querySelector('.tf-all');
    if(allBtn) allBtn.addEventListener('click',function(){{
      document.querySelectorAll('.tf-btn').forEach(function(b){{b.classList.add('tf-active')}});
      applyTopics(); saveTopics();
    }});
    var bmBtn=document.querySelector('.tf-bm-view');
    if(bmBtn) bmBtn.addEventListener('click',function(){{
      this.classList.toggle('bm-on');
      var on=this.classList.contains('bm-on');
      document.querySelectorAll('article.rc').forEach(function(c){{
        c.classList.toggle('bm-hidden', on&&!c.classList.contains('is-bookmarked'));
      }});
      document.querySelectorAll('section.band').forEach(function(sec){{
        if(on){{
          var vis=[].some.call(sec.querySelectorAll('article.rc'),
            function(c){{return !c.classList.contains('bm-hidden')}});
          sec.style.display=vis?'':'none';
        }}else{{
          sec.style.display=''; applyTopics();
        }}
      }});
    }});
    applyTopics();
  }}

  // P3-2 已读/收藏
  var READ_LBL='{_p3_read_lbl}';
  var BM_LBL='{_p3_bm_lbl}';
  function getCardKey(el){{
    var a=el.querySelector('.hl a[href]');
    if(!a||!a.href||a.href==='#') return null;
    return 'aipulse:'+a.href;
  }}
  function initCardActions(){{
    document.querySelectorAll('article.rc').forEach(function(card){{
      var key=getCardKey(card);
      if(!key) return;
      var state=JSON.parse(localStorage.getItem(key)||'{{}}');
      if(state.read) card.classList.add('is-read');
      if(state.bookmarked) card.classList.add('is-bookmarked');
      var bar=document.createElement('div');
      bar.className='card-actions';
      bar.innerHTML='<button class="ca-btn ca-read">'+READ_LBL+'</button>'
                   +'<button class="ca-btn ca-bm">'+BM_LBL+'</button>';
      card.appendChild(bar);
      bar.querySelector('.ca-read').addEventListener('click',function(e){{
        e.stopPropagation();
        state.read=!state.read;
        card.classList.toggle('is-read',state.read);
        localStorage.setItem(key,JSON.stringify(state));
      }});
      bar.querySelector('.ca-bm').addEventListener('click',function(e){{
        e.stopPropagation();
        state.bookmarked=!state.bookmarked;
        card.classList.toggle('is-bookmarked',state.bookmarked);
        var bmOn=document.querySelector('.tf-bm-view.bm-on');
        if(bmOn&&!state.bookmarked) card.classList.add('bm-hidden');
        else if(bmOn&&state.bookmarked) card.classList.remove('bm-hidden');
        localStorage.setItem(key,JSON.stringify(state));
      }});
    }});
  }}

  if(document.readyState==='loading'){{
    document.addEventListener('DOMContentLoaded',function(){{
      setTimeout(function(){{initTopicFilter();initCardActions();}},160);
    }});
  }}else{{
    setTimeout(function(){{initTopicFilter();initCardActions();}},160);
  }}
}})();
</script>
"""
    html_f = html_f.replace('</style>', _p3_css + '</style>', 1)
    html_f = html_f.replace('<div id="bands">', _p3_topic_bar + '<div id="bands">', 1)
    html_f = html_f.replace('</body>', _p3_js + '</body>', 1)

    open(OUT_FEEDS, "w", encoding="utf-8").write(html_f)
    print(f"{OUT_FEEDS} {os.path.getsize(OUT_FEEDS)} bytes · LANG={LANG} · feeds {len(nl_bands)} · cards {_fc}")
