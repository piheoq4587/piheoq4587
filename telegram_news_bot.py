#!/usr/bin/env python3
"""
Telegram科研AI资讯推送机器人

使用方法：
1. pip install -r requirements.txt
2. python telegram_news_bot.py

机器人命令：
/start - 开始并订阅资讯
/digest - 获取今日资讯摘要
/channels - 查看所有频道
/subscribe - 订阅指定频道
/unsubscribe - 取消订阅
/help - 帮助信息
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token
BOT_TOKEN = "8898156089:AAHCyokKUao_6ahpMjQ4K51b_oWunuAq09Q"

# 数据存储文件
DATA_FILE = Path(__file__).parent / "bot_data.json"

# Slack频道配置
CHANNELS = {
    "ai_tools": {
        "name": "AI工具动态",
        "emoji": "🛠️",
        "slack_id": "C0B66BDHK1V",
        "description": "最新AI产品发布、效率工具、开发工具"
    },
    "lifesci": {
        "name": "生命科学前沿",
        "emoji": "🧬",
        "slack_id": "C0B6JDPS4BF",
        "description": "顶刊论文、疾病机制、临床研究"
    },
    "ai4sci": {
        "name": "AI赋能科研",
        "emoji": "🔬",
        "slack_id": "C0B6FE49527",
        "description": "AlphaFold、药物发现、科学计算"
    },
    "deep_research": {
        "name": "深度研究",
        "emoji": "📚",
        "slack_id": "C0B6KNZ0NH4",
        "description": "系统综述、知识管理、研究方法"
    },
    "papers": {
        "name": "文献精选",
        "emoji": "📄",
        "slack_id": "C0B6RDLHBTN",
        "description": "预印本追踪、高引论文、论文解读"
    },
    "bioinf": {
        "name": "生信/组学",
        "emoji": "🧮",
        "slack_id": "C0B6JDR3N8M",
        "description": "单细胞分析、空间转录组、多组学"
    },
    "tcm_ai": {
        "name": "中医药+AI",
        "emoji": "🌿",
        "slack_id": "C0B6MR407TL",
        "description": "网络药理学、方剂研究、中药现代化"
    },
    "llm_agents": {
        "name": "LLM/Agent",
        "emoji": "🤖",
        "slack_id": "C0B7G442FKJ",
        "description": "大模型应用、AI Agent、MCP开发"
    }
}


class BotData:
    """机器人数据管理"""

    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.data = self._load()

    def _load(self) -> dict:
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"subscribers": {}, "last_update_id": 0}

    def save(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_subscriber(self, chat_id: int, channels: List[str] = None):
        """添加订阅者"""
        if channels is None:
            channels = list(CHANNELS.keys())
        self.data["subscribers"][str(chat_id)] = {
            "channels": channels,
            "subscribed_at": datetime.now().isoformat(),
            "active": True
        }
        self.save()

    def get_subscribers(self) -> Dict:
        return self.data["subscribers"]

    @property
    def last_update_id(self) -> int:
        return self.data.get("last_update_id", 0)

    @last_update_id.setter
    def last_update_id(self, value: int):
        self.data["last_update_id"] = value
        self.save()


class TelegramBot:
    """Telegram机器人"""

    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.data = BotData(DATA_FILE)

    def api_call(self, method: str, **kwargs) -> dict:
        """调用Telegram API"""
        url = f"{self.api_url}/{method}"
        response = requests.post(url, json=kwargs)
        return response.json()

    def get_me(self) -> dict:
        return self.api_call("getMe")

    def get_updates(self, offset: int = 0, timeout: int = 30) -> dict:
        return self.api_call("getUpdates", offset=offset, timeout=timeout)

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> dict:
        return self.api_call(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=False
        )

    def handle_start(self, chat_id: int, user_name: str):
        """处理 /start 命令"""
        self.data.add_subscriber(chat_id)

        message = f"""🎉 <b>欢迎 {user_name}!</b>

你已成功订阅<b>科研AI资讯推送</b>！

📬 我会定期从以下频道收集最新资讯并推送给你：

"""
        for key, ch in CHANNELS.items():
            message += f"{ch['emoji']} <b>{ch['name']}</b>\n"
            message += f"   {ch['description']}\n"

        message += """
━━━━━━━━━━━━━━━━━━━━

<b>可用命令:</b>
/digest - 获取今日资讯摘要
/channels - 查看所有频道
/subscribe - 订阅管理
/help - 帮助信息

💡 敬请期待每日资讯推送！
"""
        self.send_message(chat_id, message)

    def handle_digest(self, chat_id: int):
        """处理 /digest 命令 - 发送今日摘要"""
        now = datetime.now()
        message = f"""📰 <b>科研AI资讯摘要</b>
📅 {now.strftime('%Y年%m月%d日 %H:%M')}
━━━━━━━━━━━━━━━━━━━━

