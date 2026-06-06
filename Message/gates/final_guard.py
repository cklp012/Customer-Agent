"""
Final Guard pure function (Phase 14v).

Decision-only — no platform send API, outbound, DB, or handler integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from Message.gates.intent_types import BLOCKED_INTENTS

_ASSISTED_SEND_ROLES = frozenset({"operator", "admin", "owner"})
_AUTO_SEND_ROLES = frozenset({"system", None})
_VALID_REPLY_MODES = frozenset({"assisted", "auto"})
_VALID_PENDING_STATUSES = frozenset({"pending", "approved"})
_HIGH_RISK_LEVELS = frozenset({"high", "critical"})
_STALE_INBOUND_SECONDS = 3600

_MODE_RANK = {
    "blocked": 0,
    "guide_only": 1,
    "template_only": 2,
    "assisted_only": 3,
    "auto_allowed": 4,
}

_SAFE_PLATFORM_GUIDANCE_PHRASES = (
    "请通过平台售后入口申请退款",
    "按照平台流程处理",
    "赠品以活动页面显示为准",
    "地址修改请通过平台订单页面操作",
)

_PLATFORM_GUIDANCE_MARKERS = (
    "平台售后",
    "售后入口",
    "平台流程",
    "活动页面",
    "订单页面",
    "平台规则",
    "平台客服",
    "平台显示",
)

_REVIEW_MANIPULATION_PATTERNS = (
    "好评返现",
    "删差评",
    "送你别差评",
)

_OFF_PLATFORM_PATTERNS = (
    "加微信",
    "加我微信",
    "私下转账",
    "线下转账",
)

_FORBIDDEN_PROMISE_PATTERNS = (
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
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@dataclass(frozen=True)
class ForbiddenScanResult:
    blocked: bool
    block_code: Optional[str] = None
    block_reason: Optional[str] = None


@dataclass
class FinalGuardInput:
    product_gate_enabled: bool = False
    workspace_pause: bool = False
    shop_pause: bool = False
    idempotency_consumed: bool = False
    workspace_id: Optional[str] = None
    shop_id: Optional[str] = None
    account_id: Optional[str] = None
    platform_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    actor_role: Optional[str] = None
    reply_log_id: Optional[str] = None
    pending_assisted_id: Optional[str] = None
    buyer_id: Optional[str] = None
    inbound_message_id: Optional[str] = None
    buyer_message: Optional[str] = None
    ai_suggested_reply: Optional[str] = None
    merchant_edited_reply: Optional[str] = None
    final_reply: Optional[str] = None
    intent_category: Optional[str] = None
    intent: Optional[str] = None
    intent_bucket: Optional[str] = None
    intent_confidence: Optional[float] = None
    risk_level: Optional[str] = None
    blocked_reason: Optional[str] = None
    human_takeover_reason: Optional[str] = None
    policy_id: Optional[str] = None
    policy_version: Optional[int] = None
    ai_intervention_mode: Optional[str] = None
    effective_mode: Optional[str] = None
    platform_mode_ceiling: Optional[str] = None
    template_id: Optional[str] = None
    template_version: Optional[int] = None
    template_validation_status: Optional[str] = None
    reply_mode: Optional[str] = None
    pending_status: Optional[str] = None
    expires_at: Optional[str] = None
    inbound_created_at: Optional[str] = None
    outbound_channel_status: Optional[str] = None
    idempotency_key: Optional[str] = None
    now: Optional[str] = None


@dataclass
class FinalGuardResult:
    allowed_to_send: bool
    decision: str
    block_code: Optional[str]
    block_reason: Optional[str]
    audit_action: str
    send_mode: str
    decision_source: str = "final_guard"
    checked_rules: List[str] = field(default_factory=list)
    policy_snapshot: Dict[str, Any] = field(default_factory=dict)
    template_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


def scan_forbidden_promise(text: Optional[str]) -> ForbiddenScanResult:
    """Scan final reply text for redline forbidden content."""
    if text is None or not str(text).strip():
        return ForbiddenScanResult(blocked=False)

    normalized = str(text).strip()

    for pattern in _REVIEW_MANIPULATION_PATTERNS:
        if pattern in normalized:
            return ForbiddenScanResult(
                blocked=True,
                block_code="review_manipulation",
                block_reason=f"回复含评价操纵用语：{pattern}",
            )

    for pattern in _OFF_PLATFORM_PATTERNS:
        if pattern in normalized:
            return ForbiddenScanResult(
                blocked=True,
                block_code="off_platform_risk",
                block_reason=f"回复含私联/绕平台风险用语：{pattern}",
            )

    for safe in _SAFE_PLATFORM_GUIDANCE_PHRASES:
        if safe in normalized:
            return ForbiddenScanResult(blocked=False)

    for pattern in _FORBIDDEN_PROMISE_PATTERNS:
        if pattern in normalized:
            return ForbiddenScanResult(
                blocked=True,
                block_code="forbidden_promise",
                block_reason=f"回复含不允许的承诺用语：{pattern}",
            )

    return ForbiddenScanResult(blocked=False)


def _is_platform_guidance(text: Optional[str]) -> bool:
    if text is None or not str(text).strip():
        return False
    normalized = str(text).strip()
    if any(safe in normalized for safe in _SAFE_PLATFORM_GUIDANCE_PHRASES):
        return True
    if not any(marker in normalized for marker in _PLATFORM_GUIDANCE_MARKERS):
        return False
    return not scan_forbidden_promise(normalized).blocked


def _mode_rank(mode: Optional[str]) -> int:
    if mode is None:
        return -1
    return _MODE_RANK.get(mode, -1)


def _build_policy_snapshot(ctx: FinalGuardInput) -> Dict[str, Any]:
    return {
        "policy_id": ctx.policy_id,
        "policy_version": ctx.policy_version,
        "intent_category": ctx.intent_category,
        "ai_intervention_mode": ctx.ai_intervention_mode,
        "effective_mode": ctx.effective_mode,
        "platform_mode_ceiling": ctx.platform_mode_ceiling,
    }


def _build_template_snapshot(ctx: FinalGuardInput) -> Dict[str, Any]:
    return {
        "template_id": ctx.template_id,
        "template_version": ctx.template_version,
        "validation_status": ctx.template_validation_status,
        "intent_category": ctx.intent_category,
    }


def _block(
    ctx: FinalGuardInput,
    *,
    rule_id: str,
    block_code: str,
    block_reason: str,
    checked_rules: List[str],
    created_at: str,
) -> FinalGuardResult:
    checked = list(checked_rules)
    if rule_id not in checked:
        checked.append(rule_id)
    return FinalGuardResult(
        allowed_to_send=False,
        decision="block",
        block_code=block_code,
        block_reason=block_reason,
        audit_action="final_guard_blocked",
        send_mode="none",
        checked_rules=checked,
        policy_snapshot=_build_policy_snapshot(ctx),
        template_snapshot=_build_template_snapshot(ctx),
        created_at=created_at,
    )


def _allow(
    ctx: FinalGuardInput,
    *,
    send_mode: str,
    checked_rules: List[str],
    created_at: str,
) -> FinalGuardResult:
    return FinalGuardResult(
        allowed_to_send=True,
        decision="allow",
        block_code=None,
        block_reason=None,
        audit_action="final_guard_passed",
        send_mode=send_mode,
        checked_rules=list(checked_rules),
        policy_snapshot=_build_policy_snapshot(ctx),
        template_snapshot=_build_template_snapshot(ctx),
        created_at=created_at,
    )


def _is_pending_expired(expires_at: Optional[str], now: str) -> bool:
    if not expires_at:
        return False
    return _parse_iso(now) > _parse_iso(expires_at)


def _is_stale_inbound(inbound_created_at: Optional[str], now: str) -> bool:
    if not inbound_created_at:
        return False
    delta = _parse_iso(now) - _parse_iso(inbound_created_at)
    return delta.total_seconds() > _STALE_INBOUND_SECONDS


def _is_unsafe_intent(ctx: FinalGuardInput) -> bool:
    if ctx.intent_bucket == "blocked":
        return True
    if ctx.intent and ctx.intent in BLOCKED_INTENTS:
        return True
    if ctx.intent_category and ctx.intent_category in BLOCKED_INTENTS:
        return True
    return False


def _evaluate_final_guard_inner(ctx: FinalGuardInput) -> FinalGuardResult:
    checked: List[str] = []
    created_at = ctx.now or _utc_now_iso()
    reply_mode = (ctx.reply_mode or "").lower()

    def fail(rule_id: str, block_code: str, block_reason: str) -> FinalGuardResult:
        return _block(
            ctx,
            rule_id=rule_id,
            block_code=block_code,
            block_reason=block_reason,
            checked_rules=checked,
            created_at=created_at,
        )

    checked.append("G1")
    if not ctx.product_gate_enabled:
        return fail("G1", "product_gate_disabled", "产品门控未启用，禁止发送")

    checked.append("G2")
    if reply_mode not in _VALID_REPLY_MODES:
        return fail("G2", "invalid_reply_mode", "回复模式不允许发送")

    checked.append("G3")
    if ctx.workspace_pause:
        return fail("G3", "workspace_paused", "工作区已暂停，禁止发送")

    checked.append("G4")
    if ctx.shop_pause:
        return fail("G4", "shop_paused", "店铺已暂停，禁止发送")

    checked.append("G5")
    if reply_mode == "assisted":
        role = (ctx.actor_role or "").lower() if ctx.actor_role else None
        if role not in _ASSISTED_SEND_ROLES:
            return fail("G5", "permission_denied", "当前角色无权执行 assisted 发送")

    checked.append("G7")
    if ctx.effective_mode == "blocked":
        return fail("G7", "policy_blocked", "商家策略禁止该类咨询自动/辅助发送")

    checked.append("G8")
    if ctx.effective_mode == "guide_only" and not _is_platform_guidance(ctx.final_reply):
        return fail("G8", "mode_violation", "guide_only 模式仅允许平台引导话术")

    checked.append("G9")
    if ctx.effective_mode == "template_only" and not ctx.template_id:
        return fail("G9", "template_required", "template_only 模式必须指定已验证模板")

    checked.append("G10")
    if ctx.template_id and ctx.template_validation_status != "passed":
        return fail("G10", "template_not_validated", "模板未通过安全校验")

    checked.append("G11")
    if ctx.effective_mode == "assisted_only" and reply_mode == "auto":
        return fail("G11", "assisted_approval_required", "assisted_only 模式不允许 auto 发送")

    checked.append("G12")
    if reply_mode == "auto":
        ceiling = ctx.platform_mode_ceiling or ctx.effective_mode
        if _mode_rank(ceiling) < _mode_rank("auto_allowed"):
            return fail("G12", "ceiling_violation", "平台模式上限不允许 auto 发送")
        if ctx.effective_mode != "auto_allowed":
            return fail("G12", "ceiling_violation", "effective_mode 不允许 auto 发送")

    checked.append("G13")
    if reply_mode == "assisted" and not ctx.pending_assisted_id:
        return fail("G13", "pending_not_found", "assisted 发送缺少 pending_assisted_id")

    checked.append("G14")
    if reply_mode == "assisted":
        status = (ctx.pending_status or "").lower()
        if status not in _VALID_PENDING_STATUSES:
            return fail("G14", "invalid_pending_status", "pending 状态不允许发送")

    checked.append("G15")
    if reply_mode == "assisted" and _is_pending_expired(ctx.expires_at, created_at):
        return fail("G15", "pending_expired", "待确认回复已过期")

    checked.append("G16")
    if ctx.idempotency_consumed:
        return fail("G16", "duplicate_send_attempt", "重复发送请求已被拦截")

    checked.append("G17")
    if _is_unsafe_intent(ctx):
        guide_exception = (
            ctx.effective_mode == "guide_only"
            and _is_platform_guidance(ctx.final_reply)
        )
        if not guide_exception:
            return fail("G17", "unsafe_intent", "意图类别不安全，禁止发送")

    checked.append("G18")
    risk = (ctx.risk_level or "").lower()
    if risk in _HIGH_RISK_LEVELS:
        return fail("G18", "high_risk", "高风险咨询禁止发送")

    checked.append("G19")
    if ctx.blocked_reason:
        return fail("G19", "blocked_intent", ctx.blocked_reason)

    checked.append("G20")
    if ctx.human_takeover_reason:
        return fail("G20", "human_takeover_required", ctx.human_takeover_reason)

    checked.append("G21")
    if not ctx.final_reply or not str(ctx.final_reply).strip():
        return fail("G21", "empty_reply", "最终回复为空，禁止发送")

    scan = scan_forbidden_promise(ctx.final_reply)
    checked.extend(["G22", "G23", "G24"])
    if scan.blocked:
        rule_id = {
            "forbidden_promise": "G22",
            "off_platform_risk": "G23",
            "review_manipulation": "G24",
        }.get(scan.block_code or "", "G22")
        return fail(rule_id, scan.block_code or "forbidden_promise", scan.block_reason or "回复未通过安全扫描")

    checked.append("G25")
    if _is_stale_inbound(ctx.inbound_created_at, created_at):
        return fail("G25", "stale_message", "入站消息已过期，禁止发送")

    checked.append("G26")
    status = (ctx.outbound_channel_status or "").lower()
    if status != "available":
        return fail("G26", "outbound_unavailable", "出站通道不可用，禁止发送")

    if reply_mode == "auto":
        role = ctx.actor_role
        if role is not None and role not in _AUTO_SEND_ROLES and (role or "").lower() not in _ASSISTED_SEND_ROLES:
            return fail("G5", "permission_denied", "auto 发送 actor 无效")
        return _allow(ctx, send_mode="auto_send", checked_rules=checked, created_at=created_at)

    return _allow(ctx, send_mode="assisted_send", checked_rules=checked, created_at=created_at)


def evaluate_final_guard(ctx: FinalGuardInput) -> FinalGuardResult:
    """Evaluate final guard rules — pure decision, no outbound side effects."""
    try:
        return _evaluate_final_guard_inner(ctx)
    except Exception as exc:
        created_at = ctx.now or _utc_now_iso()
        return FinalGuardResult(
            allowed_to_send=False,
            decision="block",
            block_code="guard_exception",
            block_reason=str(exc),
            audit_action="final_guard_blocked",
            send_mode="none",
            checked_rules=["G27"],
            policy_snapshot=_build_policy_snapshot(ctx),
            template_snapshot=_build_template_snapshot(ctx),
            created_at=created_at,
        )
