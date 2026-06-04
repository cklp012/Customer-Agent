"""Phase 10g Route B：pdd_queue_name 与历史 f"pdd_{shop_id}" parity（不接入 lifecycle）。"""

from __future__ import annotations

import unittest

from Message.queue_naming import pdd_queue_name

# 正常 shop_id 样本（与 DB / AutoReply 常见形态一致）
_REPRESENTATIVE_SHOP_IDS = (
    "S1",
    "123",
    123,
    "shop-abc",
    "店铺001",
)


class TestPddQueueNameLegacyParity(unittest.TestCase):
    """
    pdd_queue_name 是未来接入 pdd_lifecycle 的候选 helper。
    本阶段不修改 Channel/pinduoduo/core/pdd_lifecycle.py。
    """

    def test_matches_fstring_for_normal_shop_ids(self) -> None:
        for shop_id in _REPRESENTATIVE_SHOP_IDS:
            expected = f"pdd_{shop_id}"
            self.assertEqual(
                pdd_queue_name(shop_id),
                expected,
                msg=f"shop_id={shop_id!r}",
            )

    def test_explicit_string_and_int(self) -> None:
        self.assertEqual(pdd_queue_name("123"), "pdd_123")
        self.assertEqual(pdd_queue_name(123), "pdd_123")


class TestPddQueueNameInvalidShopId(unittest.TestCase):
    """None / 空 shop_id：helper 抛 ValueError，不与 legacy f-string 对齐。"""

    def test_none_raises(self) -> None:
        with self.assertRaises(ValueError):
            pdd_queue_name(None)
        # 历史 f-string 会生成 "pdd_None"；helper 拒绝以避免脏队列名

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            pdd_queue_name("")
        # 历史 f-string 会生成 "pdd_"

    def test_whitespace_only_raises(self) -> None:
        with self.assertRaises(ValueError):
            pdd_queue_name("   ")


if __name__ == "__main__":
    unittest.main()
