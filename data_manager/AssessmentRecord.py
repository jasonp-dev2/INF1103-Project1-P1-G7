"""
Assessment Record Class.
Binds a Product, AIAssessment and Decision under a record ID.
"""

from __future__ import annotations

from copy import deepcopy

class AssessmentRecord:
    def __init__(self,
        record_id: str,
        product: dict,
        ai_assessment: dict, 
        decision: dict, 
        staff_approved: bool | None = None,
        isDeleted: bool = False) -> None:
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a nonempty string.")
        if not all(isinstance(value, dict) for value in (product, ai_assessment, decision)):
            raise ValueError("Assessment components must be dictionaries.")
        self._record_id = record_id.strip().upper()
        self._product = deepcopy(product)
        self._ai_assessment = deepcopy(ai_assessment)
        self._decision = deepcopy(decision)
        self.set_staff_approved(staff_approved)
        self.set_deleted(isDeleted)


    @property
    def record_id(self) -> str:
        return self._record_id

    @property
    def is_deleted(self) -> bool:
        return self._is_deleted

    def set_deleted(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("isDeleted must be True or False.")
        self._is_deleted = value

    def set_decision(self, new_decision: dict) -> None:
        if not isinstance(new_decision, dict):
            raise ValueError("decision must be a dictionary.")
        if new_decision != self._decision:
            self._staff_approved = None
        self._decision = deepcopy(new_decision)

    def set_staff_approved(self, value: bool | None) -> None:
        if value is not None and not isinstance(value, bool):
            raise ValueError("staff_approved must be True, False, or None.")
        self._staff_approved = value

    def to_dict(self) -> dict:
        data = {
            "record_id": self._record_id,
            "isDeleted": self._is_deleted,
            "product": self._product,
            "ai_assessment": self._ai_assessment,
            "decision": self._decision,
        }

        if self._staff_approved is not None:
            data["staff_approved"] = self._staff_approved

        return deepcopy(data)

    @classmethod
    def from_dict(cls, data: dict) -> AssessmentRecord:
        return cls(
            record_id = data["record_id"],
            product = data["product"],
            ai_assessment = data["ai_assessment"],
            decision = data["decision"],
            staff_approved = data.get("staff_approved"),
            isDeleted = data.get("isDeleted", False),
        )
