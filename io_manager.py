from datetime import datetime, date, timedelta
import json

DATE_FORMAT= "%Y-%m-%d"
current_date = date.today()
minimum_expiry = current_date + timedelta(days=30)

def valid_product(Userinput):
    if Userinput.isdigit():
        return "no"
    else:
        return str(Userinput)

def valid_stock (Userinput):
    if Userinput.isdigit():
        return (Userinput)
    else:
        return "no"

def valid_date(Userinput):
    try:
        expiry_date = date.strptime(Userinput, DATE_FORMAT)
        if expiry_date >= minimum_expiry:
            return expiry_date
        else:
            return "no"
    except ValueError:
        return "no"



def get_product_info():
 print("----Assess a new product-----")
 Userinput=input("Please enter product name:")
 while valid_product(Userinput) == "no" or valid_product(Userinput) == "":#checking if input is valid ie no number and blank
    print("Invalid input Please enter a product name")
    Userinput=input("Please enter product name:")
 product_name= Userinput# saving user input into varible 


 print("Category:\n1. Dairy & Eggs\n2. Bakery\n3. Meat & Seafood\n4. Fruits & Vegetables\n5. Frozen Food\n6. Beverages\n7. Other")
 Userinput=input("Please enter category number:")
 while Userinput.isdigit() ==False:
    print("Invalid input Please enter a number")
    Userinput=input("Please enter category number:")
 product_category= int(Userinput)# saving user input into varible

 Userinput=input("Quantity in stock:")
 while valid_stock(Userinput) == "no" or valid_stock(Userinput) == "":#checking if input is valid ie no number and blank
    print("Invalid input Please enter a number")
    user_input=input("Quantity in stock:")
 product_amt = int(Userinput)# saving user input into varible


 Userinput=input("Please enter expiry date(yyyy-mm-dd):")
 while valid_date(Userinput) == "no":
    print("Invalid date format or date too close to current date.(minimum 30 days from current date)")
    Userinput=input("Please enter expiry date(yyyy-mm-dd):")
 product_expiry = valid_date(Userinput)# saving user input into varible


 Userinput=input("Please enter product price per unit($):")
 while valid_stock(Userinput) == "no" or valid_stock(Userinput) == "":#checking if input is valid ie no number and blank
    print("Invalid input Please enter a number")
    Userinput=input("Please enter product price per unit($):")
 product_price = float(Userinput)# saving user input into variable and converting to float

 product_info = {# creating a dictionary to store product information
    "name": product_name,
    "category": product_category,
    "quantity": product_amt,
    "expiry_date": product_expiry,
    "price_per_unit": product_price
}
 return product_info

get_product_info()