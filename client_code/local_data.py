import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime, timezone, timedelta

global FLIGHTS
FLIGHTS = []

# Define a mapping of month numbers to month names
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def load_up():
    """Load flight data and get latest data version info.
    
    Returns:
        dict: {'latest_log_date': datetime} for display in UI
    """
    global FLIGHTS
    FLIGHTS = anvil.server.call('flight_records')
    
    # Call api_handler to get latest log date
    result = anvil.server.call('api_handler')
    
    # Adjust the latest_log_date to local time
    if 'latest_log_date' in result:
        utc_time = result['latest_log_date']
        # Define your local time zone offset (e.g., UTC-5 for EST without DST)
        local_offset = timedelta(hours=+2)  # Replace with your local offset
        local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(local_offset))
        result['latest_log_date'] = local_time
    
    return result

def package_flights(package):
    """
    Filters and sorts FLIGHTS based on the given package dictionary.

    Args:
        package (dict): A dictionary with keys 'years', 'months', 'ac_type', 'rego', 'cff_base', and 'cff_client',
                        each containing a list of strings.

    Returns:
        list: Filtered and sorted list of flights.
    """
    global FLIGHTS

    # Extract filter criteria from the package
    years = package.get('years', [])
    months = package.get('months', [])
    ac_types = package.get('ac_type', [])
    regos = package.get('rego', [])
    cff_bases = package.get('cff_base', [])
    cff_clients = package.get('cff_client', [])

    # Filter FLIGHTS based on the package criteria
    filtered_flights = [
        flight for flight in FLIGHTS
        if str(flight['FltDate'].year) in years and
           MONTH_NAMES[flight['FltDate'].month - 1] in months and
           flight['ACType'] in ac_types and
           flight['Rego'] in regos and
           flight['CFF_Base_of_Operation'] in cff_bases and
           flight['CFF_Client'] in cff_clients
    ]

    # Sort the filtered flights by date (newest to oldest)
    sorted_flights = sorted(filtered_flights, key=lambda x: x['FltDate'], reverse=True)

    return sorted_flights
