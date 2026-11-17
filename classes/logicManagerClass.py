from datetime import date, datetime

NEAR_EXPIRY_DAYS = 7          
URGENT_DAYS = 3               
URGENT_UNSOLD_RATIO = 0.5     
URGENT_MIN_DISCOUNT = 30

# Default max discount, user can set with set_max_discount() 
MAX_DISCOUNT_PERCENT = 50     

# The max discount itself can never be set above this.
ABSOLUTE_MAX_DISCOUNT = 100

# The AI result's "status" value when the AI call worked.
STATUS_OK = "ok"

# Unknown products will be under "Others"
OTHERS_CATEGORY = "others"
DEFAULT_OTHERS_DISCOUNT = 20

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
        self._max_discount = MAX_DISCOUNT_PERCENT
        self._known_categories = set()
        # "others" always has a default discount so unknown categories are covered.
        self._category_discounts = {OTHERS_CATEGORY: DEFAULT_OTHERS_DISCOUNT}

    def _normalize_category(self, category: str) -> str:
        if not category or not isinstance(category, str):
            return ""
        
        cat = " ".join(category.lower().split())

        if cat in ("other", "others"):
            return OTHERS_CATEGORY

        #Handles common plurals/typos
        if cat.endswith("ies") and len(cat) > 3:
            return cat[:-3] + "y" # e.g: "berries" -> "berry"
        if cat.endswith(("sses", "shes", "ches", "xes", "oes")) and len(cat) > 3:
            return cat[:-2] # e.g: "tomatoes" -> "tomato"
        if cat.endswith("s") and not cat.endswith("ss") and len(cat) > 3:
            return cat[:-1] # e.g: "meats" -> "meat"

        return cat

    # Call this after loading products (json/mongodb) and after adding a product,
    # so the manager knows which categories really exist.
    def load_categories(self, products: list) -> None:
        self._known_categories = set()
        for product in products:
            cat = self._normalize_category(product.get("category"))
            if cat:
                self._known_categories.add(cat)

    def get_known_categories(self) -> list:
        return sorted(self._known_categories)

    # Which bucket a category belongs to: itself if it exists, otherwise "others"
    def resolve_category(self, category) -> str:
        cat = self._normalize_category(category)

        # If categories have not been loaded yet, do not push everything into "others"
        if not self._known_categories:
            return cat or OTHERS_CATEGORY

        if cat in self._known_categories:
            return cat
        return OTHERS_CATEGORY

    # ---------------------------------------------------------------------------
    # User-configurable discount settings
    # ---------------------------------------------------------------------------

    def set_max_discount(self, max_discount: float) -> None:
        if max_discount < 0 or max_discount > ABSOLUTE_MAX_DISCOUNT:
            raise ValueError(f"Max discount must be between 0 and {ABSOLUTE_MAX_DISCOUNT}")
        self._max_discount = max_discount

    def get_max_discount(self) -> float:
        return self._max_discount

    #Setting the category discount
    def set_category_discount(self, category, discount: float) -> str:
        if not isinstance(discount, (int, float)) or isinstance(discount, bool):
            raise ValueError("Discount must be a number")
    
        if discount < 0 or discount > ABSOLUTE_MAX_DISCOUNT:
            raise ValueError("Invalid discount")

    # Buckeet meaning its just to show the user where its stored under (typo errors)
        bucket = self.resolve_category(category)
        self._category_discounts[bucket] = discount
        return bucket

    # Go back to AI's discount for that category ("others" goes back to its default)
    def remove_category_discount(self, category) -> None:
        bucket = self.resolve_category(category)
        if bucket == OTHERS_CATEGORY:
            self._category_discounts[OTHERS_CATEGORY] = DEFAULT_OTHERS_DISCOUNT
        else:
            self._category_discounts.pop(bucket, None)

    def get_category_discounts(self) -> dict:
        return dict(self._category_discounts)

    # For saving/loading the user's settings (json/mongodb)
    # (Discounts still work after restarting program)
    def get_settings(self) -> dict:
        return {
            "max_discount": self._max_discount,
            "category_discounts": dict(self._category_discounts),
        }

    # Call load_categories() first, then this.
    def load_settings(self, settings: dict) -> None:
        self.set_max_discount(settings.get("max_discount", MAX_DISCOUNT_PERCENT))
        for category, discount in settings.get("category_discounts", {}).items():
            self.set_category_discount(category, discount)

    # Category discount overrides the AI's discount. No category discount -> keep AI's.
    def get_final_discount(self, product: dict, recommended_discount: float) -> float:
        bucket = self.resolve_category(product.get("category"))

        if bucket in self._category_discounts:
            return self._category_discounts[bucket]

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

        # Check category override.
        bucket = self.resolve_category(product.get("category"))

        if bucket in self._category_discounts:

            # User category discount overrides AI completely.
            percent = self._category_discounts[bucket]

            # Apply global maximum discount.
            percent = self.apply_discount_cap(
            percent, self._max_discount
            )

            # A 0% category discount means no discount.
            if percent == 0:
                return self.make_decision(
                    OUTCOME_MONITOR, "R4",
                    f"User-configured discount for {bucket} is 0%. "
                    "No discount will be applied.",
                    days_left, 0, price, waste_cost
                )
            final = self.make_decision(
                OUTCOME_URGENT_DISCOUNT if days_left <= URGENT_DAYS else OUTCOME_DISCOUNT, "R4",
                f"User-configured {bucket} discount overrides the AI recommendation.",
                days_left, percent, price, waste_cost
            )
            return final

        # Rule5: Multi-condition rule using AI output. (Urgent)
        #      Few days left AND high risk AND alot expected unsold.
        if (days_left <= URGENT_DAYS and risk == "high" and unsold_ratio >= URGENT_UNSOLD_RATIO):
            percent = max(ai_percent, URGENT_MIN_DISCOUNT)
            percent = self.apply_discount_cap(percent, self._max_discount)
            final = self.make_decision(
                OUTCOME_URGENT_DISCOUNT, "R5",
                f"{days_left} day(s) left, high risk and about "
                f"{predicted_unsold:.0f} unit(s) likely unsold.",
                days_left, percent, price, waste_cost)
            return final

        # Rule6: Normal discount: AI suggests a discount and risk is not low.
        if ai_percent > 0 and risk != "low":
            percent = self.apply_discount_cap(ai_percent, self._max_discount)
            final = self.make_decision(
                OUTCOME_DISCOUNT, "R6",
                f"Near expiry with {risk} risk - a discount is recommended.",
                days_left, percent, price, waste_cost)
            return final

        # Rule7: Keep an eye on it, no discount yet.
        final = self.make_decision(
            OUTCOME_MONITOR, "R7",
            "Near expiry but low risk of waste - keep monitoring.",
            days_left, 0, price, waste_cost)
        return final
