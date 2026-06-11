# W1 内部简报 · 北美 AI Engineer 现状×前瞻（真实数据）

> 数据采集时间：2026-05-19 ｜ 搜索词 "AI Engineer" ｜ 地区 United States
> 来源：JobSpy(LinkedIn 34 + Indeed 29，去重后 63 条，29 条含完整 JD) + fetch_metrics(GitHub/OSSInsight)
> 本简报为 W1 内部验证产物（先给自己看，不对外）

---

## 0. 最重要的 W1 发现（数据质量，必须正视）

搜 "AI Engineer" 抓回的 29 份带 JD 的岗位里，**只有 ~18 份是真 AI 核心/应用岗，~11 份是噪声**（DevSecOps、MES/.NET、数据中心设施电气工程师、S1000D 技术文档、Dynamics 365、招聘 sourcer……公司沾 AI 但岗位不是）。

→ **结论：关键词抓取必然带 ~38% 噪声；LLM 抽取/分类层不是可选项，是命门。** 正则数词频会把这 11 份噪声算进技能榜，得出错误结论。这条 W1 就验证了架构里"理解层必须用 LLM"的判断是对的。

---

## 1. 现状：北美 AI 岗真实技能需求（基于 18 份 AI 相关 JD，LLM 抽取）

**第一梯队（几乎必备）**
- **Python** — 绝对主力，AI 岗默认语言
- **AWS** — 云平台霸主；企业/政府岗也常要 **Azure**（Bedrock / Azure OpenAI / Entra）
- **LLM / 生成式 AI 应用** — 18 份里绝大多数明确要求"用 LLM 构建产品"
- **Docker / Kubernetes** — 部署标配
- **TypeScript / Node.js** — 全栈 AI 岗高频（前端 React/Next.js 次之）
- **SQL** — 数据/后端 AI 岗高频

**第二梯队（AI-native 差异化技能，正在成门槛）**
- **AI Agents / 智能体编排**（agentic systems、tool invocation、orchestration）— 高频且在涨
- **Prompt engineering** — 高频
- **Evals / 评测体系**（evaluation harnesses、eval datasets、regression testing、red team）— **显著高频，且是"高级岗"标志**
- **RAG（检索增强生成）** — 中高频
- **可观测性 / 监控（针对 AI 系统）** — 高频
- **MLOps / LLMOps、Terraform/IaC、CI/CD** — 中高频

**第三梯队（新兴信号，值得盯）**
- **把 AI 编码 agent（Claude Code / Cursor / Codex）当成"必备技能"写进 JD** — 出现在 Berkeley Lab(JGI)、Metriport 等岗，**这是个很新的信号**：会用 AI 写代码本身成了岗位要求
- **Token/成本可观测、Prompt injection/AI 安全、多模型供应商抽象（Anthropic/OpenAI/Google）** — 刚冒头
- **"Forward Deployed Engineer"（前置部署工程师）** 角色范式高频出现（Charta/Accenture）—— AI 落地催生的新岗型

**薪资快照**（23 条有薪资，样本小仅作方向）：北美 AI/SWE 岗主力区间 **$150k–270k/年**；Senior/Staff AI ≈ **$200k+**；企业/政府岗带宽极大（$63k–268k）。
**远程**：AI-native 创业公司明显偏**线下**（多家要求 NYC/SF 每周 5 天在岗），远程占比低于整体。

---

## 2. 前瞻：AI 开源方向动量（commit 活跃度代理）

> ⚠️ OSSInsight 今天故障（star 增速 HTTP 500 全失败），改用 **GitHub commit 活跃度** 作动量代理——其实是更硬的"在不在猛干"信号。

| 方向 | 代表仓 | ★ | commit/4周 | commit/52周 | 动量判断 |
|---|---|---:|---:|---:|---|
| **Serving 推理** | vllm | 80,418 | **796** | **10,151** | 🔥🔥🔥 全场最猛 |
| **Eval 评测** | deepeval | 15,541 | **254** | **4,437** | 🔥🔥🔥 体量小但猛 |
| MCP 协议 | modelcontextprotocol/servers | 85,899 | 8 | 1,454 | 🌟 star 最高(采纳广)，主仓已拆分 |
| Agent 编排 | langgraph | 32,377 | 93 | 1,420 | 🟢 活跃 |
| RAG | llama_index | 49,499 | 36 | 1,310 | 🟢 体量大、趋稳（成熟中） |
| 多模态 | LLaVA | 24,804 | **0** | **0** | 🔴 该代表仓已停摆（多模态创新已转移到 Qwen-VL 等，W2 需换代表） |

---

## 3. 🎯 交叉印证（护城河"现状×前瞻"在 W1 第一次跑出来）

这是 W1 最有价值的产出 —— 信号在两个独立来源同时出现，才算数：

| 信号 | 现状(招聘 JD) | 前瞻(开源动量) | 判定 |
|---|---|---|---|
| **Eval/评测** | 高频，且是高级岗标志 | deepeval 动量爆表 | ✅ **双源确认 = 正在硬化的新门槛**，最该让用户提前学 |
| **AI Agents/编排** | 高频且在涨 | langgraph 活跃 | ✅ 双源确认，已是主流要求 |
| **Serving/推理基建** | 仅在芯片/HPC 岗出现（窄） | vllm 全场最猛 | ⚠️ 前瞻领先于招聘——"学这个领先市场 6-12 月"的典型 |
| **AI 编码 agent 当必备技能** | 已进 JD（JGI/Metriport） | 开源动量代理未覆盖此维 | 🆕 单源新信号，**待 W3 的 HF/HN 源交叉验证**，先不下结论 |

> 这就是产品的核心价值雏形：能对用户说"Eval 现在招聘要、开源也在猛干 → 双确认，赶紧学；Serving 招聘还没普及但开源已爆 → 提前卡位"。**W1 证明这个机制能跑出真东西。**

---

## 4. W1 证明了什么 / 没证明什么

**证明了**：
- 端到端管道（采集 JobSpy + fetch_metrics → LLM 抽取 → 交叉印证简报）**真能跑通、能出真信号**
- 护城河"现状×前瞻交叉确认"不是 PPT，W1 就跑出了 Eval/Agent 两个双源确认结论
- LLM 抽取层是命门（38% 噪声证明正则会出错）

**没证明 / 下一步要补**：
- JobSpy 单次 OK，但**稳定性/反爬未验证**（W1 只跑一次没被封不代表能持续）
- LLM 抽取目前是我人工读 29 份做的，**未自动化、未做 schema 约束**（W2/W3）
- 前瞻只有"开源"一条腿，多模态代表仓停摆暴露"选代表仓"很脆 → W2 接 edgartools/博客补腿
- 噪声过滤需要产品化（自动判定"这岗是不是真 AI 岗"）

---

## 5. 数据局限

- 样本小：63 岗、29 份完整 JD、23 条有薪资——**方向性参考，非统计结论**
- OSSInsight star 增速今日全失败，前瞻用 commit 代理（已注明）
- "AI Engineer" 单关键词召回噪声 ~38%，技能榜已**人工剔除噪声岗**后统计
- LinkedIn 34 条多数无完整 JD（JobSpy 不深抓详情页），技能榜主要基于 Indeed 的 29 份有正文岗
- 薪资为 JD 自报区间，口径不一
