Problem Statement and Target Users

Problem Statement:
F&B merchants / supermarkets may throw out bulk batches of unsold, near expiry ingredients and products because staff or existing systems may not identify that the product is near its expiry date or  there is too much inventory to be sold within a short period of time . 

Our application aims to help identify such products and recommend discounts early to help alleviate food and product waste.

Target Users/Audiences:
Supermarket staff
F&B outlet managers

User Inputs:
Product Name / Category
Quantity In Stock
Expiry date
Current selling price

AI Processing Layer:

Dynamic Action Plans: AI analyses the product type, quantity, demand, and time remaining before expiry to recommend suitable actions, such as applying discounts to selected products 

Estimate Waste Cost: AI predicts the amount of savings if the recommended action plan is executed.

Predict Future Demand: AI estimates how much of the product is likely to be sold before its expiry date

AI can help to generate these outputs:
Identify products at risk of expiring
Discounts based on time left to expiry date 
Estimate quantity that may remain unsold

Logic Layer:
Validate inputs such as quantity, price, and expiry date
Check whether the product is near its expiry date
Products that are not near expiry date won’t have discount recommendation
Calculate the final price after the recommended discount

Data Layer: 
Stores the product information in the data file
Retrieve existing product information from data file
Filter products based on expiry dates
Update existing products information in the data file

Output Layer:
Display product nearing their expiry dates  
Display recommend discount percentages based on time to expiry
Display predicted unsold quantities
Display formatted stock tables containing quantity, price, discount and expiry date


Business Rules:

Food safety:
The application must not recommend expired products for sale. If a product's expiry date has already passed the current date, it will be marked as expired and no discount will be recommended. 

Cost regulation:
The application must not recommend a 100% discount. A maximum discount should be set to ensure that product is still sold at a reasonable price

Overlapping value 
The application must not stack discounts on products that are already discounted due to a previous application recommendation

Discount Approval
AI-generated discounts are recommendations only and must be approved by staff before they are applied.
 

Group Repository URL: https://github.com/jasonp-dev2/INF1103-Project1-P1-G7
