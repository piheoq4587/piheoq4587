#!/usr/bin/env python3
"""
Slack频道信息收集并推送到Telegram机器人

功能：
- 从Slack各科研频道收集最新消息
- 整理成新闻摘要格式
- 定时推送到Telegram机器人

频道列表：
- #ai-tools-daily: AI工具每日动态
- #lifesci-research: 生命科学前沿
- #ai-for-science: AI赋能科研
- #deep-research: 深度研究方法
- #paper-digest: 文献精选
- #bioinformatics-omics: 生信/组学
- #tcm-ai-research: 中医药+AI
- #llm-agents: LLM/Agent开发
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Telegram Bot配置
TELEGRAM_BOT_TOKEN = "8898156089:AAHCyokKUao_6ahpMjQ4K51b_oWunuAq09Q"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Slack频道配置（Channel ID -> 频道名称/emoji）
SLACK_CHANNELS = {
    "C0B66BDHK1V": {"name": "ai-tools-daily", "emoji": "🛠️", "desc": "AI工具动态"},
    "C0B6JDPS4BF": {"name": "lifesci-research", "emoji": "🧬", "desc": "生命科学前沿"},
    "C0B6FE49527": {"name": "ai-for-science", "emoji": "🔬", "desc": "AI赋能科研"},
    "C0B6KNZ0NH4": {"name": "deep-research", "emoji": "📚", "desc": "深度研究"},
    "C0B6RDLHBTN": {"name": "paper-digest", "emoji": "📄", "desc": "文献精选"},
    "C0B6JDR3N8M": {"name": "bioinformatics-omics", "emoji": "🧮", "desc": "生信/组学"},
    "C0B6MR407TL": {"name": "tcm-ai-research", "emoji": "🌿", "desc": "中医药+AI"},
    "C0B7G442FKJ": {"name": "llm-agents", "emoji": "🤖", "desc": "LLM/Agent"},
}


class TelegramBot:
    """Telegram机器人类"""

    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"

    def get_updates(self, offset: int = 0) -> dict:
        """获取最新消息更新"""
        url = f"{self.api_url}/getUpdates"
        params = {"offset": offset, "timeout": 30}
        response = requests.get(url, params=params)
        return response.json()

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> dict:
        """发送消息"""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        response = requests.post(url, json=data)
        return response.json()

    def get_me(self) -> dict:
        """获取机器人信息"""
        url = f"{self.api_url}/getMe"
        response = requests.get(url)
        return response.json()


class NewsDigest:
    """新闻摘要生成器"""

    def __init__(self):
        self.items: Dict[str, List[dict]] = {}

    def add_item(self, channel_id: str, title: str, summary: str, link: str = None):
        """添加新闻条目"""
        if channel_id not in self.items:
            self.items[channel_id] = []
        self.items[channel_id].append({
            "title": title,
            "summary": summary,
            "link": link,
            "timestamp": datetime.now().isoformat()
        })

    def format_telegram_message(self) -> str:
        """格式化为Telegram消息"""
        now = datetime.now()
        header = f"📰 <b>科研AI资讯日报</b>\n"
        header += f"📅 {now.strftime('%Y年%m月%d日')}\n"
        header += "━" * 20 + "\n\n"

        body = ""
        for channel_id, items in self.items.items():
            if channel_id in SLACK_CHANNELS:
                channel_info = SLACK_CHANNELS[channel_id]
                body += f"{channel_info['emoji']} <b>{channel_info['desc']}</b>\n"
                for item in items[:5]:  # 每个频道最多5条
                    body += f"• {item['title']}\n"
                    if item['summary']:
                        body += f"  <i>{item['summary'][:100]}...</i>\n"
                    if item['link']:
                        body += f"  🔗 {item['link']}\n"
                body += "\n"

        footer = "━" * 20 + "\n"
        footer += "💡 回复关键词获取更多信息\n"
        footer += "📬 由Claude自动收集整理"

        return header + body + footer


def test_telegram_bot():
    """测试Telegram机器人连接"""
    bot = TelegramBot(TELEGRAM_BOT_TOKEN)
    result = bot.get_me()
    if result.get("ok"):
        print(f"✅ Telegram机器人连接成功!")
        print(f"   Bot名称: {result['result']['first_name']}")
        print(f"   Bot用户名: @{result['result']['username']}")
        return True
    else:
        print(f"❌ 连接失败: {result}")
        return False


def send_welcome_message(chat_id: int):
    """发送欢迎消息"""
    bot = TelegramBot(TELEGRAM_BOT_TOKEN)

    welcome = """🎉 <b>欢迎使用科研AI资讯机器人!</b>

