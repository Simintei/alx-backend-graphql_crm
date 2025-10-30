import requests
import json
import datetime
import os
import sys

# --- Configuration ---
GRAPHQL_URL = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"

def get_date_seven_days_ago():
    """Calculates the date exactly 7 days ago and formats it for GraphQL filtering."""
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    # We use YYYY-MM-DD format, assuming the backend filter is date-based
    return seven_days_ago.strftime("%Y-%m-%d")

def fetch_pending_orders(min_date):
    """Fetches orders using a GraphQL query via the requests library."""
    
    # NOTE: We assume your 'allOrders' query accepts a filter argument 
    # like 'orderDate_Gte' (Greater than or Equal) from django-filter.
    query = """
    query PendingOrders($minDate: Date) {
      allOrders(orderDate_Gte: $minDate) {
        edges {
          node {
            id
            orderDate
            customer {
              email
            }
          }
        }
      }
    }
    """
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        'query': query,
        'variables': {'minDate': min_date}
    }
    
    try:
        # Use requests.post instead of gql/Client
        response = requests.post(GRAPHQL_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL Errors encountered: {data['errors']}", file=sys.stderr)
            return []
            
        return data['data']['allOrders']['edges']
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to GraphQL endpoint: {e}", file=sys.stderr)
        return []
    except KeyError:
        print("Error parsing GraphQL response structure. Check query field names.", file=sys.stderr)
        return []

def log_reminders(orders):
    """Writes order reminder entries to the log file."""
    if not orders:
        return 0

    log_entries = []
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for edge in orders:
        order = edge['node']
        # NOTE: Using a simple integer conversion for ID here. Adjust if your ID is UUID/string.
        order_id = order['id']
        customer_email = order['customer']['email'] if order.get('customer') else "N/A"
        order_date = order['orderDate']
        
        log_entry = (
            f"[{current_timestamp}] "
            f"REMINDER: Order ID {order_id} (Date: {order_date}). "
            f"Customer Email: {customer_email}"
        )
        log_entries.append(log_entry)

    try:
        with open(LOG_FILE, 'a') as f:
            f.write('\n'.join(log_entries) + '\n')
        return len(orders)
    except IOError as e:
        print(f"Error writing to log file {LOG_FILE}: {e}", file=sys.stderr)
        return 0

if __name__ == "__main__":
    min_date = get_date_seven_days_ago()
    
    # In a cron job, suppress excessive logging unless there's an issue
    orders = fetch_pending_orders(min_date)
    count = log_reminders(orders)

    if count > 0:
        print(f"Order reminders processed! Logged {count} pending orders.")
    else:
        # If no orders found, still print success message for cron job tracking
        print("Order reminders processed!")
