import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

global FLIGHTS
FLIGHTS = []

# Define a mapping of month numbers to month names
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def load_up():
  global FLIGHTS
  FLIGHTS = anvil.server.call('flight_records')

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
        if (str(flight['FltDate'].year) in years if years else True) and
           (MONTH_NAMES[flight['FltDate'].month - 1] in months if months else True) and
           (flight['ACType'] in ac_types if ac_types else True) and
           (flight['Rego'] in regos if regos else True) and
           (flight['CFF_Base_of_Operation'] in cff_bases if cff_bases else True) and
           (flight['CFF_Client'] in cff_clients if cff_clients else True)
    ]

    # Sort the filtered flights by date (newest to oldest)
    sorted_flights = sorted(filtered_flights, key=lambda x: x['FltDate'], reverse=True)

    return sorted_flights
