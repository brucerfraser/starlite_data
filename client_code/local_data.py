import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

global FLIGHTS
FLIGHTS = []


def load_up():
  global FLIGHTS
  for r in app_tables.flights.search():
    FLIGHTS.append(dict(r))
