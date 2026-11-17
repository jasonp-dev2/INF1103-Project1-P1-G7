from __future__ import annotations

from typing import Any


class Decision:
    """Encapsulates the business-rule evaluation result for a product."""

    OUTCOME_EXPIRED = "EXPIRED"
    OUTCOME_NOT_NEAR_EXPIRY = "NOT_NEAR_EXPIRY"
    OUTCOME_MANUAL_REVIEW = "MANUAL_REVIEW"
    OUTCOME_URGENT_DISCOUNT = "URGENT_DISCOUNT"
    OUTCOME_DISCOUNT = "DISCOUNT_RECOMMENDED"
    OUTCOME_MONITOR = "MONITOR"

    def __init__(
        self,
        outcome: str,
        rule: str,
        reason: str,
        days_to_expiry: int,
        discount_percent: float,
        final_price: float,
        waste_cost_if_unsold: float,
        needs_staff_approval: bool | None = None,
    ) -> None:
        self._outcome = outcome
        self._rule = rule
        self._reason = reason
        self._days_to_expiry = int(days_to_expiry)
        self._discount_percent = discount_percent
        self._final_price = round(float(final_price), 2)
        self._waste_cost_if_unsold = round(float(waste_cost_if_unsold), 2)
        self._needs_staff_approval = (
            bool(discount_percent > 0)
            if needs_staff_approval is None
            else bool(needs_staff_approval)
        )

    @property
    def outcome(self) -> str:
        return self._outcome

    @property
    def rule(self) -> str:
        return self._rule

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def days_to_expiry(self) -> int:
        return self._days_to_expiry

    @property
    def discount_percent(self) -> float:
        return self._discount_percent

    @property
    def final_price(self) -> float:
        return self._final_price

    @property
    def waste_cost_if_unsold(self) -> float:
        return self._waste_cost_if_unsold

    @property
    def needs_staff_approval(self) -> bool:
        return self._needs_staff_approval

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self._outcome,
            "rule": self._rule,
            "reason": self._reason,
            "days_to_expiry": self._days_to_expiry,
            "discount_percent": self._discount_percent,
            "final_price": self._final_price,
            "waste_cost_if_unsold": self._waste_cost_if_unsold,
            "needs_staff_approval": self._needs_staff_approval,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Decision:
        return cls(
            outcome=str(data["outcome"]),
            rule=str(data["rule"]),
            reason=str(data["reason"]),
            days_to_expiry=int(data["days_to_expiry"]),
            discount_percent=data["discount_percent"],
            final_price=float(data["final_price"]),
            waste_cost_if_unsold=float(data["waste_cost_if_unsold"]),
            needs_staff_approval=bool(data.get("needs_staff_approval", data["discount_percent"] > 0)),
        )

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]
