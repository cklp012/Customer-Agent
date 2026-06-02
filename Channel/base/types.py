"""
多平台 Channel 基础类型。

PlatformType 字符串值与 bridge.context.ChannelType 对齐，便于 Phase 2+ 映射。
"""

from enum import Enum


class PlatformType(str, Enum):
    """电商平台 / 客服渠道类型"""

    # 与 bridge.context.ChannelType 一致
    PINDUODUO = "pinduoduo"
    JINGDONG = "jingdong"
    TAOBAO = "taobao"
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"

    # Phase 6b：契约验证用假平台，非生产；未接入 bridge.ChannelType / Message 链路
    DEMO = "demo"

    # 预留：后续 Adapter 接入时使用（当前运行时未使用）
    QIANNIU = "qianniu"
    DOUDIAN = "doudian"
    JINGMAI = "jingmai"
    XIAOHONGSHU = "xiaohongshu"
    WECHAT_SHOP = "wechat_shop"
    WECOM = "wecom"

    def __str__(self) -> str:
        return self.value


class ChannelStatus(str, Enum):
    """Channel 连接/会话状态（与 core.connection_status.ConnectionState 语义对齐）"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    LOGGING_IN = "logging_in"

    def __str__(self) -> str:
        return self.value
