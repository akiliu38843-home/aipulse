"""build_site.py — 「直面就业」index.html 双语版（中/EN）。
用法: python3 build_site.py [zh|en]    默认 zh
输出: site/index.html (zh) 或 site/index-en.html (en)"""
import json, os, re, sys, sqlite3, statistics, collections

LANG = (sys.argv[1] if len(sys.argv)>1 else "zh").lower()
ZH = LANG == "zh"
def t(zh, en): return zh if ZH else en
OUT = "site/index.html" if ZH else "site/index-en.html"

def L(fp,d=None):
    try: return json.load(open(fp))
    except: return d if d is not None else {}
jw=L("data/jobs_w1.json",{}); blg=L("data/blogs_w2.json",{}); ex=L("data/w4_extra.json",{}); h1b=L("data/h1b_ai.json",{})
TPL="site/_news_design_template.html"
def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def clean(s,n=180):
    s=str(s or "").replace("\\-","-").replace("\\&","&").replace("\\.",".").replace("\\","")
    s=re.sub(r"[#*`>]+"," ",s); s=re.sub(r"\s+"," ",s).strip()
    return s[:n]+("…" if len(s)>n else "")
AI_TITLE=re.compile(r"(?i)(\bAI\b|\bML\b|\bLLM\b|Machine Learning|Data Scientist|Applied Scientist|Research Scientist|Data Engineer|MLOps|Generative|Forward Deployed|Prompt Engineer|AI[/\s-]?Native)")
BLOCK_T=re.compile(r"(?i)(DevSecOps|Apriso|Dynamics 365|S1000D|Technical Author|Sourcer|Recruiter|Account Executive|Head of (Business )?Operations|Facilities|Electrical Engineer|Software Engineering Internship|Cloud Platform Specialist)")
def keep(tit,b):
    tit=str(tit or ""); b=(str(b or "")).lower()
    if BLOCK_T.search(tit): return False
    if AI_TITLE.search(tit): return True
    return sum(1 for k in ("ai ","llm","machine learning","agent","generative","prompt","rag","embedding","fine-tun") if k in b)>=3

sal=[]; remote_n=0; cos=[]; ai_jobs=0; total=0
for j in (jw.get("jobs") or []):
    total+=1
    tit=str(j.get("title","")); brief=str(j.get("description",""))[:520]
    if not keep(tit,brief): continue
    ai_jobs+=1
    if str(j.get("is_remote")).lower() in ("true","1"): remote_n+=1
    co=str(j.get("company","")).strip()
    if co: cos.append(co)
    try:
        lo=float(j.get("min_amount") or 0); hi=float(j.get("max_amount") or 0)
        if lo>1000 and str(j.get("interval","")).startswith("year"): sal.append((lo+hi)/2)
    except: pass
sal_med=int(statistics.median(sal)) if sal else 0
rem_pct=int(remote_n*100/max(ai_jobs,1))
top_co=[c for c,_ in collections.Counter(cos).most_common(3)]

con=sqlite3.connect("data/signals.db")
fore=[(c,n) for c,n in con.execute(
 "SELECT canonical,n_src FROM ontology WHERE layer='foresight' ORDER BY n_src DESC").fetchall() if n>=2]
con.close()
FORE_EN_NAME={"AI Agents/编排":"AI Agents / Orchestration","Eval 评测":"Evals","RAG":"RAG","Serving 推理":"Serving / Inference",
 "多模态":"Multimodal","AI安全/Responsible AI":"AI Safety / Responsible AI","AI编码agent当硬技能":"AI coding agents as hard skill"}
def fen(x): return x if ZH else FORE_EN_NAME.get(x,x)

