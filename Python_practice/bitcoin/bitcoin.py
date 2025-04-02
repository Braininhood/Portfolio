import sys
import requests


def main():
    # Check if command-line argument is provided
    if len(sys.argv) != 2:
        print("Usage: python bitcoin.py <number_of_bitcoins>")
        sys.exit(1)

    # Try to convert command-line argument to float
    try:
        bitcoins = float(sys.argv[1])
    except ValueError:
        print("Invalid number of bitcoins.")
        sys.exit(1)

    # Query the CoinDesk API
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()  # Parse JSON response

        # Get the current price of Bitcoin in USD
        price_per_bitcoin = data["bpi"]["USD"]["rate_float"]

        # Calculate the total cost in USD
        total_cost = bitcoins * price_per_bitcoin

        # Output the total cost formatted to 4 decimal places
        print(f"${total_cost:,.4f}")

    except requests.RequestException:
        print("Failed to fetch data from CoinDesk.")
        sys.exit(1)


if __name__ == "__main__":
    main()
