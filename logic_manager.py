from datetime import date, datetime
import json

with open("products.json", "r") as file:
    data = json.load(file)

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

    # Rule3: If the AI failed, then will send it to a person.
    if ai_result["status"] != STATUS_OK:
        final = make_decision(
            OUTCOME_MANUAL_REVIEW, "R3",
            "The AI assessment was unavailable, so staff must review this item.",
            days_left, 0, price, 0)
        print(final)
        return final

    risk = ai_result["risk_level"]
    ai_percent = ai_result["recommended_discount_percent"]
    predicted_unsold = ai_result["predicted_unsold_quantity"]
    unsold_ratio = calculate_unsold_ratio(predicted_unsold, quantity)
    waste_cost = calculate_waste_cost(predicted_unsold, price)

    # Rule4: Multi-condition rule using AI output. (Urgent)
    #      Few days left AND high risk AND alot expected unsold.
    if (days_left <= URGENT_DAYS and risk == "high" and unsold_ratio >= URGENT_UNSOLD_RATIO):
        percent = max(ai_percent, URGENT_MIN_DISCOUNT)
        percent = apply_discount_cap(percent, MAX_DISCOUNT_PERCENT)
        final = make_decision(
            OUTCOME_URGENT_DISCOUNT, "R4",
            f"{days_left} day(s) left, high risk and about "
            f"{predicted_unsold:.0f} unit(s) likely unsold.",
            days_left, percent, price, waste_cost)
        print(final)
        return final

    # Rule5: Normal discount: AI suggests a discount and risk is not low.
    if ai_percent > 0 and risk != "low":
        percent = apply_discount_cap(ai_percent, MAX_DISCOUNT_PERCENT)
        final = make_decision(
            OUTCOME_DISCOUNT, "R5",
            f"Near expiry with {risk} risk - a discount is recommended.",
            days_left, percent, price, waste_cost)
        print(final)
        return final

    # Rule6: Keep an eye on it, no discount yet.
    final = make_decision(
        OUTCOME_MONITOR, "R7",
        "Near expiry but low risk of waste - keep monitoring.",
        days_left, 0, price, waste_cost)
    print(final)
    return final



#Example (product from io_manager, ai_result from ai_manager)

product = {
    "product_name": "Milk",
    "category": "Dairy & Eggs",
    "quantity_in_stock": 10,
    "expiry_date": "2026-11-30",
    "current_price": 4.5,

    "product_name": "Cookie",
      "category": "Pantry & Dry Goods",
      "quantity_in_stock": 100,
      "expiry_date": "2026-10-10",
      "current_price": 1.2,
}

ai_assessment = {
    "status": "ok",
    "risk_level": "high",
    "recommended_discount_percent": 30,
    "predicted_unsold_quantity": 3
}

print("-"*50)
evaluate(product, ai_assessment, date(2026,10,8))