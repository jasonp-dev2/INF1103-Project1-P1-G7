from datetime import date, datetime

# Return how many days left until expiry (negative means expired) (E.g: 2026-07-26)
def days_until_expiry(expiry_date: str, today: date) -> int:
    expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    return (expiry - today).days

def apply_discount_cap(discount_percent: float, max_percent: float) -> float:
    if discount_percent > max_percent:
        return max_percent
    if discount_percent < 0:
        return 0
    return discount_percent

def calculate_final_price(price: float, discount_percent: float) -> float:
    return round(price * (1 - discount_percent / 100), 2)

# To check proportion of stocks expected to remain unsold based on AI prediction
def calculate_unsold_ratio(predicted_unsold: float, quantity: int) -> float:
    if quantity <= 0:
        return 0
    return predicted_unsold / quantity

# To check money lost for predicted unsold stock
def calculate_waste_cost(predicted_unsold: float, price: float) -> float:
    return round(predicted_unsold * price, 2)


