"""
入口：收集 -> 翻译 -> 推送 Telegram（+ 可选 Slack）

环境变量：
  TELEGRAM_BOT_TOKEN   必填，Telegram 机器人 token
  TELEGRAM_CHAT_ID     选填，目标 chat_id（逗号分隔多个）；不填则自动发现
  SLACK_BOT_TOKEN      选填，提供则把资讯回发到对应 Slack 频道
  TRANSLATE_SUMMARY    选填，设为 "1" 时连摘要一起翻译（更慢）

本地调试：
  DRY_RUN=1 python scripts/main.py   # 只打印，不真正推送
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector import collect_all
from translator import translate_items
from notifier import push_telegram, push_slack, build_telegram_messages

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("开始收集资讯…")
    grouped = collect_all()

    logger.info("翻译标题为中文…")
    translate_items(grouped, do_summary=os.environ.get("TRANSLATE_SUMMARY") == "1")

    if os.environ.get("DRY_RUN") == "1":
        for msg in build_telegram_messages(grouped):
            print("\n" + "=" * 40)
            print(msg)
        logger.info("DRY_RUN 模式，未实际推送")
        return 0

    ok = push_telegram(grouped)
    push_slack(grouped)

    if not ok:
        logger.error("Telegram 推送未完全成功")
        return 1
    logger.info("全部完成 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
