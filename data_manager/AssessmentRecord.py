"""
Assessment Record Class.
Binds a Product, AIAssessment and Decision under a record ID.
"""

from __future__ import annotations

from typing import Any
from classes.Product import Product
from classes.AIAssessment import AIAssessment
from classes.Decision import Decision


class AssessmentRecord:
    def __init__(
        self,
        record_id: str,
        product: Product,
        ai_assessment: AIAssessment,
        decision: Decision,
        staff_approved: bool | None = None,
    ) -> None:
        if staff_approved is not None and not isinstance(staff_approved, bool):
            raise ValueError("staff_approved must be True, False, or None.")

        self._record_id = record_id.strip().upper()
        self._product = Product.from_dict(product.to_dict())
        self._ai_assessment = AIAssessment.from_dict(ai_assessment.to_dict())
        self._decision = Decision.from_dict(decision.to_dict())
        self._staff_approved = staff_approved

    @property
    def record_id(self) -> str:
        return self._record_id

    @property
    def product(self) -> Product:
        return self._product

    @property
    def ai_assessment(self) -> AIAssessment:
        return self._ai_assessment

    @property
    def decision(self) -> Decision:
        return self._decision

    @decision.setter
    def decision(self, new_decision: Decision) -> None:
        self._decision = Decision.from_dict(new_decision.to_dict())

    @property
    def staff_approved(self) -> bool | None:
        return self._staff_approved

    @staff_approved.setter
    def staff_approved(self, value: bool | None) -> None:
        if value is not None and not isinstance(value, bool):
            raise ValueError("staff_approved must be True, False, or None.")
        self._staff_approved = value

    def approve_discount(self) -> None:
        self._staff_approved = True

    def reject_discount(self) -> None:
        self._staff_approved = False

    def is_already_discounted(self) -> bool:
        return (
            self._decision.discount_percent > 0
            and self._staff_approved is True
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "record_id": self._record_id,
            "product": self._product.to_dict(),
            "ai_assessment": self._ai_assessment.to_dict(),
            "decision": self._decision.to_dict(),
        }

        if self._staff_approved is not None:
            data["staff_approved"] = self._staff_approved

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssessmentRecord:
        return cls(
            record_id=data["record_id"],
            product=Product.from_dict(data["product"]),
            ai_assessment=AIAssessment.from_dict(data["ai_assessment"]),
            decision=Decision.from_dict(data["decision"]),
            staff_approved=data.get("staff_approved"),
        )