JD_TOP_ZH=["Python","AWS/Azure 云","LLM/生成式AI应用","Docker/Kubernetes","TypeScript/Node","SQL","AI Agents/编排","Eval 评测","RAG"]
JD_TOP_EN=["Python","AWS/Azure Cloud","LLM / GenAI Apps","Docker/Kubernetes","TypeScript/Node","SQL","AI Agents/Orchestration","Evals","RAG"]
JD_TOP=JD_TOP_ZH if ZH else JD_TOP_EN
FORE_NOTE_ZH={
 "AI Agents/编排":("已是硬门槛，4 源全确认","LangGraph/CrewAI 等编排框架；写得动多步骤工具调用的 agent"),
 "Eval 评测":("正在硬化的新门槛，3 源","deepeval/RAGAS 等；'我的 AI 准不准'的工程方法"),
 "RAG":("已主流化的检索增强","LlamaIndex/向量检索；把私有数据接进 LLM"),
 "Serving 推理":("前瞻领先招聘 6-12 月","vllm/SGLang 高吞吐推理；自托管上线 LLM"),
 "多模态":("HF trending 第一热","视觉+语言模型(VLM)；MiniCPM-V/Qwen-VL"),
 "AI安全/Responsible AI":("企业押注上升","prompt injection 防御 / 评测 / 红队"),
 "AI编码agent当硬技能":("W1单源→W2双源确认升级","Claude Code/Cursor/Codex 当生产工具用"),
}
FORE_NOTE_EN={
 "AI Agents/编排":("Hard bar already · 4-source confirmed","LangGraph / CrewAI; ship multi-step tool-using agents"),
 "Eval 评测":("New hard bar, 3-source","deepeval / RAGAS; 'is my AI correct?' as engineering"),
 "RAG":("Mainstreamed","LlamaIndex / vector retrieval; wire private data into LLMs"),
 "Serving 推理":("Foresight leads hiring 6–12 mo","vllm / SGLang; self-host LLMs at throughput"),
 "多模态":("HF trending #1","Vision-language models (VLM); MiniCPM-V / Qwen-VL"),
 "AI安全/Responsible AI":("Enterprise bets rising","Prompt injection defense / evals / red teaming"),
 "AI编码agent当硬技能":("W1 single→W2 double-source upgrade","Claude Code / Cursor / Codex as production tools"),
}
FORE_NOTE=FORE_NOTE_ZH if ZH else FORE_NOTE_EN
f3=t("北美 AI 岗门槛正从'会调 LLM API'上移到'会编排 Agent + 会做 Eval + 会用 AI 编码 agent 干活'；多模态采纳最猛；Serving 是领先招聘 6–12 月的卡位点。",
     "The NA AI hiring bar is moving from 'calling an LLM API' to 'orchestrating Agents + doing Evals + using AI coding agents at work'; multimodal adoption leads; Serving is the 6–12 month leading-indicator role.")
CHK=([
 "AI编码agent 在 jobs 频次是否升","Serving 是否从 jobs 未普及→出现","多模态 HF 占比是否保持"] if ZH else [
 "Does AI-coding-agent freq rise in jobs?",'Does Serving move from "not-yet-in-jobs" to "present"?',"Does multimodal share on HF hold?"])

# Personas
NEED_F=[c for c,n in fore if n>=2]
NEED_B_ZH=["Python","SQL","Docker/Kubernetes","AWS/Azure 云","LLM/生成式AI应用"]
NEED_B_EN=["Python","SQL","Docker/Kubernetes","AWS/Azure Cloud","LLM / GenAI Apps"]
NEED_B=NEED_B_ZH if ZH else NEED_B_EN
PERSONAS_ZH=[
 {"id":"p1","name":"转行后端工程师","desc":"有 Python/AWS/Docker，没碰过 AI 应用","has":["Python","AWS/Azure 云","Docker/Kubernetes","SQL"]},
 {"id":"p2","name":"应届 CS 毕业生","desc":"学过 Python/算法，无工程与 AI 经验","has":["Python"]},
 {"id":"p3","name":"非技术产品经理转 AI PM","desc":"懂产品不写代码","has":[]},
]
PERSONAS_EN=[
 {"id":"p1","name":"Backend engineer pivoting in","desc":"Has Python/AWS/Docker, no AI app experience","has":["Python","AWS/Azure Cloud","Docker/Kubernetes","SQL"]},
 {"id":"p2","name":"New-grad CS","desc":"Took Python/algos, no eng or AI experience","has":["Python"]},
 {"id":"p3","name":"Non-tech PM pivoting to AI PM","desc":"Knows product, doesn't code","has":[]},
]
PERSONAS=PERSONAS_ZH if ZH else PERSONAS_EN
# normalize 'has' values to current-lang baseline labels for matching (zh has vs en label)
HAS_MAP={"AWS/Azure 云":"AWS/Azure Cloud","LLM/生成式AI应用":"LLM / GenAI Apps"}
for p in PERSONAS:
    if not ZH:
        p["has"]=[HAS_MAP.get(x,x) for x in p["has"]]
    has=set(p["has"])
    p["base_gap"]=[b for b in NEED_B if b not in has]
    p["fore_gap"]=[fen(x) for x in NEED_F if x not in has]
    plan=[(t("基线","Baseline"),b) for b in p["base_gap"][:3]]+[(t("前瞻","Foresight"),x) for x in p["fore_gap"][:5]]
    p["learn"]=[f'{k}：{v}' if ZH else f'{k}: {v}' for k,v in plan[:6]]

