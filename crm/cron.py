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
