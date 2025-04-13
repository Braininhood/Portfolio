# Prompt the user for a greeting
greeting = input("Greeting: ").strip().lower()

# Check the greeting conditions
if greeting.startswith("hello"):
    print("$0")
elif greeting.startswith("h"):
    print("$20")
else:
    print("$100")
