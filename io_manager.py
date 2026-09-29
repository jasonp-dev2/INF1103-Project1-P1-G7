"""
categories = ["Dairy & Eggs", "Bakery", "Meat & Seafood", "Fruits & Vegetables", "Frozen Food", "Beverages", "Other"]

print("Assess a new product")

product_name = ""
while product_name == "":
    product_name = input("Product name: ")
    if product_name == "":
        print("This field cannot be empty. Try again.")

quantity = 0
while quantity <= 0:
    quantity_text = input("Quantity in stock: ")
    if quantity_text.isdigit():
        quantity = int(quantity_text)
    else:
        print("Please enter a whole number.")

print("Choose a category:")
for i in range(len(categories)):
    print(i + 1, "-", categories[i])

category_choice = 0
while category_choice < 1 or category_choice > len(categories):
    choice_text = input("Enter a number: ")
    if choice_text.isdigit():
        category_choice = int(choice_text)

category = categories[category_choice - 1]

print("Product name entered:", product_name)
print("Quantity entered:", quantity)
print("Category chosen:", category) 
"""

from datetime import datetime, date
DATE_FORMAT= "%y-%m-%d"





def valid_product(Userinput):
    if user_input.isdigit():
        return "no"
    else:
        return str(Userinput)
    


user_input=input("Please enter product name:")
while valid_product(user_input) == "no" or valid_product(user_input) == "":#checking if input is valid ie no number and blank
    print("Invalid input Please enter a product name")
    user_input=input("Please enter product name:")

product_name= user_input# saving user input into varible 
print(f"{product_name}")#testing line

user_input=input("Enter current inventory amount:")




