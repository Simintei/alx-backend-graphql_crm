#!/usr/bin/env python3
"""
Script: send_order_reminders.py
Description: Queries pending orders from GraphQL endpoint and logs reminders.
"""

from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

import sys

LOG_FILE = "/tmp/order_reminders_log.txt"

def main():
    # Define GraphQL transport
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
    )

    # Initialize GraphQL client
    client = Client(transport=transport, fetch_schema_from_transport=False)

    # Calculate date range (last 7 days)
    today = datetime.now()
    week_ago = today - timedelta(days=7)

    # GraphQL query for orders in the last 7 days
    query = gql(f"""
    query {{
        allOrders(orderDate_Gte: "{week_ago.date()}", orderDate_Lte: "{today.date()}") {{
            id
            customer {{
                email
            }}
        }}
    }}
    """)

    try:
        response = client.execute(query)
        orders = response.get("allOrders", [])
    except Exception as e:
        with open(LOG_FILE, "a") as log:
            log.write(f"{datetime.now()} - ERROR: {e}\n")
        sys.exit(1)

    # Log results
    with open(LOG_FILE, "a") as log:
        for order in orders:
            order_id = order.get("id")
            customer_email = order.get("customer", {}).get("email")
            log.write(f"{datetime.now()} - Order ID: {order_id}, Customer: {customer_email}\n")

    print("Order reminders processed!")

if __name__ == "__main__":
    main()
