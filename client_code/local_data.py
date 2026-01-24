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
  global FLIGHTS
  pass
  