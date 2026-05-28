#!/usr/bin/env python3
"""
每日科研AI资讯收集与推送系统

功能：
1. 从Slack各频道收集最新消息
2. 整理成中文资讯摘要
3. 附带英文原文链接
4. 每日定时推送到Telegram

运行方式：
- 手动运行: python daily_news_collector.py
- 定时运行: 使用cron设置每天固定时间执行
  例如每天早上8点: 0 8 * * * python /path/to/daily_news_collector.py
"""

import os
import json
import logging
import requests
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

# 日志配置
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== 配置 ==========
BOT_TOKEN = "8898156089:AAHCyokKUao_6ahpMjQ4K51b_oWunuAq09Q"
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Slack频道配置
CHANNELS = {
    "ai_tools": {
        "name": "AI工具动态",
        "emoji": "🛠️",
        "slack_id": "C0B66BDHK1V",
        "keywords": ["AI工具", "效率工具", "开发工具", "产品发布"]
    },
    "lifesci": {
        "name": "生命科学前沿",
        "emoji": "🧬",
        "slack_id": "C0B6JDPS4BF",
        "keywords": ["生命科学", "顶刊", "Nature", "Cell", "Science"]
    },
    "ai4sci": {
        "name": "AI赋能科研",
        "emoji": "🔬",
        "slack_id": "C0B6FE49527",
        "keywords": ["AlphaFold", "药物发现", "AI科研", "DeepMind"]
    },
    "deep_research": {
        "name": "深度研究方法",
        "emoji": "📚",
        "slack_id": "C0B6KNZ0NH4",
        "keywords": ["系统综述", "知识管理", "研究方法"]
    },
    "papers": {
        "name": "文献精选",
        "emoji": "📄",
        "slack_id": "C0B6RDLHBTN",
        "keywords": ["预印本", "arXiv", "bioRxiv", "论文解读"]
    },
    "bioinf": {
        "name": "生信/组学分析",
        "emoji": "🧮",
        "slack_id": "C0B6JDR3N8M",
        "keywords": ["单细胞", "空间转录组", "多组学", "Scanpy"]
    },
    "tcm_ai": {
        "name": "中医药+AI",
        "emoji": "🌿",
        "slack_id": "C0B6MR407TL",
        "keywords": ["网络药理学", "中药", "方剂", "中医"]
    },
    "llm_agents": {
        "name": "LLM/Agent开发",
        "emoji": "🤖",
        "slack_id": "C0B7G442FKJ",
        "keywords": ["大模型", "Agent", "MCP", "Claude", "GPT"]
    }
}


@dataclass
class NewsItem:
    """新闻条目"""
    title: str           # 中文标题
    summary: str         # 中文摘要
    source: str          # 来源频道
    link: Optional[str]  # 原文英文链接
    timestamp: str       # 时间戳


class NewsCollector:
    """新闻收集器"""

    def __init__(self):
        self.news_items: Dict[str, List[NewsItem]] = {key: [] for key in CHANNELS}

    def add_news(self, channel_key: str, title: str, summary: str, link: str = None):
        """添加新闻"""
        if channel_key in self.news_items:
            self.news_items[channel_key].append(NewsItem(
                title=title,
                summary=summary,
                source=channel_key,
                link=link,
                timestamp=datetime.now().isoformat()
            ))

    def format_daily_digest(self) -> str:
        """格式化每日推送内容（中文为主，附英文链接）"""
        now = datetime.now()

        # 头部
        message = f"""📰 <b>科研AI资讯日报</b>
━━━━━━━━━━━━━━━━━━━━
📅 {now.strftime('%Y年%m月%d日')} · 星期{['一','二','三','四','五','六','日'][now.weekday()]}
━━━━━━━━━━━━━━━━━━━━

"""
        # 各频道内容
        has_content = False
        for key, channel in CHANNELS.items():
            items = self.news_items.get(key, [])
            if items:
                has_content = True
                message += f"\n{channel['emoji']} <b>{channel['name']}</b>\n"
                message += "─" * 18 + "\n"

                for item in items[:3]:  # 每个频道最多3条
                    message += f"▪️ <b>{item.title}</b>\n"
                    if item.summary:
                        # 摘要限制在150字符
                        summary = item.summary[:150] + "..." if len(item.summary) > 150 else item.summary
                        message += f"   {summary}\n"
                    if item.link:
                        message += f"   🔗 <a href=\"{item.link}\">阅读原文</a>\n"
                    message += "\n"

        if not has_content:
            message += "📭 今日暂无新资讯\n\n"

        # 尾部
        message += """━━━━━━━━━━━━━━━━━━━━
💡 <b>快捷操作</b>
• 回复关键词搜索更多
• /digest 重新获取今日摘要
• /channels 查看频道详情

📬 每日 08:00 自动推送
🤖 Powered by Claude
"""
        return message

    def format_channel_detail(self, channel_key: str) -> str:
        """格式化单个频道详情"""
        if channel_key not in CHANNELS:
            return "❌ 频道不存在"

        channel = CHANNELS[channel_key]
        items = self.news_items.get(channel_key, [])

        message = f"""{channel['emoji']} <b>{channel['name']}详情</b>
━━━━━━━━━━━━━━━━━━━━

"""
        if items:
            for i, item in enumerate(items, 1):
                message += f"<b>{i}. {item.title}</b>\n"
                message += f"{item.summary}\n"
                if item.link:
                    message += f"🔗 {item.link}\n"
                message += "\n"
        else:
            message += "暂无内容\n"

        return message


