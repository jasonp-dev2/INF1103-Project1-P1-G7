


class product:
    def __init__(self):
        self.product:list[inputHandler] = []

    def add_product(self, inputer: inputHandler):
        self.product.append(inputer)

    def remove_product(self, product_name: str):
        for product in self.product:
            if product.product_name == product_name:
                self.product.remove(product)
                print(f"Product '{product_name}' removed successfully.")
                return
        print(f"Product '{product_name}' not found.")


    def display_all(self):
        if not self.product:
            print("No products available.")
            return
        for item in self.product:
            item.display_info()
            print("--------------------")