# P2.1 个性化表单卡片（真 LLM 后端 /api/personalize）
target_role_opts="".join(f'<option>{esc(r)}</option>' for r in ["AI Engineer","ML Engineer","Machine Learning Engineer","Data Scientist","Applied Scientist","Research Scientist","Data Engineer","Forward Deployed AI Engineer","AI/ML Engineer","Applied AI Engineer","AI Native Engineer","Prompt Engineer","AI Solutions Architect","AI Product Manager","MLOps Engineer"])
INP_STYLE="padding:9px 11px;font-size:13.5px;background:var(--paper);border:1px solid var(--line-2);border-radius:6px;color:var(--ink);font-family:var(--sans);width:100%;box-sizing:border-box;margin-top:6px"
personalize_card={"soft":True,"custom":(
   f'<div class="hl">{t("个性化学习路径","Personal Learning Path")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("LLM × 真实北美 JD 数据 → 你的差距 + 学习顺序","LLM × real NA JD data → your gap + learn order")}</div>'
   f'<form id="p-form" onclick="event.stopPropagation()" onsubmit="return false" style="display:flex;flex-direction:column;gap:8px;margin-top:6px">'
   f'<label style="font-size:11px;color:var(--mut);letter-spacing:.04em;text-transform:uppercase;margin-top:4px">{t("你的现技能 / 背景","Your current skills / background")}'
   f'<textarea id="p-skills" rows="2" placeholder="{t("例: Python, AWS, Docker, FastAPI; 5 年后端经验","e.g.: Python, AWS, Docker, FastAPI; 5 yrs backend exp.")}" style="{INP_STYLE}"></textarea></label>'
   f'<label style="font-size:11px;color:var(--mut);letter-spacing:.04em;text-transform:uppercase">{t("目标岗位","Target role")}'
   f'<select id="p-target" style="{INP_STYLE}">{target_role_opts}</select></label>'
   f'<label style="font-size:11px;color:var(--mut);letter-spacing:.04em;text-transform:uppercase">{t("经验年限","Years of experience")}'
   f'<input id="p-years" type="number" min="0" max="40" placeholder="0" style="{INP_STYLE}"></label>'
   f'<details style="margin-top:2px"><summary style="font-size:11px;color:var(--mut);cursor:pointer;letter-spacing:.04em;text-transform:uppercase">{t("（可选）贴简历正文","(optional) paste résumé text")}</summary>'
   f'<textarea id="p-resume" rows="3" placeholder="{t("4000 字以内","up to 4000 chars")}" style="{INP_STYLE};margin-top:6px"></textarea></details>'
   f'<button id="p-submit" type="button" style="margin-top:8px;padding:10px 16px;background:var(--acc);color:#fff;border:none;border-radius:6px;font-weight:600;font-size:13.5px;cursor:pointer;font-family:var(--sans);letter-spacing:.02em">{t("生成我的学习路径 →","Generate my path →")}</button>'
   f'</form>'
   f'<div id="p-out" style="margin-top:14px;font-size:13.5px;color:var(--body);line-height:1.55;display:none"></div>'),
   "more":[[t("数据","Data"),t("北美 JD 真实抓取 + 前瞻交叉印证","real NA JDs + cross-confirmed foresight")],
           [t("模型","Model"),"gpt-5.4-mini (uyilink)"],
           [t("耗时","Latency"),t("约 5-15 秒","~5-15s")]]}
fixed_p_cards=[]
for p in PERSONAS:
    fixed_p_cards.append({"soft":True,"custom":(
      f'<div class="hl">{esc(p["name"])}</div>'
      f'<div class="mt"><span class="pip"></span>{esc(p["desc"])}</div>'
      f'<div class="dg" style="-webkit-line-clamp:unset;display:block">'
      f'<b>{t("基线缺口","Baseline gap")}:</b> { "/".join(esc(x) for x in p["base_gap"]) or t("无","none") }<br>'
      f'<b>{t("前瞻缺口","Foresight gap")}:</b> { "/".join(esc(x) for x in p["fore_gap"][:5]) or t("无","none") }</div>'
      f'<div class="ft">{t("已有","Has")}: { "、".join(esc(x) for x in p["has"]) or "—" }</div>'),
      "more":([[t(f'建议第 1 步',"Step 1"),esc(p["learn"][0])]]+
              [[t(f'建议第 {i+1} 步',f"Step {i+1}"),esc(p["learn"][i])] for i in range(1,min(5,len(p["learn"])))])
              if p["learn"] else []})

