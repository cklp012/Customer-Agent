"""Phase 13e: preview ReplyLog projection unit tests."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from Message.gates.consultation_intent_classifier import classify_consultation_intent
from Message.gates.guarded_send import evaluate_guarded_send
from Message.gates.intent_types import IntentBucket, SendMode
from Message.gates.preview_log import append_preview_log, preview_log
from Message.gates.reply_log_projection import (
    PreviewReplyLogListItem,
    build_not_sent_explanation,
    list_preview_reply_logs,
    project_preview_record_to_reply_log,
)
from Message.gates.send_decision import build_send_decision


class TestPreviewReplyLogProjection(unittest.TestCase):
    def setUp(self) -> None:
        preview_log.clear()

    def tearDown(self) -> None:
        preview_log.clear()

    def _append_allowed(self) -> None:
        cls = classify_consultation_intent("这款商品还有库存吗")
        decision = build_send_decision(cls, reply_mode="preview", product_gate_enabled=True)
        guarded = evaluate_guarded_send(decision, "建议回复")
        append_preview_log(
            message_text="这款商品还有库存吗",
            reply_text="建议回复",
            classification=cls,
            send_decision=decision,
            guarded_result=guarded,
            metadata={
                "workspace_id": "ws-1",
                "shop_id": "shop-1",
                "account_id": "acc-1",
                "from_uid": "buyer-1",
                "platform_id": "pinduoduo",
            },
        )

    def _append_blocked(self) -> None:
        cls = classify_consultation_intent("我要退款")
        decision = build_send_decision(cls, reply_mode="preview", product_gate_enabled=True)
        guarded = evaluate_guarded_send(decision, "不应发送")
        append_preview_log(
            message_text="我要退款",
            reply_text="不应发送",
            classification=cls,
            send_decision=decision,
            guarded_result=guarded,
            metadata={
                "workspace_id": "ws-1",
                "shop_id": "shop-1",
                "account_id": "acc-1",
                "from_uid": "buyer-2",
                "platform_id": "pinduoduo",
            },
        )

    def test_allowed_preview_send_status(self) -> None:
        self._append_allowed()
        item = list_preview_reply_logs()[0]
        self.assertEqual(item.send_status, "not_sent_preview")
        self.assertEqual(item.send_mode, SendMode.PREVIEW_ONLY.value)

    def test_blocked_refund_human_takeover(self) -> None:
        self._append_blocked()
        item = list_preview_reply_logs()[0]
        self.assertEqual(item.send_status, "not_sent_human_takeover")
        self.assertEqual(item.send_mode, SendMode.HUMAN_TAKEOVER.value)
        self.assertEqual(item.intent_bucket, IntentBucket.BLOCKED.value)

    def test_projection_includes_intent_fields(self) -> None:
        self._append_allowed()
        item = list_preview_reply_logs()[0]
        self.assertTrue(item.intent)
        self.assertEqual(item.intent_bucket, IntentBucket.ALLOWED.value)
        self.assertGreater(item.intent_confidence, 0.0)
        self.assertIn(item.risk_level, ("low", "medium", "high"))

    def test_projection_includes_shop_account_buyer(self) -> None:
        self._append_allowed()
        item = list_preview_reply_logs()[0]
        self.assertEqual(item.shop_id, "shop-1")
        self.assertEqual(item.account_id, "acc-1")
        self.assertEqual(item.buyer_id, "buyer-1")
        self.assertEqual(item.platform_id, "pinduoduo")
        self.assertEqual(item.workspace_id, "ws-1")

    def test_not_sent_explanation_differs(self) -> None:
        self._append_allowed()
        self._append_blocked()
        items = list_preview_reply_logs()
        preview_expl = items[0].not_sent_explanation
        blocked_expl = items[1].not_sent_explanation
        self.assertIn("Preview mode", preview_expl)
        self.assertIn("Human takeover", blocked_expl)
        self.assertNotEqual(preview_expl, blocked_expl)

    def test_clear_empties_list(self) -> None:
        self._append_allowed()
        self.assertEqual(len(list_preview_reply_logs()), 1)
        preview_log.clear()
        self.assertEqual(list_preview_reply_logs(), [])

    def test_module_does_not_import_send_paths(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "Message"
            / "gates"
            / "reply_log_projection.py"
        )
        with open(source_path, encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("from Channel.pinduoduo.utils.API.send_message", source)
        self.assertNotIn("import SendMessage", source)
        self.assertNotIn("outbound_resolver", source)

    def test_missing_fields_safe_degradation(self) -> None:
        broken = MagicMock()
        broken.message_text = "hello"
        broken.reply_text = "world"
        broken.metadata = {}
        broken.created_at = ""
        broken.reply_log_id = ""
        broken.workspace_id = None
        broken.platform_id = None
        broken.shop_id = None
        broken.account_id = None
        broken.buyer_id = None
        broken.send_status = ""
        broken.send_mode = ""
        broken.blocked_reason = None
        broken.human_takeover_reason = None
        broken.classification = MagicMock(side_effect=RuntimeError("boom"))
        broken.send_decision = MagicMock()
        broken.guarded_result = MagicMock(send_status="not_sent_preview")

        item = project_preview_record_to_reply_log(broken)
        self.assertIsInstance(item, PreviewReplyLogListItem)
        self.assertEqual(item.buyer_message, "hello")
        self.assertEqual(item.ai_suggested_reply, "world")

    def test_build_not_sent_explanation_preview(self) -> None:
        text = build_not_sent_explanation(
            send_status="not_sent_preview",
            send_mode="preview_only",
            blocked_reason="preview_mode",
            human_takeover_reason=None,
        )
        self.assertIn("Preview mode", text)


if __name__ == "__main__":
    unittest.main()
