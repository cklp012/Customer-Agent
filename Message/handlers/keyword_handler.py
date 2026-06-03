"""
关键词检测处理器 - 检测转人工关键词并触发转人工流程
"""
from typing import Dict, Any
from bridge.context import Context, ContextType
from .base import BaseHandler
from database.db_manager import db_manager
from utils.logger_loguru import get_logger
from Channel.pinduoduo.utils.API.send_message import SendMessage

class KeywordDetectionHandler(BaseHandler):
    """关键词检测处理器 - 检测转人工关键词并触发转人工流程"""

    def __init__(self):
        super().__init__("KeywordDetectionHandler")
        self.logger = get_logger("KeywordDetectionHandler")
        self.keywords = self._load_keywords()

        # 记录加载的关键词数量
        self.logger.info(f"关键词检测处理器初始化完成，加载了 {len(self.keywords)} 个关键词")

    def _load_keywords(self):
        """从数据库加载关键词"""
        try:
            keywords_data = db_manager.get_all_keywords()
            keywords = {item['keyword'].lower() for item in keywords_data if item.get('keyword')}
            self.logger.debug(f"从数据库加载关键词: {keywords}")
            return keywords
        except Exception as e:
            self.logger.error(f"加载关键词失败: {e}")
            # 如果加载失败，使用默认关键词
            default_keywords = {
                "转人工", "人工客服", "真人", "客服", "人工", "工单", "好评",
                "取消订单", "改地址", "转售后客服", "转售后", "返现", "过敏",
                "退款", "没有效果", "骗人", "投诉", "纠纷", "开发票", "开票",
                "烂", "取消", "备注"
            }
            self.logger.warning(f"使用默认关键词: {default_keywords}")
            return default_keywords

    def can_handle(self, context: Context) -> bool:
        """检查消息是否包含关键词"""
        # 只处理文本类型的消息
        if context.type != ContextType.TEXT:
            return False

        # 检查消息内容是否存在且为字符串
        if not context.content or not isinstance(context.content, str):
            return False

        # 将消息内容转换为小写进行检测
        content_lower = context.content.lower()

        # 检查是否包含任何关键词
        for keyword in self.keywords:
            if keyword in content_lower:
                self.logger.debug(f"检测到关键词: '{keyword}'")
                return True

        return False

    def _transfer_to_human_legacy(
        self,
        shop_id: str,
        user_id: str,
        from_uid: str,
    ) -> bool:
        """Legacy：同步 SendMessage 转人工（含无客服离线提示）。"""
        sender = SendMessage(shop_id, user_id)
        cs_list = sender.getAssignCsList()
        my_cs_uid = f"cs_{shop_id}_{user_id}"

        if cs_list and isinstance(cs_list, dict):
            available_cs_uids = [uid for uid in cs_list.keys() if uid != my_cs_uid]

            if available_cs_uids:
                cs_uid = available_cs_uids[0]
                target_cs = cs_list[cs_uid]
                cs_name = target_cs.get("username", "客服")

                transfer_result = sender.move_conversation(from_uid, cs_uid)

                if transfer_result and transfer_result.get("success"):
                    self.logger.info(f"会话已成功转接给 {cs_name} ({cs_uid})")
                    return True
                self.logger.error("会话转接失败")
            else:
                self.logger.warning("没有其他可用的客服进行转接")
                sender.send_text(
                    from_uid,
                    "抱歉，当前没有其他客服在线，请您稍后再试。",
                )

        return False

    async def handle(self, context: Context, metadata: Dict[str, Any]) -> bool:
        """转接到人工客服（outbound-first，失败回退 legacy）。"""
        from Message.metadata_observability import log_handler_observation

        log_handler_observation(self.logger, metadata, context, self.name)
        try:
            from Message.handlers.outbound_resolver import (
                extract_pdd_send_context,
                resolve_pinduoduo_outbound,
            )

            shop_id, user_id, from_uid = extract_pdd_send_context(metadata, context)

            if not all([shop_id, user_id, from_uid]):
                return False

            outbound = resolve_pinduoduo_outbound(metadata, context)
            if outbound is not None:
                if await outbound.transfer_to_human(from_uid, reason="keyword"):
                    return True
                self.logger.warning(
                    "PinduoduoOutbound.transfer_to_human 失败，回退 legacy 转人工"
                )

            return self._transfer_to_human_legacy(shop_id, user_id, from_uid)

        except Exception as e:
            self.logger.error(f"客服转接处理失败: {e}")
            return False
            
    def reload_keywords(self) -> None:
        """重新加载关键词（用于管理员更新关键词后刷新）"""
        old_count = len(self.keywords)
        self.keywords = self._load_keywords()
        new_count = len(self.keywords)
        self.logger.info(f"关键词重新加载完成: {old_count} -> {new_count}")

    def get_keyword_count(self) -> int:
        """获取当前关键词数量"""
        return len(self.keywords)

    def get_keywords(self) -> set:
        """获取当前关键词列表"""
        return self.keywords.copy()