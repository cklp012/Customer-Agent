"""Policy / Template validation service skeleton (Phase 14w) — no DB, no send."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Sequence, Union

from Message.gates.final_guard import scan_forbidden_promise

_MODE_RANK = {
    "blocked": 0,
    "guide_only": 1,
    "template_only": 2,
    "assisted_only": 3,
    "auto_allowed": 4,
}

_ALL_MODES = frozenset(_MODE_RANK)

_REDLINE_INTENT_CATEGORIES = frozenset(
    {
        "private_contact",
        "off_platform_payment",
        "review_cashback",
        "delete_bad_review",
        "platform_rule_dispute",
    }
)

_DEFAULT_PLATFORM_CEILING: dict[str, str] = {
    "private_contact": "blocked",
    "off_platform_payment": "blocked",
    "review_cashback": "blocked",
    "delete_bad_review": "blocked",
    "platform_rule_dispute": "blocked",
    "order_change": "guide_only",
    "address_change": "guide_only",
    "refund_request": "assisted_only",
    "compensation_request": "assisted_only",
    "gift_request": "assisted_only",
    "complaint": "assisted_only",
    "bad_review_threat": "assisted_only",
    "product_question": "auto_allowed",
    "size_or_spec_question": "auto_allowed",
    "inventory_question": "auto_allowed",
    "promotion_question": "assisted_only",
    "shipping_basic": "assisted_only",
}

_UNKNOWN_INTENT_CEILING = "assisted_only"

_ALLOWED_TEMPLATE_VARIABLES = frozenset(
    {
        "buyer_nick",
        "product_name",
        "order_id",
        "shop_name",
        "platform_after_sales_url",
    }
)

_SUSPICIOUS_TEMPLATE_PHRASES = (
    "我们会尽快帮您看看",
    "可以给您申请一下",
)


@dataclass(frozen=True)
class PolicyValidationResult:
    valid: bool
    effective_mode: str
    requested_mode: str
    platform_ceiling: str
    status: str
    reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TemplateValidationResult:
    validation_status: str
    reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    forbidden_category: Optional[str] = None
    forbidden_keyword: Optional[str] = None
    content_hash: Optional[str] = None


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _normalize_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized not in _ALL_MODES:
        raise ValueError(f"unknown ai_intervention_mode: {mode}")
    return normalized


def _mode_rank(mode: str) -> int:
    return _MODE_RANK[normalized] if (normalized := _normalize_mode(mode)) else -1


def _resolve_platform_ceiling(
    intent_category: str,
    platform_ceiling: Optional[str],
) -> str:
    if platform_ceiling is not None:
        return _normalize_mode(platform_ceiling)
    return _DEFAULT_PLATFORM_CEILING.get(intent_category, _UNKNOWN_INTENT_CEILING)


def _min_mode(*modes: str) -> str:
    return min(modes, key=_mode_rank)


def validate_policy_mode(
    intent_category: str,
    requested_mode: str,
    platform_ceiling: Optional[str] = None,
    shop_reply_mode_cap: Optional[str] = None,
) -> PolicyValidationResult:
    """Validate merchant policy mode against platform ceiling and shop cap."""
    requested = _normalize_mode(requested_mode)
    ceiling = _resolve_platform_ceiling(intent_category, platform_ceiling)
    warnings: List[str] = []

    if intent_category in _REDLINE_INTENT_CATEGORIES or ceiling == "blocked":
        if requested != "blocked":
            return PolicyValidationResult(
                valid=False,
                effective_mode="blocked",
                requested_mode=requested,
                platform_ceiling=ceiling,
                status="rejected",
                reason=(
                    f"红线 intent `{intent_category}` 不可放宽，"
                    "ai_intervention_mode 必须为 blocked"
                ),
                warnings=warnings,
            )
        return PolicyValidationResult(
            valid=True,
            effective_mode="blocked",
            requested_mode=requested,
            platform_ceiling=ceiling,
            status="passed",
            reason=None,
            warnings=warnings,
        )

    if _mode_rank(requested) > _mode_rank(ceiling):
        return PolicyValidationResult(
            valid=False,
            effective_mode=_min_mode(requested, ceiling),
            requested_mode=requested,
            platform_ceiling=ceiling,
            status="rejected",
            reason=(
                f"requested_mode `{requested}` 超过 platform_ceiling `{ceiling}`"
            ),
            warnings=warnings,
        )

    effective = _min_mode(requested, ceiling)
    if shop_reply_mode_cap is not None:
        cap = _normalize_mode(shop_reply_mode_cap)
        if _mode_rank(requested) > _mode_rank(cap):
            warnings.append(
                f"requested_mode `{requested}` 超过 shop_reply_mode_cap `{cap}`"
            )
        effective = _min_mode(effective, cap)

    return PolicyValidationResult(
        valid=True,
        effective_mode=effective,
        requested_mode=requested,
        platform_ceiling=ceiling,
        status="passed",
        reason=None,
        warnings=warnings,
    )


def _normalize_variable_names(
    variables: Union[Mapping[str, Any], Sequence[str], str, None],
) -> List[str]:
    if variables is None:
        return []
    if isinstance(variables, Mapping):
        return [str(key) for key in variables.keys()]
    if isinstance(variables, (list, tuple)):
        return [str(item) for item in variables]
    if isinstance(variables, str):
        stripped = variables.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [stripped]
        if isinstance(parsed, Mapping):
            return [str(key) for key in parsed.keys()]
        if isinstance(parsed, (list, tuple)):
            return [str(item) for item in parsed]
        return [stripped]
    return [str(variables)]


def _extract_forbidden_keyword(content: str, block_code: Optional[str]) -> Optional[str]:
    normalized = content.strip()
    pattern_groups = {
        "review_manipulation": (
            "好评返现",
            "删差评",
            "送你别差评",
        ),
        "off_platform_risk": (
            "加微信",
            "加我微信",
            "私下转账",
            "线下转账",
        ),
        "forbidden_promise": (
            "我给你退",
            "直接退款",
            "马上退款",
            "给你赔",
            "赔你",
            "补偿你",
            "我帮你改地址",
            "我帮你改订单",
            "一定今天到",
            "保证明天到",
            "肯定有货",
        ),
    }
    patterns = pattern_groups.get(block_code or "", ())
    for pattern in patterns:
        if pattern in normalized:
            return pattern
    return None


def validate_reply_template(
    content: str,
    intent_category: Optional[str] = None,
    variables: Union[Mapping[str, Any], Sequence[str], str, None] = None,
) -> TemplateValidationResult:
    """Validate template content and variable whitelist before save/enable."""
    _ = intent_category  # reserved for future category-specific rules
    content_hash = compute_content_hash(content or "")

    if not content or not content.strip():
        return TemplateValidationResult(
            validation_status="rejected",
            reason="模板内容为空",
            content_hash=content_hash,
        )

    normalized = content.strip()
    variable_names = _normalize_variable_names(variables)
    unknown_variables = [
        name for name in variable_names if name not in _ALLOWED_TEMPLATE_VARIABLES
    ]
    if unknown_variables:
        return TemplateValidationResult(
            validation_status="rejected",
            reason=f"模板变量不在白名单内: {', '.join(unknown_variables)}",
            content_hash=content_hash,
        )

    scan = scan_forbidden_promise(normalized)
    if scan.blocked:
        block_code = scan.block_code or "forbidden_promise"
        return TemplateValidationResult(
            validation_status="rejected",
            reason=scan.block_reason or "模板内容未通过禁诺扫描",
            forbidden_category=block_code,
            forbidden_keyword=_extract_forbidden_keyword(normalized, block_code),
            content_hash=content_hash,
        )

    warnings: List[str] = []
    for phrase in _SUSPICIOUS_TEMPLATE_PHRASES:
        if phrase in normalized:
            warnings.append(f"模板含待人工复核用语: {phrase}")
            return TemplateValidationResult(
                validation_status="pending_review",
                reason="模板含待人工复核用语，需运营确认后启用",
                warnings=warnings,
                content_hash=content_hash,
            )

    return TemplateValidationResult(
        validation_status="passed",
        reason=None,
        warnings=warnings,
        content_hash=content_hash,
    )