status_cards=[
 {"soft":True,"stat":True,"custom":(
   f'<div class="hl">{t("年薪中位","Median Salary")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("北美 AI 岗","NA AI roles")}</div>'
   f'<div class="stat-big">${sal_med:,}</div>'
   f'<div class="stat-sub">{t("来自","From")} {len(sal)} {t("条 JD 自报","self-reported JDs")}</div>'
   f'<div class="axis-bar"><i style="left:14%;width:62%"></i><b style="left:50%"></b></div>'
   f'<div class="axis"><span>${int(min(sal)/1000) if sal else 90}k</span><span>{t("中位","median")}</span><span>${int(max(sal)/1000) if sal else 300}k</span></div>'),
  "more":[[t("中位","Median"),f"${sal_med:,}"],[t("样本","Sample"),f"n={len(sal)}"],
          [t("实测范围","Observed range"),f"${int(min(sal)/1000) if sal else 90}k–${int(max(sal)/1000) if sal else 300}k"]]},
 {"soft":True,"custom":(
   f'<div class="hl">{t("JD 高频技能","Top JD Skills")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("简历该往这些词靠","Align résumé to these")}</div>'
   f'<div class="weighted" style="margin-top:14px">'+
   "".join(f'<span style="font-size:{34-i*3 if i<6 else 14}px"{" class=dim" if i>=4 else ""}>{esc(s)}</span>' for i,s in enumerate(JD_TOP[:6]))+
   f'</div>'),
  "more":[[t("来源","Source"),t("W1 LLM 抽取 (29 份 JD)","W1 LLM extraction (29 JDs)")],
          [t("层级","Tier"),t("按需求强度排序","Ordered by demand intensity")]]},
 {"soft":True,"custom":(
   f'<div class="hl">{t("远程占比","Remote Share")}</div>'
   f'<div class="mt"><span class="pip"></span>{ai_jobs} {t("个 AI 相关岗中","AI-relevant roles")}</div>'
   f'<div class="stat-big">{rem_pct}%</div>'
   f'<div class="stat-sub">{remote_n} {t("个标 Remote","marked Remote")}</div>'),
  "more":[[t("远程数","Remote count"),f"{remote_n} / {ai_jobs}"],[t("占比","Share"),f"{rem_pct}%"]]},
 {"soft":True,"custom":(
   f'<div class="hl">{t("发岗大户","Top Hirers")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("本期前 3","Top 3 this issue")}</div>'
   f'<div class="dg" style="-webkit-line-clamp:unset;display:block;font-size:14.5px;line-height:1.7;margin-top:6px">'+
   "<br>".join(f'· {esc(c)}' for c in top_co) +'</div>'),
  "more":[[f"#{i+1}",esc(c)] for i,c in enumerate(top_co)]},
]

PAL=["#CC3B1B","#1F6F4A","#2A6FDB","#5B3FB8","#9A6B1F","#0F1419","#C15F3C"]
fore_cards=[]
for i,(c,n) in enumerate(fore):
    why,how=FORE_NOTE.get(c,(t("≥2源交叉确认","≥2-source confirmed"),t("见 W1-W4 简报","See W1-W4 briefs")))
    fore_cards.append({"kind":"co","accent":PAL[i%len(PAL)],"hl":esc(fen(c)),
       "mt":t(f'{n} 源确认',f'{n}-source confirmed'),"dg":esc(f'{why} · {how}'),
       "more":[[t("确认源数","Sources"),f"{n} / 4"],[t("性质","Nature"),esc(why)],[t("怎么入门","How to start"),esc(how)]]})

pred_cards=[{"soft":True,"custom":(
   f'<div class="hl">{t("F-3 预测（首期，已写可证伪留痕）","F-3 Prediction (Issue 1, falsifiable trace logged)")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("2026-08 回看检验","Aug 2026 retro check")}</div>'
   f'<div class="dg" style="-webkit-line-clamp:unset;display:block">{esc(f3)}</div>'
   f'<div class="ft">{t("见 research/11-F3-prediction.md","See research/11-F3-prediction.md")}</div>'),
   "more":[[t("首发","Issued"),"2026-05-19"],[t("回看","Retro"),"2026-08"],
           [t("纪律","Discipline"),t("错了认账不补丁","Admit wrong; no patching")]]}]
for c in CHK:
    pred_cards.append({"subj":{"label":t("检验点","Check"),"color":"#CC3B1B"},
       "hl":esc(c),"mt":t("2026-08 可比","Aug 2026 comparable"),
       "dg":t("3 个月后重跑同样采集 → 是/否","Rerun same scrape in 3 mo → yes/no"),
       "more":[[t("检验日","Check date"),"Aug 2026"],
               [t("反向","If reverse"),t("记 FAIL，不补丁掩盖","Log FAIL, no cover-up")]]})

if h1b and h1b.get("top_sponsors"):
    tops=h1b["top_sponsors"][:6]
    summ=h1b.get("summary",{})
    top_list_html="".join(
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--line);font-size:13px">'
        f'<span style="color:var(--ink);font-weight:500">{esc(s["name"][:32])}</span>'
        f'<span style="font-family:var(--serif);color:var(--acc);font-weight:600">{s["initial_3y"]}</span></div>'
        for s in tops)
    visa_card={"soft":True,"custom":(
       f'<div class="hl">{t("H-1B Sponsor 榜","H-1B Sponsor Leaderboard")}</div>'
       f'<div class="mt"><span class="pip"></span>{t("USCIS · 3 年新批合计","USCIS · 3-yr initial approvals")}</div>'
       f'<div style="margin-top:8px">{top_list_html}</div>'
       f'<div class="ft">{summ.get("n_ai_employers_3y","?")} {t("家 AI 雇主 · 想去北美的看这个谁能办","AI employers · check who sponsors")}</div>'),
       "more":[[s["name"],f'{s["initial_3y"]} ({s["state_top"]})'] for s in tops[:5]]}
