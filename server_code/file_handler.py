import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

@anvil.server.callable
def save_file(file, description):
    """Saves a file along with its description to the database."""
    app_tables.Flights.add_row(file=file, description=description)
