from datetime import date, datetime

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
OUTCOME_URGENT_DISCOUNT = "URGENT_DISCOUNT"
OUTCOME_DISCOUNT = "DISCOUNT_RECOMMENDED"
OUTCOME_MONITOR = "MONITOR"

OUTCOMES = (
    OUTCOME_EXPIRED,
    OUTCOME_NOT_NEAR_EXPIRY,
    OUTCOME_MANUAL_REVIEW,
    OUTCOME_URGENT_DISCOUNT,
    OUTCOME_DISCOUNT,
    OUTCOME_MONITOR,
    )

class logicManager():

    def __init__(self):
        self._category_discounts = {}

    def _normalize_category(self, category: str) -> str:
        if not category:
            return ""
        cat = category.lower().strip()

        #Handles common plurals/typos
        if cat.endswith("ies") and len(cat) > 3:
            return cat[:-3] + "y" # e.g: "berries" -> "berry"
        if cat.endswith("es") and len(cat) > 3:
            return cat[:-2] # e.g:
        if cat.endswith("s") and len(cat) > 3:
            return cat[:-1] # e.g: "meats" -> "meat"

        return cat

    #Setting the category discount
    def set_category_discount(self, category, discount):
        if discount < 0 or discount > MAX_DISCOUNT_PERCENT:
            raise ValueError("Invalid discount")

        normalized_cat = self._normalize_category(category)
        self._category_discounts[normalized_cat] = discount

    #Retrieving the category discount
    def get_final_discount(self, product: dict, recommended_discount: float) -> float:
        category = product.get("category")
        normalized_cat = self._normalize_category(category)

        if normalized_cat in self._category_discounts:
            return self._category_discounts[normalized_cat]

        return recommended_discount

    # Return how many days left until expiry (negative means expired)
    def days_until_expiry(self, expiry_date: str, today: date) -> int:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        days_remaining = (expiry - today).days
        return days_remaining

    def apply_discount_cap(self, discount_percent: float, discount_cap: float) -> float:
        if discount_percent > discount_cap:
            return discount_cap
        if discount_percent < 0:
            return 0
        return discount_percent

    def calculate_final_price(self, price: float, discount_percent: float) -> float:
        return round(price * (1 - discount_percent / 100), 2)


    # To check proportion of stocks expected to remain unsold based on AI prediction
    def calculate_unsold_ratio(self, predicted_unsold: float, quantity: int) -> float:
        if quantity <= 0:
            return 0
        return predicted_unsold / quantity


    # To check money lost for predicted unsold stock
    def calculate_waste_cost(self, predicted_unsold: float, price: float) -> float:
        return round(predicted_unsold * price, 2)

    # Create a dictionary to store information on what to do with product
    def make_decision(self, outcome: str, rule: str, reason: str, days_left: int,
                    discount_percent: float, price: float, waste_cost: float) -> dict:
        return {
            "outcome": outcome,
            "rule": rule,
            "reason": reason,
            "days_to_expiry": days_left,
            "discount_percent": discount_percent,
            "final_price": self.calculate_final_price(price, discount_percent),
            "waste_cost_if_unsold": waste_cost,
            # Any recommended discount must be approved by staff before use.
            "needs_staff_approval": discount_percent > 0,
        }

    # Example below based on rules


    # ---------------------------------------------------------------------------
    # The main function: applies the rules in priority order
    # ---------------------------------------------------------------------------

    def evaluate(self, product: dict, ai_result: dict, today: date) -> dict:
        #If duplicate rules exist, then will take first rule
        
        days_left = self.days_until_expiry(product["expiry_date"], today)
        price = product["current_price"]
        quantity = product["quantity_in_stock"]

        # Rule1: Never recommend an expired product. (Food safety)
        if days_left < 0:
            final = self.make_decision(
                OUTCOME_EXPIRED, "R1",
                "The product has passed its expiry date and must not be sold.",
                days_left, 0, price, 0)
            return final

        # Rule2: Only near-expiry products have discount.
        if days_left > NEAR_EXPIRY_DAYS:
            final = self.make_decision(
                OUTCOME_NOT_NEAR_EXPIRY, "R2",
                f"{days_left} days left - not near expiry, no discount needed.",
                days_left, 0, price, 0)
            return final

        # Rule3: If the AI failed, then will send it to a person.
        if ai_result["status"] != STATUS_OK:
            final = self.make_decision(
                OUTCOME_MANUAL_REVIEW, "R3",
                "The AI assessment was unavailable, so staff must review this item.",
                days_left, 0, price, 0)
            return final

        risk = ai_result["risk_level"]
        ai_percent = ai_result["recommended_discount_percent"]
        predicted_unsold = ai_result["predicted_unsold_quantity"]
        unsold_ratio = self.calculate_unsold_ratio(predicted_unsold, quantity)
        waste_cost = self.calculate_waste_cost(predicted_unsold, price)

        # Rule4: Multi-condition rule using AI output. (Urgent)
        #      Few days left AND high risk AND alot expected unsold.
        if (days_left <= URGENT_DAYS and risk == "high" and unsold_ratio >= URGENT_UNSOLD_RATIO):
            percent = max(ai_percent, URGENT_MIN_DISCOUNT)
            percent = max(URGENT_MIN_DISCOUNT, self.get_final_discount(product, percent))
            percent = self.apply_discount_cap(percent, MAX_DISCOUNT_PERCENT)
            final = self.make_decision(
                OUTCOME_URGENT_DISCOUNT, "R4",
                f"{days_left} day(s) left, high risk and about "
                f"{predicted_unsold:.0f} unit(s) likely unsold.",
                days_left, percent, price, waste_cost)
            return final

        # Rule5: Normal discount: AI suggests a discount and risk is not low.
        if ai_percent > 0 and risk != "low":
            percent = self.get_final_discount(product, ai_percent)
            percent = self.apply_discount_cap(percent, MAX_DISCOUNT_PERCENT)
            final = self.make_decision(
                OUTCOME_DISCOUNT, "R5",
                f"Near expiry with {risk} risk - a discount is recommended.",
                days_left, percent, price, waste_cost)
            return final

        # Rule6: Keep an eye on it, no discount yet.
        final = self.make_decision(
            OUTCOME_MONITOR, "R6",
            "Near expiry but low risk of waste - keep monitoring.",
            days_left, 0, price, waste_cost)
        return final