else:
    visa_card={"soft":True,"custom":(
       f'<div class="hl">{t("北美签证 / H-1B","NA Visa / H-1B")}</div>'
       f'<div class="mt"><span class="pip"></span>{t("数据待抓","data pending")}</div>'
       '<div class="editors-note"><span class="tk">TK</span>'
       f'<span class="body">{t("fetch_h1b.py 未跑","fetch_h1b.py not run")}</span></div>'),
       "more":[[t("状态","Status"),t("数据未生成","data not generated")]]}
val_card={"soft":True,"custom":(
   f'<div class="hl">{t("真人验证（W4 决策门，需用户自跑）","Real-user validation (W4 gate, requires you to run)")}</div>'
   f'<div class="mt"><span class="pip"></span>{t("5 真人 × 3 问","5 humans × 3 questions")}</div>'
   '<div class="dg" style="-webkit-line-clamp:unset;display:block">'
   +t("协议在 research/13-validation-protocol.md。AI 不能替跑——这是产品「值不值得继续投入」的第一道生死门。",
      "Protocol at research/13-validation-protocol.md. AI cannot run this for you — it is the first life-or-death gate for whether this product warrants further investment.")+
   '</div>'
   f'<div class="ft">{t("问 ①周频复访 ②前瞻可信 ③愿付费","Ask ①weekly revisit ②foresight trustable ③willingness-to-pay")}</div>'),
   "more":[[t("协议","Protocol"),"research/13-validation-protocol.md"],
           [t("人数","People"),"5 × 1 persona each"],
           [t("判定","Decision"),t("Q1+Q2 双成立→进 P2 辅导端","Q1+Q2 both pass → ship P2 coaching layer")]]}

BANDS=[
 {"id":"b1","n":"01","k":t("你的差距分析","Your Gap"),"pp":t("贴你的技能背景，LLM 算你的差距","Paste your skills, LLM computes your gap"),"cnt":t("个性化 · 真 LLM","Personalized · real LLM"),"cards":[personalize_card]+fixed_p_cards},
 {"id":"b2","n":"02","k":t("北美 AI 现状水位","NA AI Now"),"pp":t("市场在哪、你要追到哪","Where the market is — what to chase"),"cnt":t(f"{ai_jobs} AI 岗",f"{ai_jobs} AI roles"),"cards":status_cards},
 {"id":"b3","n":"03","k":t("该提前学什么","What to Learn Next"),"pp":t("≥2 源交叉印证的前瞻信号","Foresight signals cross-confirmed ≥2 sources"),"cnt":t(f"{len(fore)} 个信号",f"{len(fore)} signals"),"cards":fore_cards},
 {"id":"b4","n":"04","k":t("可证伪预测","Falsifiable Predictions"),"pp":t("留痕 + 2026-08 回看","Logged · Aug 2026 retro"),"cnt":t("F-3 首期","F-3 Issue 1"),"cards":pred_cards},
 {"id":"b5","n":"05","k":t("签证 & 真人验证","Visa & Validation"),"pp":t("北美落地 + 决策门","NA landing + decision gate"),"cnt":"","cards":[visa_card,val_card]},
]

fore_top=", ".join(fen(c) for c,_ in fore[:4])
DIGESTS={
 "b1": t(
  f"贴你的<em>现技能</em> + <em>目标岗</em> + <em>年限</em> → LLM (gpt-5.4-mini) 在真实北美 JD 数据上算：<br>"
  f"<b>fit score</b>（0-100）、<b>基线缺口</b>、<b>前瞻缺口</b>（={esc(fore_top)} 等 ≥2 源信号）、<br>"
  f"<b>建议学习顺序</b>（带免费资源）、<b>头 3 周具体行动</b>、<b>现实检查</b>。<br>"
  f"耗时约 5-15 秒。下面 3 个样例 persona 是<em>静态展示</em>，让你看看输出长啥样。",
  f"Paste your <em>current skills</em> + <em>target role</em> + <em>years</em> → LLM (gpt-5.4-mini) computes against real NA JD data:<br>"
  f"<b>fit score</b> (0-100), <b>baseline gap</b>, <b>foresight gap</b> (={esc(fore_top)} ≥2-source signals),<br>"
  f"<b>learn order</b> (with free resources), <b>concrete 3-week actions</b>, <b>reality check</b>.<br>"
  f"~5-15s. The 3 sample personas below are <em>static examples</em> so you know what to expect."),
 "b2": t(
  f"<b>{ai_jobs}</b> 个 AI 相关岗（已滤噪声）。<br>年薪中位 <em>${sal_med//1000}k</em>，实测 <b>${int(min(sal)/1000) if sal else 90}–{int(max(sal)/1000) if sal else 300}k</b>。<br>远程占比 <b>{rem_pct}%</b>。<br>发岗大户：{ '、'.join(top_co) }。",
  f"<b>{ai_jobs}</b> AI-relevant roles (noise filtered).<br>Median salary <em>${sal_med//1000}k</em>; observed <b>${int(min(sal)/1000) if sal else 90}–{int(max(sal)/1000) if sal else 300}k</b>.<br>Remote share <b>{rem_pct}%</b>.<br>Top hirers: { ', '.join(top_co) }."),
 "b3": t(
  f"<b>{len(fore)}</b> 个 ≥2 源交叉确认的前瞻信号（不靠单源吹）。<br>每张卡告诉你<em>是什么</em>+<em>怎么入门</em>。<br>排序按命中源数：4源(全确认)→3源(强)→2源(双源)。",
  f"<b>{len(fore)}</b> ≥2-source confirmed foresight signals (no single-source hype).<br>Each card explains <em>what it is</em> + <em>how to start</em>.<br>Sorted by source count: 4 (all) → 3 (strong) → 2 (dual)."),
 "b4": t(
  "产品与 AI newsletter 的本质区别：<br><b>有留痕、能回看、错了认账</b>。<br>F-3 首期预测+3 个 2026-08 检验点已写入留痕快照。",
  "What separates this from an AI newsletter:<br><b>Traceable, reviewable, admits when wrong</b>.<br>F-3 Issue 1 prediction + 3 Aug-2026 checks already written to falsifiable trace."),
 "b5": t(
  "<b>签证</b>占位 (DOL 薪资 403 被挡)，列专项。<br><b>真人验证</b>是 W4 决策门——AI 不能替跑，需你拿协议找 5 个人跑 3 问。",
  "<b>Visa</b> placeholder (DOL salary 403 blocked) — deferred.<br><b>Real-user validation</b> is the W4 gate — AI cannot run this; bring the protocol to 5 humans × 3 questions."),
}
for b in BANDS: b["digest"]=DIGESTS.get(b["id"],"")

