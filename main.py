from classes.Inputhandler import inputHandler
from classes.productCatergory import product

my_products = product()
new_product = inputHandler.collect_product_info()
my_products.add_product(new_product)
my_products.display_all()