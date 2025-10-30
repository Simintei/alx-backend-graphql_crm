#!/bin/bash
# Script: clean_inactive_customers.sh
# Description: Deletes customers with no orders in the past year.

LOG_FILE="/tmp/customer_cleanup_log.txt"

# Run Django shell command to delete inactive customers
DELETED_COUNT=$(python manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer
one_year_ago = timezone.now() - timedelta(days=365)
inactive = Customer.objects.filter(orders__isnull=True, created_at__lt=one_year_ago)
count = inactive.count()
inactive.delete()
print(count)
")

# Log with timestamp
echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Deleted customers: ${DELETED_COUNT}\" >> ${LOG_FILE}