"""
        # 这里将来会从Slack频道获取真实内容
        # 目前显示示例内容
        sample_news = [
            ("🛠️", "AI工具动态", "Claude Code发布新版本，支持MCP协议和多智能体协作"),
            ("🧬", "生命科学前沿", "Nature Methods发表空间多组学整合分析新方法"),
            ("🔬", "AI赋能科研", "AlphaFold 3开放学术使用，支持蛋白-配体复合物预测"),
            ("📄", "文献精选", "Cell报道肿瘤微环境单细胞图谱构建新进展"),
            ("🧮", "生信/组学", "Scanpy 2.0发布：更快的单细胞数据处理"),
            ("🤖", "LLM/Agent", "OpenAI发布GPT-4o mini，适合Agent应用开发"),
        ]

        for emoji, channel, news in sample_news:
            message += f"{emoji} <b>{channel}</b>\n"
            message += f"• {news}\n\n"

        message += """━━━━━━━━━━━━━━━━━━━━
💡 回复关键词获取详细内容
📬 由Claude从Slack频道自动收集
"""
        self.send_message(chat_id, message)

    def handle_channels(self, chat_id: int):
        """处理 /channels 命令"""
        message = """📋 <b>科研资讯频道列表</b>
━━━━━━━━━━━━━━━━━━━━

"""
        for key, ch in CHANNELS.items():
            message += f"{ch['emoji']} <b>{ch['name']}</b>\n"
            message += f"   📝 {ch['description']}\n"
            message += f"   🔗 Slack: #{ch['slack_id'][:10]}...\n\n"

        message += """━━━━━━━━━━━━━━━━━━━━
💡 所有频道内容每日自动汇总推送
"""
        self.send_message(chat_id, message)

    def handle_help(self, chat_id: int):
        """处理 /help 命令"""
        message = """📖 <b>使用帮助</b>
━━━━━━━━━━━━━━━━━━━━

<b>命令列表:</b>
/start - 开始订阅资讯
/digest - 获取今日摘要
/channels - 查看频道列表
/help - 显示本帮助

<b>关键词搜索:</b>
直接发送关键词，获取相关资讯
例如: "AlphaFold", "单细胞", "空间转录组"

<b>信息来源:</b>
资讯收集自多个Slack科研频道，
包括AI工具、生命科学、生信分析等

━━━━━━━━━━━━━━━━━━━━
🤖 Powered by Claude
"""
        self.send_message(chat_id, message)

    def handle_message(self, message: dict):
        """处理收到的消息"""
        chat_id = message["chat"]["id"]
        user = message.get("from", {})
        user_name = user.get("first_name", "用户")
        text = message.get("text", "")

        logger.info(f"收到消息: {text} (from {user_name}, chat_id: {chat_id})")

        if text.startswith("/start"):
            self.handle_start(chat_id, user_name)
        elif text.startswith("/digest"):
            self.handle_digest(chat_id)
        elif text.startswith("/channels"):
            self.handle_channels(chat_id)
        elif text.startswith("/help"):
            self.handle_help(chat_id)
        else:
            # 处理普通消息 - 关键词搜索
            self.send_message(
                chat_id,
                f"🔍 搜索: <b>{text}</b>\n\n"
                f"正在从科研频道搜索相关资讯...\n"
                f"（功能开发中，敬请期待）"
            )

    def run(self):
        """运行机器人（轮询模式）"""
        logger.info("启动Telegram机器人...")

        # 检查机器人信息
        me = self.get_me()
        if me.get("ok"):
            bot_info = me["result"]
            logger.info(f"机器人: @{bot_info['username']} ({bot_info['first_name']})")
        else:
            logger.error(f"无法连接到Telegram: {me}")
            return

        logger.info("开始监听消息...")

        while True:
            try:
                updates = self.get_updates(
                    offset=self.data.last_update_id + 1,
                    timeout=30
                )

                if updates.get("ok") and updates.get("result"):
                    for update in updates["result"]:
                        self.data.last_update_id = update["update_id"]

                        if "message" in update:
                            self.handle_message(update["message"])

            except KeyboardInterrupt:
                logger.info("收到停止信号，退出...")
                break
            except Exception as e:
                logger.error(f"错误: {e}")
                continue


def broadcast_digest(bot: TelegramBot):
    """向所有订阅者推送今日摘要"""
    subscribers = bot.data.get_subscribers()
    for chat_id in subscribers:
        try:
            bot.handle_digest(int(chat_id))
            logger.info(f"已推送摘要到 chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"推送失败 {chat_id}: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 科研AI资讯推送机器人")
    print("=" * 50)
    print(f"\n机器人链接: https://t.me/shaniawei_bot")
    print("\n请在Telegram中向机器人发送 /start 开始使用")
    print("-" * 50)

    bot = TelegramBot(BOT_TOKEN)
    bot.run()
