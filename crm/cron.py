from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    """Logs a timestamped heartbeat message to /tmp/crm_heartbeat_log.txt and verifies GraphQL endpoint."""
    log_file = "/tmp/crm_heartbeat_log.txt"
    now = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{now} CRM is alive\n"

    # Append to log file
    with open(log_file, "a") as f:
        f.write(message)

    # Optional: Query GraphQL 'hello' field
    try:
        # Define the transport
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=False,
        )

        # Create the GraphQL client
        client = Client(transport=transport, fetch_schema_from_transport=False)

        # Define query
        query = gql("{ hello }")

        # Execute query
        response = client.execute(query)
        hello_message = response.get("hello", "No response")

        # Log the response
        with open(log_file, "a") as f:
            f.write(f"{now} GraphQL endpoint responded: {hello_message}\n")

    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{now} GraphQL query failed: {e}\n")


def update_low_stock():
    """Runs a GraphQL mutation to restock low-stock products and logs the updates."""
    log_file = "/tmp/low_stock_updates_log.txt"
    now = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    try:
        # Setup GraphQL transport
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=False,
        )
        client = Client(transport=transport, fetch_schema_from_transport=False)

        # Define GraphQL mutation
        mutation = gql("""
        mutation {
            updateLowStockProducts {
                success
                updatedProducts {
                    name
                    stock
                }
            }
        }
        """)

        # Execute the mutation
        response = client.execute(mutation)
        result = response.get("updateLowStockProducts", {})

        updated = result.get("updatedProducts", [])
        success_message = result.get("success", "No message returned")

        # Log to file
        with open(log_file, "a") as f:
            f.write(f"{now} - {success_message}\n")
            for product in updated:
                f.write(f"{now} - Product: {product['name']} | Stock: {product['stock']}\n")

    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{now} - ERROR: {e}\n")
