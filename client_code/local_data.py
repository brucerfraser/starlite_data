import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

global FLIGHTS
FLIGHTS = []


def load_up():
  global FLIGHTS
  FLIGHTS = anvil.server.call('flight_records')

def package_flights(package):
  """
  Filters and sorts FLIGHTS based on the given package dictionary.

  Args:
      package (dict): A dictionary with 'years' and 'months' as keys, each containing a list of strings.

  Returns:
      list: Filtered and sorted list of flights.
  """
  global FLIGHTS
  print(FLIGHTS[34]['FltDate'].month)
  # Extract years and months from the package
  years = package.get('years', [])
  months = package.get('months', [])

  # Filter FLIGHTS based on years and months
  filtered_flights = [
      flight for flight in FLIGHTS
      if str(flight['FltDate'].year) in years and str(flight['FltDate'].month) in months
  ]

  # Sort the filtered flights by date (newest to oldest)
  sorted_flights = sorted(filtered_flights, key=lambda x: x['FltDate'], reverse=True)

  return sorted_flights
