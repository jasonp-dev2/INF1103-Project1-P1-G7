class inputHandler:
    def __init__(self, product_name, product_category, product_amt, product_expiry, product_price):
        self.product_name = product_name
        self.product_category = product_category
        self.product_amt = product_amt
        self.product_expiry = product_expiry
        self.product_price = product_price

    def display_info(self):
        print(f"Product Name: {self.product_name}")
        print(f"Product Category: {self.product_category}")
        print(f"Product Amount: {self.product_amt}")
        print(f"Product Expiry Date: {self.product_expiry}")
        print(f"Product Price per Unit: ${self.product_price:.2f}")

    def collect_menu_choices(self):
        print("\n===== Expiry & Discount Advisor =====")
        print("1. Assess a new product")
        print("2. Show all products")
        print("3. Show products near expiry")
        print("4. View product details")
        print("0. Exit")
        return input("Please enter your choice (0-4): ")