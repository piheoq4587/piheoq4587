"""
配置：频道定义 + 新闻来源（RSS/arXiv/PubMed）

所有来源都是免费、无需 API key 的公开接口，适合在 GitHub Actions 上运行。
"""

# ============ 8 个主题频道 ============
# slack_id 用于（可选的）回发 Slack；没有 Slack bot token 时会自动跳过
CHANNELS = {
    "ai_tools": {"name": "AI工具动态", "emoji": "🛠️", "slack_id": "C0B66BDHK1V"},
    "lifesci": {"name": "生命科学前沿", "emoji": "🧬", "slack_id": "C0B6JDPS4BF"},
    "ai4sci": {"name": "AI赋能科研", "emoji": "🔬", "slack_id": "C0B6FE49527"},
    "deep_research": {"name": "深度研究方法", "emoji": "📚", "slack_id": "C0B6KNZ0NH4"},
    "papers": {"name": "文献精选", "emoji": "📄", "slack_id": "C0B6RDLHBTN"},
    "bioinf": {"name": "生信/组学", "emoji": "🧮", "slack_id": "C0B6JDR3N8M"},
    "tcm_ai": {"name": "中医药+AI", "emoji": "🌿", "slack_id": "C0B6MR407TL"},
    "llm_agents": {"name": "LLM/Agent开发", "emoji": "🤖", "slack_id": "C0B7G442FKJ"},
}

# 每个频道展示的最大条数
MAX_ITEMS_PER_CHANNEL = 4

# ============ RSS / Atom 来源 ============
# (category, 来源名, url)  —— feedparser 可解析 RSS 与 Atom（含 arXiv）
RSS_FEEDS = [
    # AI 工具 / 行业动态
    ("ai_tools", "The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("ai_tools", "MIT Tech Review", "https://www.technologyreview.com/feed/"),
    ("ai_tools", "ScienceDaily AI", "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml"),

    # 生命科学前沿
    ("lifesci", "Nature", "https://www.nature.com/nature.rss"),
    ("lifesci", "Cell Press", "https://www.cell.com/cell/inpress.rss"),

    # 生信 / 组学（bioRxiv 分栏 RSS）
    ("bioinf", "bioRxiv 生信", "http://connect.biorxiv.org/biorxiv_xml.php?subject=bioinformatics"),
    ("bioinf", "bioRxiv 基因组", "http://connect.biorxiv.org/biorxiv_xml.php?subject=genomics"),
]

# ============ arXiv 来源 ============
# (category, arXiv 检索式)  —— 按提交时间倒序取最新
ARXIV_QUERIES = [
    ("ai4sci", "cat:cs.LG+AND+cat:q-bio.QM"),
    ("deep_research", "cat:cs.AI"),
    ("llm_agents", "cat:cs.CL"),
    ("papers", "cat:cs.LG"),
]

# ============ PubMed 来源（eutils，关键词检索）============
# (category, 检索式)
PUBMED_QUERIES = [
    ("tcm_ai", '("network pharmacology"[Title] OR "traditional chinese medicine"[Title]) AND ("artificial intelligence" OR "machine learning" OR "deep learning")'),
    ("lifesci", '"artificial intelligence"[Title] AND (medicine OR clinical)'),
]