我会定期从以下Slack频道收集最新资讯并推送给你：

🛠️ <b>AI工具动态</b> - 最新AI产品和效率工具
🧬 <b>生命科学前沿</b> - 顶刊论文、疾病机制
🔬 <b>AI赋能科研</b> - AlphaFold、药物发现
📚 <b>深度研究</b> - 系统综述、知识管理
📄 <b>文献精选</b> - 预印本追踪、论文解读
🧮 <b>生信/组学</b> - 单细胞、空间转录组
🌿 <b>中医药+AI</b> - 网络药理学、方剂研究
🤖 <b>LLM/Agent</b> - 大模型、多智能体

━━━━━━━━━━━━━━━━━━━━
<b>可用命令:</b>
/start - 开始接收资讯
/digest - 获取今日摘要
/subscribe - 订阅频道
/help - 帮助信息
━━━━━━━━━━━━━━━━━━━━

💡 资讯每日自动推送，敬请期待！
"""

    return bot.send_message(chat_id, welcome)


def create_sample_digest():
    """创建示例新闻摘要"""
    digest = NewsDigest()

    # 添加示例内容
    digest.add_item(
        "C0B66BDHK1V",
        "Claude 4新功能发布",
        "Anthropic发布Claude 4系列新模型，支持更长上下文和多模态能力",
        "https://anthropic.com"
    )
    digest.add_item(
        "C0B6JDPS4BF",
        "Nature发表空间转录组新方法",
        "新型空间转录组技术实现亚细胞分辨率，有望揭示肿瘤微环境",
    )
    digest.add_item(
        "C0B6FE49527",
        "AlphaFold 3预测蛋白-配体复合物",
        "DeepMind最新模型可准确预测蛋白质与小分子的结合模式",
    )

    return digest


def main():
    """主函数"""
    print("=" * 50)
    print("Slack → Telegram 科研资讯推送系统")
    print("=" * 50)

    # 测试Telegram连接
    print("\n1. 测试Telegram机器人连接...")
    if not test_telegram_bot():
        return

    # 创建示例摘要
    print("\n2. 生成示例新闻摘要...")
    digest = create_sample_digest()
    message = digest.format_telegram_message()
    print("摘要内容预览:")
    print("-" * 40)
    print(message[:500] + "...")

    # 等待用户发送消息获取chat_id
    print("\n3. 等待用户消息...")
    print("   请在Telegram中向 @shaniawei_bot 发送任意消息")
    print("   然后程序将自动回复欢迎消息")

    bot = TelegramBot(TELEGRAM_BOT_TOKEN)
    updates = bot.get_updates()

    if updates.get("ok") and updates.get("result"):
        for update in updates["result"]:
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                user_name = update["message"]["from"].get("first_name", "用户")
                print(f"\n   ✅ 收到来自 {user_name} 的消息 (chat_id: {chat_id})")

                # 发送欢迎消息
                result = send_welcome_message(chat_id)
                if result.get("ok"):
                    print(f"   ✅ 欢迎消息发送成功!")
                else:
                    print(f"   ❌ 发送失败: {result}")
    else:
        print("   暂无新消息，请先向机器人发送消息")

    print("\n" + "=" * 50)
    print("系统设置完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
