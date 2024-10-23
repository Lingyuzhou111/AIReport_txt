import os
import json
import requests
from common.log import logger
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *
import config

@plugins.register(name="AIReport_txt",
                  desc="获取AI相关的最新资讯",
                  version="1.0",
                  author="Lingyuzhou",
                  desire_priority=500)
class AIReport_txt(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] initialized")

    def get_help_text(self, **kwargs):
        return "输入“AI简讯”获取最新的AI相关资讯。"

    def on_handle_context(self, e_context):
        if e_context['context'].type == ContextType.TEXT:
            content = e_context["context"].content.strip()
            if content.startswith("AI简讯"):
                logger.info(f"[{__class__.__name__}] 收到消息: {content}")
                self.fetch_ai_news(e_context)

    def fetch_ai_news(self, e_context):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if not os.path.exists(config_path):
            logger.error(f"请先配置{config_path}文件")
            return

        with open(config_path, 'r') as file:
            api_key = json.load(file).get('TIAN_API_KEY', '')
        
        if not api_key:
            logger.error("API key is missing in config.json")
            return

        url = f"https://apis.tianapi.com/ai/index?key={api_key}&num=10"
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            data = response.json()
            # 检查API返回的内容
            if data.get('code') == 200:
                if 'result' in data and 'newslist' in data['result']:
                    self.construct_reply(data['result']['newslist'], e_context)
                else:
                    logger.error(f"API返回格式不正确: {data}")
                    self.send_error_reply(e_context, "获取资讯失败，返回数据格式不正确。")
            else:
                logger.error(f"API error: {data.get('msg', '未知错误')}")
                self.send_error_reply(e_context, f"获取资讯失败: {data.get('msg', '未知错误')}。")
        except Exception as e:
            logger.error(f"接口抛出异常: {e}")
            self.send_error_reply(e_context, "请求失败，请稍后再试。")

    def construct_reply(self, newslist, e_context):
        reply = Reply()
        reply.type = ReplyType.TEXT
        
        # 构造回复内容
        reply.content = "📢 最新AI资讯如下：\n"
        
        for i, news_item in enumerate(newslist, 1):
            title = news_item.get('title', '未知标题').replace('\n', '')
            link = news_item.get('url', '未知链接').replace('\n', '')
            reply.content += f"No.{i}《{title}》\n🔗{link}\n"

        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def send_error_reply(self, e_context, message):
        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = message
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS