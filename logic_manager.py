from datetime import date, datetime

# Can be change depending on respective store
NEAR_EXPIRY_DAYS = 7          
URGENT_DAYS = 3               
URGENT_UNSOLD_RATIO = 0.5     
URGENT_MIN_DISCOUNT = 30      
MAX_DISCOUNT_PERCENT = 50     

# The AI result's "status" value when the AI call worked.
STATUS_OK = "ok"

# The possible outcomes of a decision
OUTCOME_EXPIRED = "EXPIRED"
OUTCOME_NOT_NEAR_EXPIRY = "NOT_NEAR_EXPIRY"
OUTCOME_MANUAL_REVIEW = "MANUAL_REVIEW"
OUTCOME_NO_STACKING = "NO_STACKING"
OUTCOME_URGENT_DISCOUNT = "URGENT_DISCOUNT"
OUTCOME_DISCOUNT = "DISCOUNT_RECOMMENDED"
OUTCOME_MONITOR = "MONITOR"

OUTCOMES = (
    OUTCOME_EXPIRED,
    OUTCOME_NOT_NEAR_EXPIRY,
    OUTCOME_MANUAL_REVIEW,
    OUTCOME_NO_STACKING,
    OUTCOME_URGENT_DISCOUNT,
    OUTCOME_DISCOUNT,
    OUTCOME_MONITOR,
    )


# Return how many days left until expiry (negative means expired)
def days_until_expiry(expiry_date: str, today: date) -> int:
    expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    days_remaining = (expiry - today).days
    return days_remaining

# Example (-87 => expired)
print(days_until_expiry("2026-07-26", date(2026, 10, 21)))

def apply_discount_cap(discount_percent: float, max_percent: float) -> float:
    if discount_percent > max_percent:
        return max_percent
    if discount_percent < 0:
        return 0
    return discount_percent

# Example (Discount > Max)
print(apply_discount_cap(50, 40))

def calculate_final_price(price: float, discount_percent: float) -> float:
    return round(price * (1 - discount_percent / 100), 2)

# Example ($20 with 10% discount)
print(calculate_final_price(20, 10))

# To check proportion of stocks expected to remain unsold based on AI prediction
def calculate_unsold_ratio(predicted_unsold: float, quantity: int) -> float:
    if quantity <= 0:
        return 0
    return predicted_unsold / quantity

# Example (5 goods, AI predict 3 unsold) => 0.6 Ratio predicted to be unsold
print(calculate_unsold_ratio(3, 5))

# To check money lost for predicted unsold stock
def calculate_waste_cost(predicted_unsold: float, price: float) -> float:
    return round(predicted_unsold * price, 2)

# Example (Predicted total lost = 30)
print(calculate_waste_cost(3, 10))

# Create a dictionary to store information on what to do with product
def make_decision(outcome: str, rule: str, reason: str, days_left: int,
                  discount_percent: float, price: float, waste_cost: float) -> dict:
    return {
        "outcome": outcome,
        "rule": rule,
        "reason": reason,
        "days_to_expiry": days_left,
        "discount_percent": discount_percent,
        "final_price": calculate_final_price(price, discount_percent),
        "waste_cost_if_unsold": waste_cost,
        # Any recommended discount must be approved by staff before use.
        "needs_staff_approval": discount_percent > 0,
    }

# Example below based on rules



