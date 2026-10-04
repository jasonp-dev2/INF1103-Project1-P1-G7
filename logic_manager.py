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


# ---------------------------------------------------------------------------
# The main function: applies the rules in priority order
# ---------------------------------------------------------------------------

def evaluate(product: dict, ai_result: dict, today: date) -> dict:
    #If duplicate rules exist, then will take first rule
    
    days_left = days_until_expiry(product["expiry_date"], today)
    print("\n" + str(days_left))
    price = product["current_price"]
    quantity = product["quantity_in_stock"]

    # Rule1: Never recommend an expired product. (Food safety)
    if days_left < 0:
        print("Rule 1")
        final = make_decision(
            OUTCOME_EXPIRED, "R1",
            "The product has passed its expiry date and must not be sold.",
            days_left, 0, price, 0)
        print(final)
        return final

    # Rule2: Only near-expiry products have discount.
    if days_left > NEAR_EXPIRY_DAYS:
        print("Rule 2")
        final = make_decision(
            OUTCOME_NOT_NEAR_EXPIRY, "R2",
            f"{days_left} days left - not near expiry, no discount needed.",
            days_left, 0, price, 0)
        print(final)
        return final




#Example (product from io_manager, ai_result from ai_manager)

product = {
    "product_name": "Milk",
    "category": "Dairy & Eggs",
    "quantity_in_stock": 10,
    "expiry_date": "2026-11-30",
    "current_price": 4.5,
}

ai_assessment = {
    "status": "ok",
    "risk_level": "high",
    "recommended_discount_percent": 30,
    "predicted_unsold_quantity": 3
}