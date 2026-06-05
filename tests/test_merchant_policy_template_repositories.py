"""Phase 14u: MerchantSafetyPolicy / MerchantReplyTemplate repository tests."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import MerchantReplyTemplateRow, MerchantSafetyPolicyRow
from product_persistence.repositories.sqlite_merchant_policy_repository import (
    MerchantPolicyRepositorySQLite,
)
from product_persistence.repositories.sqlite_reply_template_repository import (
    MerchantReplyTemplateRepositorySQLite,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPO_SOURCES = (
    _REPO_ROOT
    / "product_persistence"
    / "repositories"
    / "sqlite_merchant_policy_repository.py",
    _REPO_ROOT
    / "product_persistence"
    / "repositories"
    / "sqlite_reply_template_repository.py",
)


def _policy_kwargs(**overrides) -> dict:
    base = dict(
        workspace_id="ws-u-1",
        shop_id="shop-u-1",
        intent_category="stock_inquiry",
        ai_intervention_mode="assisted_only",
        platform_mode_ceiling="assisted_only",
        allowed_template_ids=("tpl-1", "tpl-2"),
        forbidden_keywords_extra=("私联",),
    )
    base.update(overrides)
    return base


def _template_kwargs(**overrides) -> dict:
    base = dict(
        workspace_id="ws-u-1",
        shop_id="shop-u-1",
        intent_category="stock_inquiry",
        title="库存回复",
        content="您好，该商品目前有货。",
        variables={"product_name": "示例商品"},
        validation_status="pending_review",
        validation_warnings=("placeholder",),
    )
    base.update(overrides)
    return base


class _RepositoryTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14u_repo_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_repo_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE",
            "PRODUCT_PERSISTENCE_READ_MERCHANT_POLICY",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_LOG",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
            "PRODUCT_PERSISTENCE_READ_DASHBOARD",
            "PRODUCT_DB_URL",
        ):
            os.environ.pop(key, None)
        importlib.reload(importlib.import_module("product_persistence.flags"))

    def tearDown(self) -> None:
        if self._db_manager is not None:
            self._db_manager.close_product_db()
        reset_product_db_manager()
        if self._db_path.exists():
            self._db_path.unlink(missing_ok=True)
        self._env_patch.stop()

    def _enable_flags(
        self,
        *,
        policy: bool = True,
        template: bool = True,
    ) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        if policy:
            os.environ["PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY"] = "true"
        if template:
            os.environ["PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager


class TestMerchantPolicyTemplateRepositories(_RepositoryTestCase):
    def test_flags_off_session_not_available(self) -> None:
        policy_repo = MerchantPolicyRepositorySQLite(
            db_manager=ProductDbManager(db_url=f"sqlite:///{self._db_path.as_posix()}")
        )
        template_repo = MerchantReplyTemplateRepositorySQLite(
            db_manager=ProductDbManager(db_url=f"sqlite:///{self._db_path.as_posix()}")
        )
        with self.assertRaises(NotImplementedError):
            policy_repo.create_policy(**_policy_kwargs())
        with self.assertRaises(NotImplementedError):
            template_repo.create_template(**_template_kwargs())

    def test_create_get_list_policy(self) -> None:
        db = self._enable_flags(policy=True, template=False)
        repo = MerchantPolicyRepositorySQLite(db_manager=db)
        policy_id = repo.create_policy(**_policy_kwargs())
        item = repo.get_policy(policy_id)
        assert item is not None
        self.assertEqual(item.policy_id, policy_id)
        self.assertEqual(item.policy_version, 1)
        self.assertEqual(item.allowed_template_ids, ("tpl-1", "tpl-2"))
        found = repo.find_policy("ws-u-1", "shop-u-1", "stock_inquiry")
        assert found is not None
        self.assertEqual(found.policy_id, policy_id)
        listed = repo.list_policies(workspace_id="ws-u-1", enabled=True)
        self.assertEqual(len(listed), 1)

    def test_update_policy_increments_version(self) -> None:
        db = self._enable_flags(policy=True, template=False)
        repo = MerchantPolicyRepositorySQLite(db_manager=db)
        policy_id = repo.create_policy(**_policy_kwargs())
        ok = repo.update_policy(policy_id, ai_intervention_mode="template_only")
        self.assertTrue(ok)
        item = repo.get_policy(policy_id)
        assert item is not None
        self.assertEqual(item.policy_version, 2)
        self.assertEqual(item.ai_intervention_mode, "template_only")

    def test_disable_policy_sets_enabled_zero(self) -> None:
        db = self._enable_flags(policy=True, template=False)
        repo = MerchantPolicyRepositorySQLite(db_manager=db)
        policy_id = repo.create_policy(**_policy_kwargs())
        ok = repo.disable_policy(policy_id)
        self.assertTrue(ok)
        session = db.get_product_session()
        try:
            row = session.get(MerchantSafetyPolicyRow, policy_id)
            assert row is not None
            self.assertEqual(row.enabled, 0)
        finally:
            session.close()

    def test_duplicate_policy_id_raises(self) -> None:
        db = self._enable_flags(policy=True, template=False)
        repo = MerchantPolicyRepositorySQLite(db_manager=db)
        policy_id = repo.create_policy(**_policy_kwargs(policy_id="policy-dup-1"))
        with self.assertRaises(ValueError):
            repo.create_policy(**_policy_kwargs(policy_id="policy-dup-1"))

    def test_create_get_list_template(self) -> None:
        db = self._enable_flags(policy=False, template=True)
        repo = MerchantReplyTemplateRepositorySQLite(db_manager=db)
        template_id = repo.create_template(**_template_kwargs())
        item = repo.get_template(template_id)
        assert item is not None
        self.assertEqual(item.template_id, template_id)
        self.assertEqual(item.template_version, 1)
        self.assertEqual(item.validation_status, "pending_review")
        listed = repo.list_templates(
            workspace_id="ws-u-1",
            intent_category="stock_inquiry",
            validation_status="pending_review",
        )
        self.assertEqual(len(listed), 1)

    def test_update_template_increments_version_and_content_hash(self) -> None:
        db = self._enable_flags(policy=False, template=True)
        repo = MerchantReplyTemplateRepositorySQLite(db_manager=db)
        template_id = repo.create_template(**_template_kwargs())
        new_content = "您好，库存充足，欢迎下单。"
        ok = repo.update_template(template_id, content=new_content)
        self.assertTrue(ok)
        item = repo.get_template(template_id)
        assert item is not None
        self.assertEqual(item.template_version, 2)
        self.assertEqual(item.content, new_content)
        expected_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
        self.assertEqual(item.content_hash, expected_hash)

    def test_disable_template_sets_enabled_zero(self) -> None:
        db = self._enable_flags(policy=False, template=True)
        repo = MerchantReplyTemplateRepositorySQLite(db_manager=db)
        template_id = repo.create_template(**_template_kwargs())
        ok = repo.disable_template(template_id)
        self.assertTrue(ok)
        session = db.get_product_session()
        try:
            row = session.get(MerchantReplyTemplateRow, template_id)
            assert row is not None
            self.assertEqual(row.enabled, 0)
        finally:
            session.close()

    def test_json_text_fields_roundtrip(self) -> None:
        db = self._enable_flags(policy=True, template=True)
        policy_repo = MerchantPolicyRepositorySQLite(db_manager=db)
        template_repo = MerchantReplyTemplateRepositorySQLite(db_manager=db)
        policy_id = policy_repo.create_policy(**_policy_kwargs())
        template_id = template_repo.create_template(**_template_kwargs())
        session = db.get_product_session()
        try:
            policy_row = session.get(MerchantSafetyPolicyRow, policy_id)
            template_row = session.get(MerchantReplyTemplateRow, template_id)
            assert policy_row is not None
            assert template_row is not None
            self.assertEqual(json.loads(policy_row.allowed_template_ids), ["tpl-1", "tpl-2"])
            self.assertEqual(json.loads(policy_row.forbidden_keywords_extra), ["私联"])
            self.assertEqual(
                json.loads(template_row.variables),
                {"product_name": "示例商品"},
            )
            self.assertEqual(json.loads(template_row.validation_warnings), ["placeholder"])
        finally:
            session.close()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_repository_no_send_side_effect(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        db = self._enable_flags(policy=True, template=True)
        policy_repo = MerchantPolicyRepositorySQLite(db_manager=db)
        template_repo = MerchantReplyTemplateRepositorySQLite(db_manager=db)
        policy_id = policy_repo.create_policy(**_policy_kwargs())
        template_id = template_repo.create_template(**_template_kwargs())
        policy_repo.update_policy(policy_id, allow_auto_reply=True)
        template_repo.update_template(template_id, validation_status="passed")
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()

    def test_repository_does_not_import_send_or_legacy(self) -> None:
        for path in _REPO_SOURCES:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("SendMessage", source)
            self.assertNotIn("Message.handlers", source)
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)

    def test_db_failure_raises_no_send(self) -> None:
        db = self._enable_flags(policy=True, template=False)
        repo = MerchantPolicyRepositorySQLite(db_manager=db)
        repo.create_policy(**_policy_kwargs(policy_id="policy-fail-1"))
        with self.assertRaises(ValueError):
            repo.create_policy(**_policy_kwargs(policy_id="policy-fail-1"))


if __name__ == "__main__":
    unittest.main()
