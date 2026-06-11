# W3 内部简报 · 补源 + 主题本体 + F-3 预测跑通（真实数据）

> 采集时间：2026-05-19 ｜ W3 内部验证产物
> 数据底座：signals.db 现 6 源类型（jobs/oss/enterprise/blog/hf/hn）+ canonical 主题本体 + 6 份留痕快照

---

## 0. W3 干了什么（对照清单 + 诚实降级）

| 计划项 | 状态 | 说明 |
|---|---|---|
| 接 Hugging Face Hub | ✅ 完成 | trending 模型采纳曲线入库（修了 1.15 API 变更 + SOCKS 代理依赖） |
| 接 Hacker News | ✅ 完成 | 最新 Who-is-hiring 200 评论解析 + AI 热度 story |
| 多模态换代表仓 | ✅ 完成 | LLaVA(停滞)→MiniCPM-V；并确立"快变品类用 HF 采纳 > GitHub 单仓" |
| 主题归一本体（替代 O*NET） | ✅ 完成 | 解决 W2 头号硬伤：alias→canonical + baseline/foresight 分层 |
| F-3 预测合成 | ✅ 完成 | LLM 直接合成，≥2 源纪律，写可证伪留痕 |
| O*NET | 🔁 替换 | 用主题本体替代（更直接解决 W2 痛点；O*NET 需注册/重下载，ROI 低） |
| gpt-researcher 工具 | ⚠️ 降级 | 本环境无 LLM/搜索 API key → F-3 由 LLM 直接合成（产出形态一致），工具化待 key |
| H-1B 全量 | ⚠️ 仅探针+设计 | 见 §3，诚实未抓全 |

---

## 1. 🎯 交叉印证（6 源 + canonical 本体，W2→W3 升级对比）

| 主题 | W2 | **W3** | 变化 |
|---|---|---|---|
| AI Agents/编排 | 4源 | **4源**(jobs+oss+enterprise+blog) | 稳，硬门槛 |
| Eval 评测 | 3源 | **3源**(jobs+oss+blog) | 稳，强确认 |
| Serving 推理 | 3源 | **3源**(oss+enterprise+blog) | 稳，招聘仍未普及=领先点 |
| **多模态** | 🟡2源矛盾(LLaVA停滞) | **🟢3源**(enterprise+hf+oss) | ⬆️ **HF 采纳曲线修好了它**——从"弱/矛盾"升"强确认" |
| **RAG** | 2源 | **🟢3源**(jobs+oss+hn) | ⬆️ HN 补到 3 源 |
| AI编码agent当硬技能 | 2源 | **2源**(jobs+blog) | 稳，killer 信号持续 |
| AI安全/Responsible AI | 2源 | 2源 | 稳 |

**新方法论收获**：加一个对的源（HF 采纳）能把矛盾信号直接救成强确认——印证"源冗余"设计的价值；且 baseline 技能(Python/云/Docker…)被本体正确分离，不再误判为"弱信号"。

---

## 2. 🏆 F-3 预测产出（首份，已留痕可证伪）

一句话预测（12 个月）：
> **北美 AI 岗硬门槛从"会调 LLM API"上移到"会编排 Agent + 会做 Eval + 会用 AI 编码 agent 干活"；多模态采纳最猛；Serving 是领先招聘 6-12 月的卡位点。**

- 只用 ≥2 源信号；单源仅观察名单不下结论（纪律）
- **可证伪检验点已写死**（2026-08 回看）：①AI编码agent 在 jobs 频次是否升 ②Serving 是否从"jobs没普及"变"出现" ③多模态 HF 占比是否保持 —— 反向则记 FAIL 不补丁
- 全文：`F3-PREDICTION-2026-05-19.md`，已存 snapshots 表 → 与 AI newsletter 的本质区别 = **有留痕、能回看、错了认账**

---

## 3. H-1B 可行性探针（诚实结论）

| 源 | 探针 | 结论 |
|---|---|---|
| USCIS H-1B Employer Data Hub | **200 可达** | ✅ 官方最干净路径，CSV 导出（雇主+年份+NAICS+批准量） |
| DOL OFLC 绩效数据(含薪资 LCA) | **403 被挡** | ⚠️ 薪资级数据在此，被 bot 检测挡，需换 host/方式 |
| h1bdata.info | 301 可达 | ⚠️ 公开但抓取属灰色，合规存疑 |

**设计决定（诚实）**：H-1B **本轮只探针+设计，不全量抓**。原因：①USCIS Hub 给"哪些公司 sponsor + 量"但**没有岗位/薪资粒度**；②岗位+薪资在 DOL LCA(被挡且年度大文件)，是独立重活。→ 列为 **W4 后专项**，不在 W3 假装抓完。签证视图设计：先用 USCIS Hub 出"北美哪些 AI 公司 sponsor + 批准量趋势"，薪资维度待 LCA 专项。

---

## 4. 诚实点 / 还没解决

- 🚩 gpt-researcher 工具未真接（无 key）——F-3 是 LLM 直接合成，缺"自动多轮取证"
- 🚩 主题本体的 alias/layer 表仍是人工维护，规模化要半自动（LLM 辅助扩本体）
- 🚩 HN Who-is-hiring 这月偏通用 SWE（AI 专有词频低，仅 RAG≥3）——单月样本波动大，要多月累积才稳
- 🚩 LLM 抽取(我做的)仍未自动化、无 schema 校验
- 🚩 H-1B 薪资维度未拿到（DOL 被挡），签证视图本轮只有"公司+量"半成品设计

---

## 5. W3 证明了什么

- ✅ 6 源跑通，**加对的源能救矛盾信号**（多模态 2→3 源强确认）
- ✅ 主题本体解决 W2 头号硬伤，baseline/foresight 分层让结论可信
- ✅ **F-3 预测首次产出且可证伪留痕**——产品"与 newsletter 的本质区别"落地
- ✅ 诚实边界清晰：gpt-researcher/H-1B 降级都明说原因，没假装做完
- ⚠️ W4 重点：抽取自动化 + schema 校验 + 个性化层 + 真人验证 + 抓取健康监控

---

## 6. 数据局限

- 6 源但每源深度有限，方向性非统计结论
- HF trending=快照（采纳曲线趋势需多轮累积）；HN 单月波动大
- F-3 由 LLM 合成非 gpt-researcher 多轮取证（已注明）
- H-1B 仅探针，签证视图未实装
- 交叉印证依赖人工维护的 canonical 本体