# ── 注入模板 ──
def sub1(p,r,s): return re.sub(p,lambda m:r,s,count=1,flags=re.S)
html=open(TPL,encoding="utf-8").read()

# Tabs + lang slots（直面就业 on）
tab_slot=(f'<a class="on" href="{OUT.split("/")[-1]}">{t("直面就业","Compass")}</a>\n'
          f'      <a href="{("news.html" if ZH else "news-en.html")}">{t("看新闻","News")}</a>')
lang_slot=('<div class="lang">'
           f'<a class="{("on" if ZH else "")}" href="index.html">中</a>'
           f'<a class="{("on" if not ZH else "")}" href="index-en.html">EN</a>'
           '</div>')
html=html.replace("<!--LANG_SLOT-->", lang_slot).replace("<!--TAB_SLOT-->", tab_slot)

# Title
html=html.replace("<title>NorthStar — 北美 AI 简讯（设计样张）</title>",
                  t("<title>NorthStar — 直面就业</title>","<title>NorthStar — Career Compass</title>"))

# issueline
iss=('<div class="issueline-inner">'+
 t(f'<span class="iss-no">直面就业</span><span class="dot">·</span><span>数据截至 2026-05-19</span><span class="dot">·</span><span>个性化差距分析 + 真实薪资 + 前瞻信号</span><span class="dot">·</span><span>{ai_jobs} AI 岗 / ${sal_med//1000}k 中位</span>',
   f'<span class="iss-no">Career Compass</span><span class="dot">·</span><span>Data as of 2026-05-19</span><span class="dot">·</span><span>Personal gap analysis + real salaries + foresight</span><span class="dot">·</span><span>{ai_jobs} AI roles / ${sal_med//1000}k median</span>')+
 '</div>')
html=sub1(r'<div class="issueline-inner">.*?</div>', iss, html)

