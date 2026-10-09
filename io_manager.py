from datetime import datetime, date, timedelta
import json

DATE_FORMAT= "%Y-%m-%d"
current_date = date.today()
minimum_expiry = current_date + timedelta(days=30)

def valid_product(Userinput):
    if user_input.isdigit():
        return "no"
    else:
        return str(Userinput)

def valid_stock (Userinput):
    if user_input.isdigit():
        return (Userinput)
    else:
        return "no"

def valid_date(userinput):
    try:
        expiry_date = date.strptime(userinput, DATE_FORMAT)
        if expiry_date >= minimum_expiry:
            return expiry_date
        else:
            return "no"
    except ValueError:
        return "no"

print("----Assess a new product-----")
user_input=input("Please enter product name:")
while valid_product(user_input) == "no" or valid_product(user_input) == "":#checking if input is valid ie no number and blank
    print("Invalid input Please enter a product name")
    user_input=input("Please enter product name:")
product_name= user_input# saving user input into varible 
print(f"{product_name}")#testing line

print("Category:\n1. Dairy & Eggs\n2. Bakery\n3. Meat & Seafood\n4. Fruits & Vegetables\n5. Frozen Food\n6. Beverages\n7. Other")
user_input=input("Please enter category number:")
while user_input.isdigit() ==False:
    print("Invalid input Please enter a number")
    user_input=input("Please enter category number:")
product_category= int(user_input)# saving user input into varible

user_input=input("Quantity in stock:")
while valid_stock(user_input) == "no" or valid_stock(user_input) == "":#checking if input is valid ie no number and blank
    print("Invalid input Please enter a number")
    user_input=input("Quantity in stock:")
product_amt = int(user_input)# saving user input into varible
print(f"{product_amt}")#testing line

user_input=input("Please enter expiry date(yyyy-mm-dd):")
while valid_date(user_input) == "no":
    print("Invalid date format or date too close to current date.(minimum 30 days from current date)")
    user_input=input("Please enter expiry date(yyyy-mm-dd):")
product_expiry = valid_date(user_input)# saving user input into varible
print(f"{product_expiry}")#testing line

user_input=input("Please enter product price per unit($):")
while valid_stock(user_input) == "no" or valid_stock(user_input) == "":#checking if input is valid ie no number and blank
    print("Invalid input Please enter a number")
    user_input=input("Please enter product price per unit($):")
product_price = float(user_input)# saving user input into variable and converting to float
print(f"{product_price}")#testing line

product_info = {# creating a dictionary to store product information
    "name": product_name,
    "category": product_category,
    "quantity": product_amt,
    "expiry_date": product_expiry.strftime(DATE_FORMAT),
    "price_per_unit": product_price
}
#with open("product_info.json", "a") as file:
#    json.dump(product_info, file)#creating and reading into json file 