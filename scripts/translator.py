"""
翻译器：把英文标题/摘要翻译成中文。

默认使用 Google 翻译的免费公开端点（无需 key）。
GitHub Actions 运行器在海外，可正常访问。失败时回退为原文，绝不中断流程。
"""

import logging
import requests

logger = logging.getLogger(__name__)

_ENDPOINT = "https://translate.googleapis.com/translate_a/single"


def translate(text: str, target: str = "zh-CN") -> str:
    """把 text 翻译为目标语言；失败则原样返回。"""
    text = (text or "").strip()
    if not text:
        return ""
    try:
        resp = requests.get(
            _ENDPOINT,
            params={"client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": text},
            timeout=15,
        )
        data = resp.json()
        # 返回结构: [[["译文","原文",...], ...], ...]
        translated = "".join(seg[0] for seg in data[0] if seg and seg[0])
        return translated.strip() or text
    except Exception as ex:
        logger.warning("翻译失败，使用原文: %s", ex)
        return text


def translate_items(grouped, do_summary: bool = False):
    """对分组后的资讯逐条翻译标题（可选翻译摘要）。"""
    for items in grouped.values():
        for item in items:
            item.title_zh = translate(item.title)
            if do_summary and item.summary:
                item.summary_zh = translate(item.summary)
    return grouped