# Hero
hero=(
 '<section class="hero" data-screen-label="Hero">'
 '<div class="hero-grid">'
 '<div class="hero-main">'
 f'<div class="hk">{t("就业 / Your Compass","Career / Your Compass")}</div>'
 f'<p class="lede">{t("想进 AI 行业？这页用真实北美招聘数据告诉你现在该学什么、避哪些坑——和右侧「看新闻」用的是同一份 signals.db。","Want into AI? This page uses real NA hiring data to show what to learn and what to avoid — same signals.db as the News view.")}</p>'
 f'<div class="byline"><span class="rule"></span><b>{t("By NorthStar 编辑部","By NorthStar Editors")}</b> · 2026-05-19</div>'
 '<ol class="tldr">'
 +t(
  '<li>选一个 <em>persona</em>，下方实时算出你的<em>基线缺口</em>+<em>前瞻缺口</em></li>'
  f'<li>北美 AI 岗薪资中位 <em>${sal_med//1000}k</em>，<em>{ai_jobs}</em> 个真实岗</li>'
  '<li>前瞻按 <em>≥2 源交叉确认</em>排序，单源不下结论，错了 2026-08 认账</li>',
  '<li>Pick a <em>persona</em> — see your <em>baseline gap</em> + <em>foresight gap</em> live</li>'
  f'<li>Median NA AI salary <em>${sal_med//1000}k</em>, across <em>{ai_jobs}</em> real roles</li>'
  '<li>Foresight signals sorted by <em>≥2-source cross-confirmation</em>; single-source never decides; if wrong, we own it Aug 2026</li>')+
 '</ol>'
 '<div class="kpi-row" aria-label="">'
 '<div class="kpi-cell" style="grid-column:1/-1;border-right:none;padding-left:0">'
 f'<div class="kpi-lbl">{t("本周变化","Week-over-week")}</div>'
 f'<div class="kpi-val down"><span style="font-family:var(--serif);font-size:20px">{t("首期 · 无环比基线","First issue · no baseline")}</span></div>'
 f'<div class="kpi-sub">{t("单期快照，无 vs 上周；2026-08 首次可比（同 F-3 检验点）","Snapshot only · first comparable in Aug 2026 (same as F-3 checks)")}</div></div></div>'
 '<div class="evidence"><div>'
 f'<div class="ev-label">{t("前瞻","Foresight")} <em>cross-evidence ≥2 sources</em></div>'
 '<div class="ev-tags">'+
 "".join(f'<span>{esc(fen(c))}<sub>{n}</sub></span>' for c,n in fore)+
 '</div></div>'
 f'<div><div class="ev-label">{t("可证伪预测","Falsifiable predictions")} <em>due {t("2026-08","Aug 2026")}</em></div>'
 '<ul class="ev-preds">'+
 "".join(f'<li>{esc(c)}</li>' for c in CHK)+
 '</ul></div></div>'
 '</div>'
 '<aside class="hero-stat">'
 f'<div class="stat-label">{t("本期样本","This issue sample")}</div>'
 '<div class="stat-grid">'
 f'<div><b>{ai_jobs}</b><span>{t("AI 岗（已滤）","AI roles (filtered)")}</span></div>'
 f'<div><b>{len(PERSONAS)}</b><span>{t("样例 persona","sample personas")}</span></div>'
 f'<div><b>{len(fore)}</b><span>{t("≥2源信号","≥2-src signals")}</span></div>'
 f'<div><b>${sal_med//1000}k</b><span>{t("年薪中位","median salary")}</span></div>'
 '</div></aside>'
 '</div></section>')
html=sub1(r'<section class="hero".*?</section>',hero,html)

# bands
bands_js="const bands = "+json.dumps(BANDS,ensure_ascii=False)+";"
html=sub1(r"const bands = \[.*?\n\];",bands_js,html)

# sidenav
sn='<nav class="sidenav" aria-label="Sections">'+"".join(
 f'<a href="#{b["id"]}" data-anchor="{b["id"]}"><span class="pip"></span><span class="lbl">{b["n"]} {esc(b["k"])}</span></a>'
 for b in BANDS)+'</nav>'
html=sub1(r'<nav class="sidenav".*?</nav>',sn,html)

# TOC head
html=html.replace('本期目录<em>/ Inside this issue</em>',
                  t('本期目录<em>/ Inside this issue</em>','Contents <em>/ Inside this issue</em>'))
html=html.replace('8 SECTIONS · ~22 CARDS · 5 MIN READ',
                  t(f'{len(BANDS)} 栏目 · ~{sum(len(b["cards"]) for b in BANDS)} 卡片 · 5 分钟',f'{len(BANDS)} SECTIONS · ~{sum(len(b["cards"]) for b in BANDS)} CARDS · 5 MIN READ'))

# 本栏要点 kicker
html=html.replace('<span class="lede-kick">本栏要点</span>',
                  f'<span class="lede-kick">{t("本栏要点","Section TL;DR")}</span>')

# Footer
foot=t(
 '<div class="rule"><b>直面就业 · 工具型</b> · 数据同源 signals.db · v2 editorial</div>'
 '个性化差距分析为 3 个样例 persona（无真实简历，需用户自行匹配） · '
 '签证视图诚实占位（DOL 薪资 403 被挡） · '
 '真人验证（W4 决策门）需用户自跑 5 真人 × 3 问，AI 不能替 · '
 '字体 Google Fonts CDN，离线回退本地衬线',
 '<div class="rule"><b>Career Compass · Tool</b> · same signals.db · v2 editorial</div>'
 '3 sample personas (no real résumé — readers must self-match). '
 'Visa view is an honest placeholder (DOL salary 403 blocked). '
 'Real-user validation (W4 gate) requires you to run 5 humans × 3 questions — AI cannot. '
 'Fonts via Google Fonts CDN with local-serif fallback.')
html=sub1(r'<footer>.*?</footer>', f'<footer>{foot}</footer>', html)

