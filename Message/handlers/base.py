"""
处理器基类和通用工具
"""
from typing import Optional
from bridge.context import Context
from Message.log_sanitizer import content_length, format_message_type, format_user_ref
from ..core.handlers import MessageHandler



class BaseHandler(MessageHandler):
    """处理器基类，提供通用功能"""

    def __init__(self, name: Optional[str] = None):
        super().__init__()
        self.name = name or self.__class__.__name__

    async def log_message(self, context: Context, action: str, extra_info: str = ""):
        """统一的日志记录（不记录完整内容以保护隐私）"""
        user_ref = self._get_user_info(context)
        msg_type = format_message_type(context)
        length = content_length(context.content)
        suffix = f" {extra_info}" if extra_info else ""
        self.logger.info(
            f"{self.name} {action} - {user_ref} - type={msg_type} content_len={length}{suffix}"
        )

    def _get_user_info(self, context: Context) -> str:
        """提取脱敏用户引用。"""
        return format_user_ref(context)
