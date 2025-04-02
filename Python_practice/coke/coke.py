def coke_machine():
    cost = 50
    amount_due = cost
    accepted_coins = [25, 10, 5]

    while amount_due > 0:
        print(f"Amount Due: {amount_due}")
        try:
            coin = int(input("Insert Coin: "))
            if coin in accepted_coins:
                amount_due -= coin
            else:
                print("Coin not accepted.")
        except ValueError:
            print("Invalid input. Please insert a coin.")

    # If amount_due is negative, that means there's change to be given
    change_owed = abs(amount_due)
    print(f"Change Owed: {change_owed}")


coke_machine()
