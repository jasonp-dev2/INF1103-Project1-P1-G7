from __future__ import annotations

from typing import Any


class AIAssessment:
    """Encapsulates the structured outcome of an AI product risk evaluation."""

    STATUS_OK = "ok"
    STATUS_FAILED = "failed"
    VALID_RISK_LEVELS = ("low", "medium", "high")

    def __init__(
        self,
        status: str,
        risk_level: str | None = None,
        recommended_discount_percent: float = 0.0,
        predicted_unsold_quantity: int = 0,
        model_used: str = "",
        error: str = "",
    ) -> None:
        self._status = status
        self._risk_level = risk_level
        self._recommended_discount_percent = recommended_discount_percent
        self._predicted_unsold_quantity = predicted_unsold_quantity
        self._model_used = model_used
        self._error = error

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_ok(self) -> bool:
        return self._status == self.STATUS_OK

    @property
    def risk_level(self) -> str | None:
        return self._risk_level

    @property
    def recommended_discount_percent(self) -> float:
        return self._recommended_discount_percent

    @property
    def predicted_unsold_quantity(self) -> int:
        return self._predicted_unsold_quantity

    @property
    def model_used(self) -> str:
        return self._model_used

    @property
    def error(self) -> str:
        return self._error

    @classmethod
    def success(
        cls,
        risk_level: str,
        recommended_discount_percent: float,
        predicted_unsold_quantity: int,
        model_used: str = "",
    ) -> AIAssessment:
        return cls(
            status=cls.STATUS_OK,
            risk_level=risk_level,
            recommended_discount_percent=recommended_discount_percent,
            predicted_unsold_quantity=predicted_unsold_quantity,
            model_used=model_used,
        )

    @classmethod
    def failed(cls, error_message: str) -> AIAssessment:
        return cls(status=cls.STATUS_FAILED, error=error_message)

    def to_dict(self) -> dict[str, Any]:
        if not self.is_ok:
            return {
                "status": self._status,
                "error": self._error,
            }
        result: dict[str, Any] = {
            "status": self._status,
            "risk_level": self._risk_level,
            "recommended_discount_percent": self._recommended_discount_percent,
            "predicted_unsold_quantity": self._predicted_unsold_quantity,
        }
        if self._model_used:
            result["model_used"] = self._model_used
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AIAssessment:
        status = data.get("status", cls.STATUS_FAILED)
        if status != cls.STATUS_OK:
            return cls.failed(str(data.get("error", "AI assessment unavailable.")))
        return cls.success(
            risk_level=str(data["risk_level"]),
            recommended_discount_percent=data["recommended_discount_percent"],
            predicted_unsold_quantity=int(data["predicted_unsold_quantity"]),
            model_used=str(data.get("model_used", "")),
        )

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]
