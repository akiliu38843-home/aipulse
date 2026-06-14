# AI★Pulse

> 中文世界的 AI 前沿信息站 — 把英文圈最好的 20+ 信源，每天「翻译 + 去重 + 排重要性」端到中文读者面前。

**Live →** [aipulse.renlab.ai](https://aipulse.renlab.ai)

---

## 它做什么

每天早上自动抓取 20+ 个 AI 信源，翻译成中文，构建成两个页面：

| 页面 | 内容 |
|---|---|
| **常规新闻**（`news.html`） | 9 个主题栏：头条 / 研究 / 工程 / 开源热榜 / 招聘 / 论文 / 播客… |
| **定制新闻**（`news-feeds.html`） | 按信源分栏，可独立折叠，适合深度订阅 |

---

## 信源覆盖

**RSS 类**（自动过滤 AI 相关）
- TLDR AI · Hacker News AI · The Batch (deeplearning.ai) · arXiv cs.AI
- OpenAI Blog · Google DeepMind · The Verge AI · TechCrunch AI
- Simon Willison · Ahead of AI · One Useful Thing · The Gradient
- 量子位 · Gradient Flow · 等共 15+ 个

**非 RSS 类**（定制爬取）
- HuggingFace Daily Papers（每日论文精选）
- GitHub Trending AI（当日 AI 仓库热榜，含中文描述翻译）

---

## 技术架构

```
fetch_newsletters.py   ← 每日抓取全部信源 → data/newsletters.json
        ↓                  + 调 DeepSeek API 翻译 GitHub 项目描述
build_news.py zh/en    ← 读 JSON → 注入模板 → site/news.html + news-feeds.html
        ↓
Vercel (静态托管)       ← GitHub Actions push → 自动触发重发
```

核心文件：

```
fetch_newsletters.py          每日数据拉取（RSS + HF + GitHub Trending + 价格）
build_news.py                 HTML 生成器（常规新闻 + 定制新闻）
build_site.py                 首页生成器
translate.py                  翻译缓存层（DeepSeek API）
site/_news_design_template.html  页面样式模板
scripts/run_daily.sh          本地定时任务脚本（launchd 调用）
.github/workflows/daily.yml   GitHub Actions 每日自动更新
```

---

## 本地运行

```bash
# 1. 克隆
git clone https://github.com/akiliu38843-home/aipulse.git
cd aipulse

# 2. 安装依赖（Python ≥ 3.10）
pip install -r requirements.txt

# 3. 设置 API Key（翻译用，可选，无 key 退回英文原文）
export DEEPSEEK_API_KEY=your_key_here

# 4. 抓取数据（走代理，或去掉 fetch_newsletters.py 里的 PROXIES 改直连）
python3 fetch_newsletters.py

# 5. 构建页面
python3 build_news.py zh

# 6. 打开
open site/news.html
```

> **代理说明**：`fetch_newsletters.py` 默认走 `http://127.0.0.1:7897`。  
> 无代理环境请把 `PROXIES = {...}` 改为 `PROXIES = {}` 或删除代理参数。

---

## 自动化

### GitHub Actions（云端，无需本地挂机）

每个工作日 09:30 北京时间自动跑，结果 push 触发 Vercel 重发。

需要在仓库 Settings → Secrets 里配置：
- `DEEPSEEK_API_KEY` — 翻译 GitHub Trending 描述（可选，无则跳过翻译）

### 本地 launchd（Mac，可选）

```bash
# 装定时任务（工作日 09:30 本机跑）
cp scripts/com.user.ainative.daily.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.ainative.daily.plist

# 手动触发测试
bash scripts/run_daily.sh

# 卸载
launchctl unload ~/Library/LaunchAgents/com.user.ainative.daily.plist
```

把 DeepSeek Key 存到 `~/.ainative_env`：
```
DEEPSEEK_API_KEY=sk-your_key_here
```

---

## 部署到 Vercel

项目根目录有 `vercel.json`，`outputDirectory` 指向 `site/`，直接 import 即可。

自定义域名：在 Vercel 项目设置里绑定，DNS 加 CNAME 指向 Vercel 的地址。

---

## 迭代路线

见 [`迭代路线-建设计划.md`](迭代路线-建设计划.md) — 记录了 P0–P5 每项功能的设计思路和验收标准。
