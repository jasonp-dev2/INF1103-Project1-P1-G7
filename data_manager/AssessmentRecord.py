"""
Assessment Record Class.
Binds a Product, AIAssessment and Decision under a record ID.
"""

from __future__ import annotations


class AssessmentRecord:
    def __init__(self,
        record_id: str,
        product: dict,
        ai_assessment: dict, 
        decision: dict, 
        staff_approved: bool | None = None) -> None:
        if staff_approved is not None and not isinstance(staff_approved, bool):
            raise ValueError("staff_approved must be True, False, or None.")

        self._record_id = record_id.strip().upper()
        self._product = product
        self._ai_assessment = ai_assessment
        self._decision = decision
        self._staff_approved = staff_approved


    def set_decision(self, new_decision: dict) -> None:
        self._decision = new_decision

    def set_staff_approved(self, value: bool | None) -> None:
        if value is not None and not isinstance(value, bool):
            raise ValueError("staff_approved must be True, False, or None.")
        self._staff_approved = value

    def approve_discount(self) -> None:
        self._staff_approved = True

    def reject_discount(self) -> None:
        self._staff_approved = False

    def is_already_discounted(self) -> bool:
        return (
            self._decision["discount_percent"] > 0
            and self._staff_approved is True
        )

    def to_dict(self) -> dict:
        data = {
            "record_id": self._record_id,
            "product": self._product,
            "ai_assessment": self._ai_assessment,
            "decision": self._decision,
        }

        if self._staff_approved is not None:
            data["staff_approved"] = self._staff_approved

        return data

    @classmethod
    def from_dict(cls, data: dict) -> AssessmentRecord:
        return cls(
            record_id = data["record_id"],
            product = data["product"],
            ai_assessment = data["ai_assessment"],
            decision = data["decision"],
            staff_approved = data.get("staff_approved"),
        )