# P2.1 表单提交 JS（调 /api/personalize 真 LLM 后端）
L_FIT=t("匹配度","Fit score"); L_BG=t("基线缺口","Baseline gap"); L_FG=t("前瞻缺口","Foresight gap")
L_LEARN=t("建议学习顺序","Suggested learn order"); L_NEXT3=t("头 3 周具体行动","Next 3 weeks · concrete actions")
L_REALITY=t("⚠️ 现实检查","⚠️ Reality check"); L_LOADING=t("生成中…（约 5-15 秒）","Generating… (~5-15s)")
L_BTN=t("生成我的学习路径 →","Generate my path →"); L_ERR=t("出错了","Error")
L_NONE=t("无","none"); L_RESOURCE=t("资源","Resource"); L_META=t("模型","Model")
personalize_js=("<script>\n"
 "document.addEventListener('click', async (ev) => {\n"
 "  if (ev.target.id !== 'p-submit') return;\n"
 "  ev.preventDefault(); ev.stopPropagation();\n"
 "  const btn = ev.target;\n"
 "  const skills = (document.getElementById('p-skills').value||'').trim();\n"
 "  const target_role = document.getElementById('p-target').value;\n"
 "  const years = parseInt(document.getElementById('p-years').value)||0;\n"
 "  const resume = (document.getElementById('p-resume').value||'').trim();\n"
 "  const out = document.getElementById('p-out');\n"
 "  if (!skills && !resume) { out.style.display='block'; out.innerHTML='<span class=\"warn\">"+t('请至少填技能或贴简历','Please fill in skills or paste a resume')+"</span>'; return; }\n"
 f"  const old = btn.textContent; btn.disabled = true; btn.textContent = '{L_LOADING}';\n"
 "  out.style.display='block'; out.innerHTML='<span style=\"color:var(--mut)\">"+L_LOADING+"</span>';\n"
 "  try {\n"
 "    const r = await fetch('/api/personalize', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({skills, target_role, years, resume})});\n"
 "    const data = await r.json();\n"
 "    if (!r.ok || !data.result) throw new Error((data&&data.error)||('HTTP '+r.status));\n"
 "    renderResult(data.result, data.meta);\n"
 "  } catch (e) {\n"
 f"    out.innerHTML = '<span class=\"warn\">{L_ERR}: '+e.message+'</span>';\n"
 "  } finally { btn.disabled = false; btn.textContent = old; }\n"
 "});\n"
 "function renderResult(r, meta) {\n"
 "  const out = document.getElementById('p-out');\n"
 "  const tags = (a) => (a||[]).map(x=>`<span class=\"tg\" style=\"margin-right:3px\">${x}</span>`).join('')||'"+L_NONE+"';\n"
 "  out.innerHTML = `\n"
 f"    <div style=\"display:flex;align-items:baseline;gap:10px;margin-bottom:10px\"><span style=\"font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)\">{L_FIT}</span><span style=\"font-family:var(--serif);font-size:28px;font-weight:600;color:var(--ink)\">${{r.fit_score}}</span><span style=\"font-size:12px;color:var(--mut)\">/100</span></div>\n"
 f"    <div style=\"margin:8px 0\"><b>{L_BG}:</b> ${{tags(r.baseline_gap)}}</div>\n"
 f"    <div style=\"margin:8px 0\"><b>{L_FG}:</b> ${{tags(r.foresight_gap)}}</div>\n"
 f"    <div style=\"margin-top:12px;padding-top:10px;border-top:1px dashed var(--line)\"><div style=\"font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin-bottom:8px\">{L_LEARN}</div>\n"
 "    <ol style=\"margin:0;padding-left:18px\">${(r.learn_order||[]).map(x=>`<li style=\"margin:6px 0\"><b>${x.skill}</b> — ${x.why}<br><span style=\"font-size:12px;color:var(--mut)\">"+L_RESOURCE+": ${x.resource_hint}</span></li>`).join('')}</ol></div>\n"
 f"    <div style=\"margin-top:12px;padding-top:10px;border-top:1px dashed var(--line)\"><div style=\"font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin-bottom:6px\">{L_NEXT3}</div>\n"
 "    <ol style=\"margin:0;padding-left:18px\">${(r.next_3_actions||[]).map(x=>`<li style=\"margin:5px 0\">${x}</li>`).join('')}</ol></div>\n"
 f"    <div style=\"margin-top:12px;padding:10px 12px;background:rgba(154,107,31,.08);border-left:2px solid var(--gold);font-size:12.5px;color:var(--ink-2);line-height:1.55\">{L_REALITY}: ${{r.reality_check}}</div>\n"
 f"    <div style=\"margin-top:10px;font-family:var(--mono);font-size:10px;color:var(--mut-2);letter-spacing:.04em\">{L_META}: ${{meta.model}} · ${{meta.usage.total_tokens||'?'}}t · "+t('数据截至','data as of')+" ${{meta.data_as_of}}</div>`;\n"
 "}\n"
 "</script>")
html=html.replace("</body>", personalize_js+"\n</body>")

os.makedirs("site",exist_ok=True)
open(OUT,"w",encoding="utf-8").write(html)
print(f"{OUT} {os.path.getsize(OUT)} bytes · LANG={LANG} · bands {len(BANDS)} · cards {sum(len(b['cards']) for b in BANDS)}")
