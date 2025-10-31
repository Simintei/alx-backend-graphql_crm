from datetime import datetime
import requests

def log_crm_heartbeat():
    """Logs a timestamped heartbeat message to /tmp/crm_heartbeat_log.txt"""
    log_file = "/tmp/crm_heartbeat_log.txt"
    now = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{now} CRM is alive\n"

    # Append to log file
    with open(log_file, "a") as f:
        f.write(message)

    # Optional: Ping the GraphQL 'hello' field to ensure the endpoint is responsive
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ hello }"},
            timeout=5
        )
        # Log endpoint status
        with open(log_file, "a") as f:
            if response.status_code == 200:
                f.write(f"{now} GraphQL endpoint responsive\n")
            else:
                f.write(f"{now} GraphQL endpoint error: {response.status_code}\n")
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{now} GraphQL request failed: {e}\n")
