def camel_to_snake(camel):
    snake = ""
    for c in camel:
        if c.isupper():
            snake += "_" + c.lower()
        else:
            snake += c
    return snake


# Prompt user for input
camel_case = input("Enter a variable name in camel case: ")
# Convert to snake case and print result
snake_case = camel_to_snake(camel_case)
print("In snake case:", snake_case)
