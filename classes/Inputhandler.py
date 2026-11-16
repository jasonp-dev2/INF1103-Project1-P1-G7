from classes.productCatergory import productCategory
from datetime import datetime , date


class inputHandler:
    @staticmethod
    def valid_product_name(product_name: str):
        if product_name == "" or product_name.isdigit():
                return "no"
        return product_name

    @staticmethod
    def valid_category(category_number: str):
        if not category_number.isdigit():
                    return "no"
        number = int(category_number)
        return number
    
    @staticmethod
    def valid_stock(quantity: str):
        # Must be a whole number (0 or more)
        if quantity.isdigit():
            return int(quantity)
        return "no"
    
    @staticmethod
    def valid_date(date_str: str):
    # Only checks the format. Whether a product is expired or near expiry
    # is decided by logic_manager, not here.
        try:
            return datetime.strptime(date_str, DATE_FORMAT).date()
        except ValueError:
            return "no"
    
    @staticmethod
    def valid_price(price: str):
    # Must be a number above 0, decimals allowed (e.g. 4.50)
        try:
         price = float(price)
        except ValueError:
            return "no"
        if price <= 0:
            return "no"
        return price


    
    @staticmethod
    def collect_record_id():
        record_id = input("Please enter the record ID: ")
        return record_id

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
        print("5. Update product stock")
        print("6. Delete product")
        print("0. Exit")
        return input("Please enter your choice (0-6): ")
    
    @staticmethod
    def collect_product_info():
        # Collect product information from the user
        product_name = input("Please enter product name:")
        while inputHandler.valid_product_name(product_name) == "no":
            print("Invalid product name. Please try again.")
            product_name = input("Please enter product name:")

        category_number = input("Please enter product category number:")
        while inputHandler.valid_category(category_number) == "no":
            print("Invalid category number. Please try again.")
            category_number = input("Please enter product category number:")
        category_number = int(category_number)

        quantity = input("Please enter quantity in stock:")
        while inputHandler.valid_stock(quantity) == "no":
            print("Invalid quantity. Please try again.")
            quantity = input("Please enter quantity in stock:")
        quantity = int(quantity)

        expiry_date_str = input("Please enter expiry date (YYYY-MM-DD):")
        while inputHandler.valid_date(expiry_date_str) == "no":
            print("Invalid date format. Please try again.")
            expiry_date_str = input("Please enter expiry date (YYYY-MM-DD):")
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        price = input("Please enter product price per unit($):")
        while inputHandler.valid_price(price) == "no":
            print("Invalid price. Please try again.")
            price = input("Please enter product price per unit($):")
        price = float(price)

        new_item = productCategory(product_name, category_number, quantity, expiry_date, price)
        return new_item

