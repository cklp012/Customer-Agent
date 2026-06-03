"""
AI回复处理器
专注的AI处理，移除复杂预处理和发送逻辑
"""

from typing import Dict, Any, Optional
from bridge.context import Context, ContextType
from .base import BaseHandler
from .preprocessor import MessagePreprocessor
from Agent.bot import Bot


class AIReplyHandler(BaseHandler):
    """专注的AI回复处理器"""

    def __init__(self, bot: Bot = None, auto_reply_types: set = None):
        super().__init__("AIReplyHandler")
        # 从 DI 容器获取 CustomerAgent（如果未传入）
        if bot is None:
            try:
                from core.di_container import container
                from Agent.CustomerAgent.custom.customer_agent import CustomerAgent
                bot = container.get(CustomerAgent)
            except Exception as e:
                from utils.logger_loguru import get_logger
                get_logger("AIReplyHandler").warning(f"从DI容器获取CustomerAgent失败: {e}, 将使用无Bot模式")
        self.bot = bot
        self.preprocessor = MessagePreprocessor()
        self.auto_reply_types = auto_reply_types or {
            ContextType.TEXT,
            ContextType.GOODS_INQUIRY,
            ContextType.GOODS_SPEC,
            ContextType.ORDER_INFO,
            ContextType.IMAGE,
            ContextType.VIDEO,
            ContextType.EMOTION
        }

    def can_handle(self, context: Context) -> bool:
        """检查是否可以处理该消息"""
        # 支持多种消息类型
        return context.type in self.auto_reply_types

    async def handle(self, context: Context, metadata: Dict[str, Any]) -> bool:
        """处理AI回复"""
        from Message.metadata_observability import log_handler_observation

        log_handler_observation(self.logger, metadata, context, self.name)
        try:
            # 1. 预处理消息
            processed_content = self.preprocessor.process(context.content, context.type)

            # 2. 调用AI生成回复
            reply = await self._get_ai_reply(processed_content, context)
            if not reply:
                self.logger.warning("AI回复生成失败，使用备用回复")
                return await self._handle_fallback(context, metadata)

            # 3. 发送回复
            success = await self._send_reply(context, reply, metadata)
            if success:
                await self.log_message(context, "AI回复发送成功", f"reply_len={len(reply)}")
            else:
                self.logger.warning("AI回复发送失败")
                return await self._handle_fallback(context, metadata)

            return True

        except Exception as e:
            self.logger.error(f"AI回复处理失败: {e}")
            return await self._handle_fallback(context, metadata)

    async def _get_ai_reply(self, query: str, context: Context) -> Optional[str]:
        """获取AI回复"""
        if not self.bot:
            return None

        try:
            # 优先使用异步接口，其次回退到同步接口
            if hasattr(self.bot, 'async_reply'):
                res = await self.bot.async_reply(query, context)
                return getattr(res, 'content', str(res))
            elif hasattr(self.bot, 'reply'):
                res = self.bot.reply(query, context)
                return getattr(res, 'content', str(res))
            else:
                self.logger.warning("Bot不支持reply或async_reply方法")
                return None

        except Exception as e:
            self.logger.error(f"AI Bot调用失败: {e}")
            return None

    def _send_text_legacy(
        self,
        shop_id: str,
        user_id: str,
        from_uid: str,
        reply: str,
    ) -> bool:
        """Legacy：同步 SendMessage.send_text。"""
        from Channel.pinduoduo.utils.API.send_message import SendMessage

        sender = SendMessage(shop_id, user_id)
        result = sender.send_text(from_uid, reply)
        if isinstance(result, dict) and result.get("success"):
            return True
        return False

    async def _send_reply(self, context: Context, reply: str, metadata: Dict[str, Any]) -> bool:
        """发送回复（outbound-first，失败回退 legacy SendMessage）。"""
        try:
            from Message.handlers.outbound_resolver import (
                extract_pdd_send_context,
                resolve_pinduoduo_outbound,
            )
            from Message.handlers.unified_outbound_flags import use_unified_outbound_resolver

            shop_id, user_id, from_uid = extract_pdd_send_context(metadata, context)

            if not all([shop_id, user_id, from_uid]):
                from Message.log_sanitizer import format_send_context_log

                self.logger.warning(
                    "缺少发送信息: %s",
                    format_send_context_log(shop_id, user_id, from_uid),
                )
                return False

            if use_unified_outbound_resolver():
                from Message.handlers.unified_outbound_resolver import resolve_outbound

                outbound = resolve_outbound(metadata, context)
            else:
                outbound = resolve_pinduoduo_outbound(metadata, context)
            if outbound is not None:
                if await outbound.send_text(from_uid, reply):
                    return True
                self.logger.warning(
                    "PinduoduoOutbound.send_text 失败，回退 legacy SendMessage"
                )

            return self._send_text_legacy(shop_id, user_id, from_uid, reply)

        except Exception as e:
            self.logger.error(f"发送回复失败: {e}")
            return False

    async def _handle_fallback(self, context: Context, metadata: Dict[str, Any]) -> bool:
        """备用回复处理"""
        try:
            # 简单的自动回复
            reply_text = "亲，感谢您的咨询！客服正在为您处理，请稍等片刻。"

            # 记录备用回复
            self.logger.info("使用备用回复")

            # 尝试发送备用回复
            success = await self._send_reply(context, reply_text, metadata)
            if not success:
                # 如果发送失败，记录日志并返回False让下游有机会处理
                await self.log_message(context, "备用回复发送失败", f"reply_len={len(reply_text)}")
                return False

            await self.log_message(context, "备用回复发送成功", f"reply_len={len(reply_text)}")
            return True

        except Exception as e:
            self.logger.error(f"备用回复处理失败: {e}")
            return True  # 即使失败也返回True，避免重复处理
