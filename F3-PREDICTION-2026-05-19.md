# F-3 预测 · 北美 AI-native 人才画像 · 2026-05-19

> 合成层产出（本轮由 LLM 直接合成；gpt-researcher 工具待 API key 接入）
> 规则：**只有 ≥2 源交叉确认的信号才进预测**；单源信号仅列观察名单不下结论
> 数据底座：signals.db（6 源类型：jobs/oss/enterprise/blog/hf/hn）+ canonical 主题本体
> 本预测已写入 snapshots 留痕表 → **3 个月后可回看检验对错（可证伪）**

---

## 1. 一句话预测（12 个月）

> **未来 12 个月，北美 AI 岗的"硬门槛"会从"会调 LLM API"上移到"会编排 Agent + 会做 Eval + 会用 AI 编码 agent 干活"；多模态(VLM)是采纳最猛的模型品类；Serving/推理工程是领先招聘 6–12 月的提前卡位点。**

---

## 2. 分层结论（每条标注几源confirmed + 来源）

### 🔴 现在就是硬门槛（4 源全确认，不会就出局）
- **AI Agents / 编排** — `jobs+oss+enterprise+blog` 全确认。已不是"新兴"，是默认要求。

### 🟢 正在硬化，最该提前学（3 源强确认）
- **Eval / 评测** — `jobs+oss+blog`。招聘里是高级岗标志，开源(deepeval)动量爆表。
- **多模态(VLM)** — `enterprise(META)+hf+oss`。**HF 采纳曲线第一热**（trending 30 个里 image-text-to-text 占 9）。
- **Serving / 推理工程** — `oss(vllm最猛)+enterprise(NVDA核心)+blog`。**注意：jobs 里还没普及** → 典型"前瞻领先招聘"，现在学＝领先市场。
- **RAG** — `jobs+oss+hn`。已主流化，属"现在就该会"。

### 🟢 新硬门槛（2 源确认，W1→W2→W3 持续被独立印证）
- **会用 AI 编码 agent（Claude Code / Cursor / Codex）** — `jobs+blog`。
  这是本产品**最有代表性的预测**：W1 仅 jobs 单源(标"待验")→ W2 blog 独立印证(OpenAI Codex 企业化)→ W3 持续。**留痕在库，可回看"我们早于普及就预测了"**。

### 🟡 上升中（2 源）
- **AI 安全 / Responsible AI** — `enterprise(MSFT)+jobs`。

### ⚪ 观察名单（单源·不下结论，等更多源印证）
- MCP 协议(oss) / MLOps-LLMOps(jobs) / AI系统可观测性·成本(jobs) / 开放权重微调LoRA(blog) / LLM架构MoE(blog,偏研究者非入行者必备)

### ⚙️ 基础技能（默认必备，不算"新该学"，别浪费篇幅教）
Python / SQL / TypeScript-Node / Docker-Kubernetes / AWS-Azure / Prompt engineering / 调 LLM API

---

## 3. 给"想入行的人"的可执行建议（产品要输出的东西）

| 优先级 | 学什么 | 为什么（几源confirmed） |
|---|---|---|
| P0 现在补 | Agent 编排 + RAG | 已是硬门槛(4源/3源) |
| P0 现在补 | **会用 Claude Code/Cursor/Codex 干真活** | 新硬门槛(2源,持续印证)，多数人还没当回事 |
| P1 提前学 | Eval/评测能力 | 高级岗分水岭(3源) |
| P1 卡位 | Serving/推理工程基础 | 招聘还没普及但全前瞻源在烧(领先6-12月) |
| P2 跟进 | 多模态(VLM)应用 | 采纳最猛(HF第一热) |
| 基础 | Python/云/Docker 等 | 默认必备，不是差异点 |

---

## 4. 可证伪检验点（3 个月后回看，2026-08 左右）

本预测对不对，到时这样验（快照已存，能比对）：
1. **AI编码agent**：3 个月后 jobs 源里"Claude Code/Cursor/Codex 当要求"的岗位频次是否上升？(预测：升)
2. **Serving**：是否从"jobs 没普及"变成"jobs 出现"？(预测：开始出现 = 我们领先判断对)
3. **多模态**：HF trending 里多模态占比是否仍 ≥ 头部？(预测：保持)
4. **若任一反向** → F-3 方法需回炉，记录 FAIL 根因，不补丁掩盖。

---

## 5. 诚实边界

- 样本仍小（6 源但每源深度有限），是**方向性预测非统计预言**
- gpt-researcher 工具未接（无 API key），本 F-3 由 LLM 直接合成——产出形态一致，但缺"自动多轮检索取证"，待 key 接入升级
- 单源信号一律未进结论（纪律），但也意味着可能漏掉"真前瞻但暂时只露头一次"的早信号——靠后续轮次多源补
- 预测的价值不在"猜得准"，在"**有留痕、可回看、错了认账**"——这是与 AI newsletter 的本质区别
