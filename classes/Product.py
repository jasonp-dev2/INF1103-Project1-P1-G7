from datetime import date, datetime

class Product:

    def __init__(self, product_name: str, product_category: str,
                 product_stock: int, expiry_date: date, product_price):
        self._name = product_name
        self._category = product_category
        self._stock = product_stock
        self._expiry = expiry_date
        self._price = product_price

    def to_dict(self) -> dict:
        return {
            "product_name": self._name,
            "category": self._category,
            "quantity_in_stock": self._stock,
            "expiry_date": self._expiry.isoformat(),
            "current_price": round(self._price, 2),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        expiry = datetime.strptime(data["expiry_date"], "%Y-%m-%d").date()
        return cls(
            data["product_name"],
            data["category"],
            data["quantity_in_stock"],
            expiry,
            data["current_price"],
        )

    def days_until_expiry(self, today: date) -> int:
        return (self._expiry - today).days

    def get_discount_cap() -> float:
        return

    def set_discount_cap(self, discount: float):
        return