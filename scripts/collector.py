"""
新闻收集器：从 RSS / arXiv / PubMed 抓取最新条目，按频道归类。

设计原则：每个来源独立 try/except，单个来源失败不影响其他来源。
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

import requests

from config import RSS_FEEDS, ARXIV_QUERIES, PUBMED_QUERIES, CHANNELS

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 25
USER_AGENT = "research-news-bot/1.0 (+https://github.com)"


@dataclass
class NewsItem:
    category: str
    title: str
    summary: str
    link: str
    source: str
    title_zh: str = ""      # 翻译后的中文标题（可选）
    summary_zh: str = ""    # 翻译后的中文摘要（可选）


def _clean(text: str, limit: int = 280) -> str:
    """去除 HTML 标签与多余空白。"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def fetch_rss() -> List[NewsItem]:
    """抓取 RSS / Atom 来源。"""
    import feedparser

    items: List[NewsItem] = []
    for category, source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
            entries = feed.entries[:3]
            for e in entries:
                title = _clean(getattr(e, "title", ""), 200)
                if not title:
                    continue
                summary = _clean(getattr(e, "summary", ""), 280)
                link = getattr(e, "link", "")
                items.append(NewsItem(category, title, summary, link, source))
            logger.info("RSS [%s] %s: %d 条", category, source, len(entries))
        except Exception as ex:
            logger.warning("RSS 抓取失败 %s (%s): %s", source, url, ex)
    return items


def fetch_arxiv() -> List[NewsItem]:
    """通过 arXiv API 抓取最新论文（Atom 格式，用 feedparser 解析）。"""
    import feedparser

    items: List[NewsItem] = []
    for category, query in ARXIV_QUERIES:
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query={query}"
            "&sortBy=submittedDate&sortOrder=descending&max_results=4"
        )
        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
            for e in feed.entries[:4]:
                title = _clean(getattr(e, "title", ""), 200)
                if not title:
                    continue
                summary = _clean(getattr(e, "summary", ""), 280)
                link = getattr(e, "link", "")
                items.append(NewsItem(category, title, summary, link, "arXiv"))
            logger.info("arXiv [%s]: %d 条", category, len(feed.entries[:4]))
        except Exception as ex:
            logger.warning("arXiv 抓取失败 [%s]: %s", category, ex)
    return items


def fetch_pubmed() -> List[NewsItem]:
    """通过 NCBI eutils 抓取最新 PubMed 文献（JSON，无需 key）。"""
    items: List[NewsItem] = []
    headers = {"User-Agent": USER_AGENT}
    for category, query in PUBMED_QUERIES:
        try:
            esearch = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={"db": "pubmed", "term": query, "retmax": 4,
                        "sort": "date", "retmode": "json"},
                headers=headers, timeout=HTTP_TIMEOUT,
            )
            ids = esearch.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                continue
            esummary = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                headers=headers, timeout=HTTP_TIMEOUT,
            )
            result = esummary.json().get("result", {})
            for pmid in ids:
                rec = result.get(pmid, {})
                title = _clean(rec.get("title", ""), 200)
                if not title:
                    continue
                source = rec.get("fulljournalname") or rec.get("source") or "PubMed"
                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                items.append(NewsItem(category, title, "", link, _clean(source, 60)))
            logger.info("PubMed [%s]: %d 条", category, len(ids))
        except Exception as ex:
            logger.warning("PubMed 抓取失败 [%s]: %s", category, ex)
    return items


def collect_all() -> Dict[str, List[NewsItem]]:
    """收集所有来源并按频道归类。"""
    all_items = fetch_rss() + fetch_arxiv() + fetch_pubmed()

    grouped: Dict[str, List[NewsItem]] = {key: [] for key in CHANNELS}
    seen_titles = set()
    for item in all_items:
        if item.category not in grouped:
            continue
        key = item.title.lower()[:60]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        grouped[item.category].append(item)

    total = sum(len(v) for v in grouped.values())
    logger.info("共收集 %d 条资讯，去重后分布到 %d 个频道", total, len(grouped))
    return grouped
