"""
扩展 RSS 源清单 - 从 14 个扩展到 50+ 个 AI 领域高质量信息源

使用方法：
1. 复制需要的源到 rss_w2.py 的 FEEDS 字典
2. 分批测试（先加 10 个，跑一次，确认没问题再加下一批）
3. 注意：某些源可能需要代理访问（已标注）

分类：
- 个人博客（AI 研究者/工程师）
- 实验室/机构
- AI 公司官方博客
- AI 新闻/媒体
- 开源项目博客
"""

# ===== 已有的 14 个源（保持不变）=====
FEEDS_CURRENT = {
 "Simon Willison":      "https://simonwillison.net/atom/everything/",
 "Lilian Weng":         "https://lilianweng.github.io/index.xml",
 "Sebastian Raschka":   "https://magazine.sebastianraschka.com/feed",
 "HuggingFace Blog":    "https://huggingface.co/blog/feed.xml",
 "Chip Huyen":          "https://huyenchip.com/feed.xml",
 "Eugene Yan":          "https://eugeneyan.com/rss/",
 "Jay Alammar":         "https://jalammar.github.io/feed.xml",
 "Berkeley BAIR":       "https://bair.berkeley.edu/blog/feed.xml",
 "The Gradient":        "https://thegradient.pub/rss/",
 "DeepLearning.AI Batch":"https://www.deeplearning.ai/the-batch/feed/",
 "OpenAI News":         "https://openai.com/news/rss.xml",
 "Google Research":     "https://research.google/blog/rss/",
 "Anthropic News":      "https://www.anthropic.com/rss.xml",
 "Sebastian Ruder":     "https://www.ruder.io/rss/",
}

# ===== 新增：个人博客（15 个）=====
FEEDS_PERSONAL_BLOGS = {
 "Andrej Karpathy":     "https://karpathy.github.io/feed.xml",
 "Distill.pub":         "https://distill.pub/rss.xml",
 "Christopher Olah":    "https://colah.github.io/rss.xml",
 "François Chollet":    "https://fchollet.com/feed/",  # Keras 作者
 "Jeremy Howard":       "https://www.fast.ai/atom.xml",  # fast.ai
 "Rachel Thomas":       "https://rachel.fast.ai/posts/index.xml",
 "Denny Britz":         "http://www.wildml.com/feed/",
 "Yoav Goldberg":       "https://gist.github.com/yoavg.atom",  # NLP 专家
 "Alexander Rush":      "http://rush-nlp.com/feed.xml",  # Harvard NLP
 "Graham Neubig":       "http://www.phontron.com/feed.xml",  # CMU NLP
 "Tim Dettmers":        "https://timdettmers.com/feed/",  # 量化/优化
 "Thomas Wolf":         "https://thomwolf.io/feed.xml",  # HuggingFace CTO
 "Yannic Kilcher":      "https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew",  # YouTube AI 解读
 "Two Minute Papers":   "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg",
 "Lex Fridman":         "https://lexfridman.com/feed/podcast/",  # AI 播客
}

# ===== 新增：实验室/机构（10 个）=====
FEEDS_LABS = {
 "MIT CSAIL":           "https://www.csail.mit.edu/rss.xml",
 "Stanford AI Lab":     "https://ai.stanford.edu/blog/feed.xml",
 "CMU ML Blog":         "https://blog.ml.cmu.edu/feed/",
 "Princeton NLP":       "https://princeton-nlp.github.io/feed.xml",
 "DeepMind Blog":       "https://www.deepmind.com/blog/rss.xml",
 "Meta AI":             "https://ai.meta.com/blog/rss/",
 "Microsoft Research":  "https://www.microsoft.com/en-us/research/feed/",
 "Allen Institute AI":  "https://allenai.org/blog/rss",
 "Montreal.AI":         "https://montrealartificialintelligence.com/feed/",
 "EleutherAI":          "https://blog.eleuther.ai/rss/",
}

# ===== 新增：AI 公司（8 个）=====
FEEDS_COMPANIES = {
 "Cohere Blog":         "https://cohere.com/blog/rss.xml",
 "Mistral AI":          "https://mistral.ai/news/rss/",  # 法国 AI 独角兽
 "Stability AI":        "https://stability.ai/blog/rss",
 "Replicate Blog":      "https://replicate.com/blog/rss.xml",
 "Modal Labs":          "https://modal.com/blog/rss.xml",
 "Weights & Biases":    "https://wandb.ai/site/blog/rss.xml",
 "LangChain Blog":      "https://blog.langchain.dev/rss/",
 "Pinecone Blog":       "https://www.pinecone.io/blog/rss/",  # 向量数据库
}

# ===== 新增：AI 新闻/媒体（5 个）=====
FEEDS_NEWS = {
 "VentureBeat AI":      "https://venturebeat.com/category/ai/feed/",
 "TechCrunch AI":       "https://techcrunch.com/category/artificial-intelligence/feed/",
 "MIT Tech Review AI":  "https://www.technologyreview.com/topic/artificial-intelligence/feed",
 "The Verge AI":        "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
 "AI News (AAAI)":      "https://aitopics.org/search?page=0&f%5B0%5D=content_type%3Anews&format=rss",
}

# ===== 新增：开源项目（5 个）=====
FEEDS_PROJECTS = {
 "PyTorch Blog":        "https://pytorch.org/blog/feed.xml",
 "TensorFlow Blog":     "https://blog.tensorflow.org/feeds/posts/default",
 "Keras.io":            "https://keras.io/atom.xml",
 "LlamaIndex Blog":     "https://www.llamaindex.ai/blog/rss.xml",
 "Gradio Blog":         "https://www.gradio.app/blog/rss.xml",
}

# ===== 合并（总计 57 个）=====
FEEDS_ALL = {
    **FEEDS_CURRENT,
    **FEEDS_PERSONAL_BLOGS,
    **FEEDS_LABS,
    **FEEDS_COMPANIES,
    **FEEDS_NEWS,
    **FEEDS_PROJECTS,
}

# ===== 使用建议 =====
"""
渐进式添加方案：

Week 1: 加个人博客前 5 个（Karpathy, Distill, Chollet, Howard, Thomas）
Week 2: 加实验室前 5 个（MIT, Stanford, CMU, Princeton, DeepMind）
Week 3: 加 AI 公司全部 8 个
Week 4: 加新闻媒体全部 5 个
Week 5: 加开源项目全部 5 个
Week 6: 加剩余个人博客

每次加完跑一次 rss_w2.py，检查 source_status 里有没有 FAIL。

常见问题：
1. "FAIL:URLError" → 可能需要代理，或者源已失效
2. "empty (bozo:1)" → RSS 格式有问题，但 feedparser 容错性强，通常能解析
3. "ok:0" → 源正常但 90 天内无新文章

优化建议：
- 加并发（10 个线程同时抓，从 30 秒降到 5 秒）
- 加重试（单源失败自动重试 3 次）
- 加缓存（24 小时内不重复抓同一个源）
"""