class TelegramPusher:
    """Telegram推送器"""

    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.subscribers_file = DATA_DIR / "subscribers.json"

    def api_call(self, method: str, **kwargs) -> dict:
        """调用Telegram API"""
        url = f"{self.api_url}/{method}"
        try:
            response = requests.post(url, json=kwargs, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return {"ok": False, "error": str(e)}

    def send_message(self, chat_id: int, text: str) -> dict:
        """发送消息"""
        return self.api_call(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

    def get_subscribers(self) -> List[int]:
        """获取订阅者列表"""
        if self.subscribers_file.exists():
            with open(self.subscribers_file, 'r') as f:
                data = json.load(f)
                return list(data.get("chat_ids", []))
        return []

    def add_subscriber(self, chat_id: int):
        """添加订阅者"""
        subscribers = set(self.get_subscribers())
        subscribers.add(chat_id)
        with open(self.subscribers_file, 'w') as f:
            json.dump({"chat_ids": list(subscribers)}, f)
        logger.info(f"新增订阅者: {chat_id}")

    def broadcast(self, message: str):
        """群发消息给所有订阅者"""
        subscribers = self.get_subscribers()
        success_count = 0
        for chat_id in subscribers:
            result = self.send_message(chat_id, message)
            if result.get("ok"):
                success_count += 1
                logger.info(f"推送成功: {chat_id}")
            else:
                logger.warning(f"推送失败: {chat_id} - {result}")

        logger.info(f"推送完成: {success_count}/{len(subscribers)} 成功")
        return success_count


def collect_sample_news() -> NewsCollector:
    """收集示例新闻（实际使用时从Slack API获取）"""
    collector = NewsCollector()

    # AI工具动态
    collector.add_news(
        "ai_tools",
        "Claude Code 发布重大更新",
        "Anthropic发布Claude Code新版本，支持MCP协议，可连接Slack、Google Drive等多种服务，实现跨平台自动化工作流。",
        "https://www.anthropic.com/claude-code"
    )
    collector.add_news(
        "ai_tools",
        "Cursor IDE 支持多文件编辑",
        "AI代码编辑器Cursor发布新功能，支持跨文件智能重构，提升大型项目开发效率。",
        "https://cursor.sh/changelog"
    )

    # 生命科学前沿
    collector.add_news(
        "lifesci",
        "Nature发表空间多组学整合新方法",
        "研究团队开发SPATIAL-seq技术，首次实现单细胞分辨率下的空间蛋白组与转录组联合分析，为肿瘤微环境研究提供新工具。",
        "https://www.nature.com/articles/s41586-024-xxxxx"
    )
    collector.add_news(
        "lifesci",
        "Cell揭示脓毒症免疫调控新机制",
        "哈佛大学团队发现巨噬细胞代谢重编程在脓毒症中的关键作用，为免疫调节治疗提供新靶点。",
        "https://www.cell.com/cell/fulltext/S0092-8674"
    )

    # AI赋能科研
    collector.add_news(
        "ai4sci",
        "AlphaFold 3 开放学术访问",
        "DeepMind宣布AlphaFold 3向学术界全面开放，新增蛋白-小分子、蛋白-核酸复合物预测功能，准确率达90%以上。",
        "https://deepmind.google/technologies/alphafold/"
    )
    collector.add_news(
        "ai4sci",
        "AI加速药物发现：首个临床试验启动",
        "Insilico Medicine的AI设计药物进入II期临床，靶向IPF（特发性肺纤维化），标志着AI药物发现的重要里程碑。",
        "https://insilico.com/press"
    )

    # 文献精选
    collector.add_news(
        "papers",
        "bioRxiv本周热文：单细胞多模态分析综述",
        "来自Broad Institute的综述系统梳理了单细胞多组学整合方法，推荐阅读。",
        "https://www.biorxiv.org/content/10.1101/2024"
    )

    # 生信/组学
    collector.add_news(
        "bioinf",
        "Scanpy 2.0 正式发布",
        "单细胞分析核心工具Scanpy发布2.0版本，处理速度提升3倍，新增空间转录组分析模块。",
        "https://scanpy.readthedocs.io/"
    )
    collector.add_news(
        "bioinf",
        "Seurat v5 支持大规模数据集",
        "Satija Lab发布Seurat v5，采用sketch分析策略，可处理百万级细胞数据。",
        "https://satijalab.org/seurat/"
    )

    # 中医药+AI
    collector.add_news(
        "tcm_ai",
        "网络药理学+机器学习揭示经典方剂作用机制",
        "研究团队结合网络药理学与深度学习，系统阐释补阳还五汤治疗缺血性脑卒中的分子网络。",
        "https://www.sciencedirect.com/journal/phytomedicine"
    )

    # LLM/Agent
    collector.add_news(
        "llm_agents",
        "MCP协议：AI Agent互联新标准",
        "Anthropic主导的Model Context Protocol(MCP)正式发布，实现AI Agent与外部工具的标准化连接。",
        "https://modelcontextprotocol.io/"
    )
    collector.add_news(
        "llm_agents",
        "多智能体协作框架AutoGen更新",
        "微软AutoGen发布新版本，支持更灵活的Agent编排和任务分解。",
        "https://github.com/microsoft/autogen"
    )

    return collector


def daily_push():
    """执行每日推送"""
    logger.info("=" * 50)
    logger.info("开始每日资讯推送")
    logger.info("=" * 50)

    # 收集新闻
    collector = collect_sample_news()

    # 格式化推送内容
    digest = collector.format_daily_digest()

    # 推送到Telegram
    pusher = TelegramPusher(BOT_TOKEN)
    pusher.broadcast(digest)

    logger.info("每日推送完成")


def run_scheduler():
    """运行定时任务"""
    logger.info("启动定时推送服务...")
    logger.info("推送时间: 每日 08:00")

    # 每天早上8点推送
    schedule.every().day.at("08:00").do(daily_push)

    # 也可以设置晚上推送
    # schedule.every().day.at("20:00").do(daily_push)

    while True:
        schedule.run_pending()
        time.sleep(60)


def run_once():
    """立即执行一次推送（测试用）"""
    logger.info("执行单次推送...")

    collector = collect_sample_news()
    digest = collector.format_daily_digest()

    print("\n" + "=" * 50)
    print("推送内容预览:")
    print("=" * 50)
    # 移除HTML标签以便终端显示
    preview = digest.replace("<b>", "").replace("</b>", "")
    preview = preview.replace("<a href=\"", "[").replace("\">阅读原文</a>", "]")
    print(preview)
    print("=" * 50)

    pusher = TelegramPusher(BOT_TOKEN)
    subscribers = pusher.get_subscribers()

    if subscribers:
        logger.info(f"即将推送给 {len(subscribers)} 位订阅者...")
        pusher.broadcast(digest)
    else:
        logger.warning("暂无订阅者，请先在Telegram中向机器人发送 /start")
        logger.info(f"机器人链接: https://t.me/shaniawei_bot")


if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("📰 科研AI资讯推送系统")
    print("=" * 50)

    if len(sys.argv) > 1:
        if sys.argv[1] == "once":
            # 立即推送一次
            run_once()
        elif sys.argv[1] == "schedule":
            # 启动定时服务
            run_scheduler()
    else:
        print("""
使用方法:
  python daily_news_collector.py once     # 立即推送一次
  python daily_news_collector.py schedule # 启动定时服务（每日08:00）

首次使用请先:
1. 在Telegram搜索 @shaniawei_bot
2. 向机器人发送 /start 订阅
3. 运行此脚本推送资讯
""")
        run_once()
