from ._anvil_designer import recordsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...local_data import FLIGHTS
from datetime import datetime


class records(recordsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.controller = None
    # Any code you write here will run before the form opens.

  @handle("", "show")
  def form_show(self, **event_args):
    # Get the current year
    self.load_controls()
    current_year = datetime.now().year

    # Filter FLIGHTS for the current year and sort by date (newest to oldest)
    self.rp_records.items = sorted(
        [flight for flight in FLIGHTS if flight.get('FltDate') and flight['FltDate'].year == current_year],
        key=lambda x: x['FltDate'],
        reverse=True
    )

  def load_controls(self,**event_args):
    from ..comp_controls import comp_controls
    self.controller = comp_controls(2026)
    self.cp_controls.add_component(self.controller)