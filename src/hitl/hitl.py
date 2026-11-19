"""
Lab 11 — Optional enrichment: Human-in-the-Loop Design
  (Không chấm — tham khảo. Tóm tắt nộp do scripts/grade.py tự sinh,
   không viết report/*.md tay.)
  - Confidence Router
  - 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# Optional enrichment: ConfidenceRouter (không chấm)
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )

        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )

        if confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )

        return RoutingDecision(
            action="escalate",
            confidence=confidence,
            reason="Low confidence — escalating",
            priority="high",
            requires_human=True,
        )


# ============================================================
# Optional enrichment: 3 HITL decision points (không chấm)
# Không bắt buộc điền. Tóm tắt bài nộp: chạy scripts/grade.py
# (tự sinh lab_report.md) — không viết report tay.
#
# For each decision point, define:
# - trigger: What condition activates this HITL check?
# - hitl_model: Which model? (human-in-the-loop, human-on-the-loop,
#   human-as-tiebreaker)
# - context_needed: What info does the human reviewer need?
# - example: A concrete scenario
# - approval_path: What approve/reject/timeout decision is recorded?
# - audit_fields: Which correlation ID, intent and proposed action/diff are logged?
#
# Think about real banking scenarios where human judgment is critical.
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "High-Value or External Fund Transfer",
        "trigger": "action_type == 'transfer_money' or amount >= 50_000_000 VND",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Customer ID, source/destination account, amount, transfer purpose, fraud risk score",
        "example": "Customer asks assistant to transfer 120,000,000 VND to a newly added beneficiary.",
        "approval_path": "Approve -> execute transfer with approval_id; Reject -> cancel and notify; Timeout (15m) -> auto-reject (fail-closed).",
        "audit_fields": "correlation_id, user_id, intent, payload_diff, reviewer_id, decision, timestamp",
    },
    {
        "id": 2,
        "name": "Account Closure or Credential Change",
        "trigger": "action_type in {'close_account', 'change_password', 'update_personal_info'}",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Verified eKYC status, recent login IP/device history, proposed field diff",
        "example": "User requests updating registered phone number and closing an active savings account.",
        "approval_path": "Approve -> apply update after OTP/staff sign-off; Reject -> lock change & alert fraud team; Timeout (10m) -> expire request.",
        "audit_fields": "correlation_id, intent, before_after_diff, reviewer_id, approval_id, decision",
    },
    {
        "id": 3,
        "name": "Low-Confidence Policy / Fee Dispute Answer",
        "trigger": "confidence < 0.9 on complex fee waiver, loan restructuring, or dispute query",
        "hitl_model": "human-on-the-loop (0.7–0.9) / human-as-tiebreaker (< 0.7)",
        "context_needed": "Original prompt, draft AI response, confidence score, matched policy clauses",
        "example": "Customer disputes an international card fee and asks for an exception waiver (confidence = 0.62).",
        "approval_path": "Approve -> send draft; Edit/Reject -> human agent sends corrected reply; Timeout (30m) -> escalate to senior support.",
        "audit_fields": "correlation_id, confidence, draft_response, reviewer_id, final_action, latency_ms",
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
