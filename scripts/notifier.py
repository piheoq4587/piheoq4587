"""
推送器：把整理好的资讯发到 Telegram（必选）和 Slack（可选）。

- Telegram：中文标题 + 来源 + 英文原文链接
- Slack：若提供 SLACK_BOT_TOKEN，则把对应内容回发到各频道
"""

import html
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import requests

from config import CHANNELS, MAX_ITEMS_PER_CHANNEL

logger = logging.getLogger(__name__)

TG_LIMIT = 4096  # Telegram 单条消息字符上限
_WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


def _beijing_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=8)


# ---------------- Telegram ----------------
class Telegram:
    def __init__(self, token: str):
        self.token = token
        self.api = f"https://api.telegram.org/bot{token}"

    def get_chat_ids(self) -> List[int]:
        """通过 getUpdates 发现最近与机器人对话过的 chat_id。"""
        try:
            r = requests.get(f"{self.api}/getUpdates", timeout=20)
            data = r.json()
            ids = set()
            for upd in data.get("result", []):
                msg = upd.get("message") or upd.get("my_chat_member") or {}
                chat = msg.get("chat", {})
                if chat.get("id"):
                    ids.add(chat["id"])
            return list(ids)
        except Exception as ex:
            logger.error("getUpdates 失败: %s", ex)
            return []

    def send(self, chat_id: int, text: str) -> bool:
        try:
            r = requests.post(
                f"{self.api}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                      "disable_web_page_preview": False},
                timeout=20,
            )
            ok = r.json().get("ok", False)
            if not ok:
                logger.warning("Telegram 发送失败: %s", r.text[:200])
            return ok
        except Exception as ex:
            logger.error("Telegram 发送异常: %s", ex)
            return False


def build_telegram_messages(grouped: Dict[str, List]) -> List[str]:
    """构建分段消息（头部 + 各频道），每段不超过 Telegram 上限。"""
    now = _beijing_now()
    header = (
        "📰 <b>科研AI资讯日报</b>\n"
        f"📅 {now.strftime('%Y年%m月%d日')} · 星期{_WEEKDAYS[now.weekday()]}（北京时间）\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    messages = [header]

    for key, channel in CHANNELS.items():
        items = grouped.get(key, [])[:MAX_ITEMS_PER_CHANNEL]
        if not items:
            continue
        block = f"\n{channel['emoji']} <b>{channel['name']}</b>\n"
        for item in items:
            title = html.escape(item.title_zh or item.title)
            block += f"▪️ <b>{title}</b>\n"
            if item.title_zh and item.title_zh != item.title:
                block += f"   <i>{html.escape(item.title[:120])}</i>\n"
            src = html.escape(item.source)
            link = html.escape(item.link, quote=True)
            if link:
                block += f"   {src} · <a href=\"{link}\">阅读原文 ↗</a>\n"
            else:
                block += f"   {src}\n"
        messages.append(block)

    if len(messages) == 1:
        messages.append("\n📭 今日各来源暂无新内容（可能是来源临时不可用）。")

    messages.append(
        "\n━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 每日自动汇总 · 来源：arXiv / bioRxiv / Nature / PubMed 等"
    )
    return _pack(messages)


def _pack(blocks: List[str]) -> List[str]:
    """把多个块合并成尽量少、且不超长的消息。"""
    packed, cur = [], ""
    for b in blocks:
        if len(cur) + len(b) + 1 > TG_LIMIT:
            if cur:
                packed.append(cur)
            cur = b
        else:
            cur = f"{cur}\n{b}" if cur else b
    if cur:
        packed.append(cur)
    return packed


def push_telegram(grouped: Dict[str, List]) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logger.error("未设置 TELEGRAM_BOT_TOKEN，无法推送")
        return False

    tg = Telegram(token)

    # 优先用显式配置的 chat_id（逗号分隔多个），否则自动发现
    raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if raw:
        chat_ids = [int(x) for x in raw.replace(" ", "").split(",") if x]
    else:
        chat_ids = tg.get_chat_ids()
        logger.info("自动发现 chat_id: %s", chat_ids)

    if not chat_ids:
        logger.error("没有可用的 chat_id。请先在 Telegram 给机器人发 /start。")
        return False

    messages = build_telegram_messages(grouped)
    all_ok = True
    for cid in chat_ids:
        for msg in messages:
            if not tg.send(cid, msg):
                all_ok = False
        logger.info("已向 chat_id=%s 推送 %d 段", cid, len(messages))
    return all_ok


# ---------------- Slack（可选回发）----------------
def push_slack(grouped: Dict[str, List]) -> None:
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        logger.info("未设置 SLACK_BOT_TOKEN，跳过 Slack 回发")
        return

    headers = {"Authorization": f"Bearer {token}",
               "Content-Type": "application/json; charset=utf-8"}
    for key, channel in CHANNELS.items():
        items = grouped.get(key, [])[:MAX_ITEMS_PER_CHANNEL]
        if not items:
            continue
        lines = [f"*{channel['name']} 今日资讯*"]
        for item in items:
            title = item.title_zh or item.title
            lines.append(f"• {title}\n  <{item.link}|原文> · {item.source}")
        text = "\n".join(lines)
        try:
            r = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json={"channel": channel["slack_id"], "text": text,
                      "unfurl_links": False},
                timeout=20,
            )
            if not r.json().get("ok"):
                logger.warning("Slack 回发失败 [%s]: %s", channel["name"], r.text[:200])
        except Exception as ex:
            logger.warning("Slack 回发异常 [%s]: %s", channel["name"], ex)
