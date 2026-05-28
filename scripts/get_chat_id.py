"""
辅助脚本：找出你的 Telegram chat_id。

用法：
  1. 在 Telegram 里给机器人 @shaniawei_bot 发一条消息（比如 /start）
  2. 运行本脚本（或在 GitHub Actions 里手动触发 get-chat-id 工作流）
  3. 把打印出的 chat_id 填到仓库 Secret: TELEGRAM_CHAT_ID
"""

import os
import sys

import requests


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("❌ 请先设置环境变量 TELEGRAM_BOT_TOKEN")
        return 1

    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20)
    data = r.json()
    if not data.get("ok"):
        print(f"❌ 调用失败: {data}")
        return 1

    found = {}
    for upd in data.get("result", []):
        msg = upd.get("message") or {}
        chat = msg.get("chat", {})
        if chat.get("id"):
            name = chat.get("first_name") or chat.get("title") or "?"
            found[chat["id"]] = name

    if not found:
        print("⚠️ 没找到任何对话。请先在 Telegram 给机器人发一条消息，再运行。")
        return 1

    print("✅ 找到以下 chat_id：")
    for cid, name in found.items():
        print(f"   chat_id = {cid}   (来自: {name})")
    print("\n把上面的 chat_id 填到仓库 Secret: TELEGRAM_CHAT_ID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
