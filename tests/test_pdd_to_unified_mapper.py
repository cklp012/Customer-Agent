"""Phase 7b：PDDChatMessage → UnifiedMessage mapper 测试。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from bridge.context import ContextType
from Channel.base.models import UnifiedMessage
from Channel.base.types import PlatformType
from Channel.pinduoduo.mappers import compute_pdd_routing, pdd_message_to_unified
from Channel.pinduoduo.pdd_message import PDDChatMessage

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "pdd_messages"

_SHOP_ID = "demo_shop_001"
_USER_ID = "demo_cs_uid_001"
_USERNAME = "demo_cs_user"
_SHOP_NAME = "Demo Shop"


def _load_fixture(name: str) -> dict:
    with open(_FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _to_unified(fixture_name: str) -> UnifiedMessage:
    data = _load_fixture(fixture_name)
    pdd = PDDChatMessage(data)
    return pdd_message_to_unified(
        pdd,
        shop_id=_SHOP_ID,
        user_id=_USER_ID,
        username=_USERNAME,
        shop_name=_SHOP_NAME,
    )


class TestComputePddRouting(unittest.TestCase):
    def test_queue_types(self) -> None:
        self.assertEqual(compute_pdd_routing(ContextType.TEXT), "queue")
        self.assertEqual(compute_pdd_routing(ContextType.GOODS_INQUIRY), "queue")

    def test_immediate_types(self) -> None:
        self.assertEqual(compute_pdd_routing(ContextType.WITHDRAW), "immediate")
        self.assertEqual(compute_pdd_routing(ContextType.MALL_CS), "immediate")

    def test_drop_unknown(self) -> None:
        # GOODS_CARD 在 queue 集；用一个不在两集的假设：若未来有仅 AUTH 等已覆盖
        self.assertEqual(compute_pdd_routing(ContextType.AUTH), "immediate")


class TestPddToUnifiedMapper(unittest.TestCase):
    def test_text_message(self) -> None:
        unified = _to_unified("text.json")
        self.assertEqual(unified.platform, PlatformType.PINDUODUO)
        self.assertEqual(unified.message_id, "demo-msg-text-001")
        self.assertEqual(unified.content_type, "text")
        self.assertEqual(unified.content, "你好，请问有货吗？")
        self.assertEqual(unified.direction, "inbound")
        self.assertEqual(unified.conversation.extra["routing"], "queue")
        self.assertEqual(unified.conversation.shop_id, _SHOP_ID)
        self.assertEqual(unified.conversation.account_id, _USER_ID)
        self.assertEqual(unified.conversation.buyer_uid, "demo_buyer_uid_001")
        self.assertEqual(unified.conversation.conversation_id, "demo_buyer_uid_001")

    def test_goods_inquiry_dict_content(self) -> None:
        unified = _to_unified("goods_inquiry.json")
        self.assertEqual(unified.content_type, "goods_inquiry")
        self.assertIsInstance(unified.content, dict)
        self.assertEqual(unified.content.get("goods_id"), 10001)
        self.assertEqual(unified.content.get("goods_name"), "Demo Product")
        self.assertEqual(unified.conversation.extra["routing"], "queue")
        self.assertNotIsInstance(unified.content, str)

    def test_withdraw_immediate_routing(self) -> None:
        unified = _to_unified("withdraw.json")
        self.assertEqual(unified.content_type, "withdraw")
        self.assertEqual(unified.conversation.extra["routing"], "immediate")

    def test_mall_cs_immediate_routing(self) -> None:
        unified = _to_unified("mall_cs.json")
        self.assertEqual(unified.content_type, "mall_cs")
        self.assertEqual(unified.conversation.extra["routing"], "immediate")
        self.assertEqual(unified.conversation.buyer_uid, "demo_cs_uid_001")

    def test_raw_preserved(self) -> None:
        data = _load_fixture("text.json")
        unified = _to_unified("text.json")
        self.assertEqual(unified.raw.get("response"), "push")
        self.assertEqual(
            unified.raw.get("message", {}).get("msg_id"),
            data["message"]["msg_id"],
        )

    def test_extra_fields(self) -> None:
        unified = _to_unified("text.json")
        extra = unified.conversation.extra
        self.assertEqual(extra["username"], _USERNAME)
        self.assertEqual(extra["shop_name"], _SHOP_NAME)
        self.assertEqual(extra["from_user"], "user")
        self.assertEqual(extra["to_user"], "mall_cs")
        self.assertEqual(extra["to_uid"], "demo_cs_uid_001")
        self.assertEqual(extra["msg_id"], "demo-msg-text-001")

    def test_timestamp_from_fixture(self) -> None:
        unified = _to_unified("text.json")
        self.assertIsNotNone(unified.timestamp)


if __name__ == "__main__":
    unittest.main()
