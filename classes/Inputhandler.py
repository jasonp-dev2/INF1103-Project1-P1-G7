from classes.InputValid import inputvalid
from datetime import datetime , date


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
    
    @staticmethod
    def collect_product_info():
        # Collect product information from the user
        product_name = input("Please enter product name:")
        while inputvalid.valid_product_name(product_name) == "no":
            print("Invalid product name. Please try again.")
            product_name = input("Please enter product name:")

        category_number = input("Please enter product category number:")
        while inputvalid.valid_category(category_number) == "no":
            print("Invalid category number. Please try again.")
            category_number = input("Please enter product category number:")
        category_number = int(category_number)

        quantity = input("Please enter quantity in stock:")
        while inputvalid.valid_stock(quantity) == "no":
            print("Invalid quantity. Please try again.")
            quantity = input("Please enter quantity in stock:")
        quantity = int(quantity)

        expiry_date_str = input("Please enter expiry date (YYYY-MM-DD):")
        while inputvalid.valid_date(expiry_date_str) == "no":
            print("Invalid date format. Please try again.")
            expiry_date_str = input("Please enter expiry date (YYYY-MM-DD):")
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        price = input("Please enter product price per unit($):")
        while inputvalid.valid_price(price) == "no":
            print("Invalid price. Please try again.")
            price = input("Please enter product price per unit($):")
        price = float(price)

        new_item = inputHandler(product_name, category_number, quantity, expiry_date, price)
        return new_item

