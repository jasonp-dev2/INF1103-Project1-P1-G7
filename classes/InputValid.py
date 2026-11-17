from datetime import datetime , date

DATE_FORMAT = "%Y-%m-%d"


class inputvalid:
    #check for valid product info
    @staticmethod
    def valid_product_name(product_name: str):
        product_name = product_name.strip()
        if product_name == "" or product_name.isdigit():
            return "no"
        return product_name

    @staticmethod
    def valid_category(category_number: str):
        if not category_number.isdigit():
                return "no"
        number = int(category_number)
        if not 1 <= number <= 7:
            return "no"
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