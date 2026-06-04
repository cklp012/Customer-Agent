"""Phase 10d：compute_pdd_routing 与 pdd_message_handler immediate/queue 契约 parity。"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import FrozenSet

from bridge.context import ContextType
from Channel.pinduoduo.mappers.pdd_to_unified import (
    _IMMEDIATE_TYPES,
    _QUEUE_TYPES,
    compute_pdd_routing,
    pdd_message_to_unified,
)

# 与 Channel/pinduoduo/core/pdd_message_handler.py L138-159 保持同构（仅测试引用）
HANDLER_IMMEDIATE_TYPES: FrozenSet[ContextType] = frozenset(
    {
        ContextType.SYSTEM_STATUS,
        ContextType.AUTH,
        ContextType.WITHDRAW,
        ContextType.SYSTEM_HINT,
        ContextType.MALL_CS,
        ContextType.TRANSFER,
    }
)
HANDLER_QUEUE_TYPES: FrozenSet[ContextType] = frozenset(
    {
        ContextType.TEXT,
        ContextType.IMAGE,
        ContextType.VIDEO,
        ContextType.EMOTION,
        ContextType.GOODS_INQUIRY,
        ContextType.ORDER_INFO,
        ContextType.GOODS_CARD,
        ContextType.GOODS_SPEC,
    }
)

_VALID_ROUTING = frozenset({"immediate", "queue", "drop"})

_SHOP_ID = "parity_shop"
_USER_ID = "parity_user"
_USERNAME = "parity_cs"


def _synthetic_pdd(user_msg_type: ContextType) -> SimpleNamespace:
    """最小合成入站对象，满足 pdd_message_to_unified 字段读取。"""
    return SimpleNamespace(
        user_msg_type=user_msg_type,
        from_uid="buyer_uid_parity",
        nickname="buyer",
        from_user="user",
        to_user="mall_cs",
        to_uid="cs_uid_parity",
        msg_id=f"parity-{user_msg_type.value}",
        content="synthetic-content",
        raw_data={
            "response": "push",
            "message": {"msg_id": f"parity-{user_msg_type.value}", "time": 1717200000},
        },
        msg={
            "response": "push",
            "message": {"msg_id": f"parity-{user_msg_type.value}", "time": 1717200000},
        },
    )


class TestHandlerMapperSetParity(unittest.TestCase):
    def test_mapper_immediate_matches_handler(self) -> None:
        self.assertEqual(_IMMEDIATE_TYPES, HANDLER_IMMEDIATE_TYPES)

    def test_mapper_queue_matches_handler(self) -> None:
        self.assertEqual(_QUEUE_TYPES, HANDLER_QUEUE_TYPES)

    def test_immediate_and_queue_disjoint(self) -> None:
        overlap = HANDLER_IMMEDIATE_TYPES & HANDLER_QUEUE_TYPES
        self.assertEqual(overlap, frozenset())


class TestComputePddRoutingTable(unittest.TestCase):
    def test_every_context_type_has_valid_routing(self) -> None:
        for context_type in ContextType:
            routing = compute_pdd_routing(context_type)
            self.assertIn(routing, _VALID_ROUTING, msg=context_type.value)

    def test_routing_matches_handler_sets(self) -> None:
        for context_type in ContextType:
            routing = compute_pdd_routing(context_type)
            in_immediate = context_type in HANDLER_IMMEDIATE_TYPES
            in_queue = context_type in HANDLER_QUEUE_TYPES

            if in_immediate:
                self.assertEqual(routing, "immediate", msg=context_type.value)
            elif in_queue:
                self.assertEqual(routing, "queue", msg=context_type.value)
            else:
                self.assertEqual(routing, "drop", msg=context_type.value)

            self.assertFalse(in_immediate and in_queue, msg=context_type.value)


class TestDropExamples(unittest.TestCase):
    def test_mall_system_msg_is_drop(self) -> None:
        self.assertEqual(compute_pdd_routing(ContextType.MALL_SYSTEM_MSG), "drop")

    def test_system_biz_is_drop(self) -> None:
        self.assertEqual(compute_pdd_routing(ContextType.SYSTEM_BIZ), "drop")


class TestSyntheticMapperRouting(unittest.TestCase):
    def test_mapper_content_type_and_routing_per_context_type(self) -> None:
        for context_type in ContextType:
            pdd = _synthetic_pdd(context_type)
            unified = pdd_message_to_unified(
                pdd,
                shop_id=_SHOP_ID,
                user_id=_USER_ID,
                username=_USERNAME,
            )
            self.assertEqual(
                unified.content_type,
                context_type.value,
                msg=context_type.value,
            )
            self.assertEqual(
                unified.conversation.extra["routing"],
                compute_pdd_routing(context_type),
                msg=context_type.value,
            )


if __name__ == "__main__":
    unittest.main()
