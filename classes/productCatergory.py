from datetime import date, datetime

class productCategory():

    def __init__(self, product_name: str, product_category: str,
                 product_stock: int, expiry_date: date, product_price):
        self._name = product_name
        self._category = product_category
        self._stock = product_stock
        self._expiry = expiry_date
        self._price = product_price

    def get_discount_cap() -> float:
        return

    def set_discount_cap(self, discount: float):
        return