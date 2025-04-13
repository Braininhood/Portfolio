# Prompt the user for an arithmetic expression
expression = input("Expression: ")

# Split the expression into x, y, and z
x, y, z = expression.split(" ")

# Convert x and z to integers
x = int(x)
z = int(z)

# Calculate the result based on the operator
if y == "+":
    result = x + z
elif y == "-":
    result = x - z
elif y == "*":
    result = x * z
elif y == "/":
    result = x / z

# Output the result formatted to one decimal place
print(f"{result:.1f}")
