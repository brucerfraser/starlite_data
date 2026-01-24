from ._anvil_designer import comp_controlsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...local_data import FLIGHTS
from datetime import datetime


class comp_controls(comp_controlsTemplate):
  def __init__(self, year=None, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Ensure year argument is a string if provided
    if year is not None:
      year = str(year)

    # Load years and months into the dropdowns
    self.load_years(year)
    self.load_months()

  def load_years(self, year):
    # Extract all unique years from FLIGHTS
    years = sorted({flight['FltDate'].year for flight in FLIGHTS if flight.get('FltDate')})
    # Add "All" option at the top
    self.msdd_years.items = [{'key': 'All', 'value': 'all'}] + [{'key': str(year), 'value': year} for year in years]

    # Set the selected year
    if year is None:
      year = str(datetime.now().year)  # Default to the current year
    self.msdd_years.selected = [year]

  def load_months(self):
    # Define month names
    months = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ]
    # Add "All" option at the top
    self.msdd_months.items = [{'key': 'All', 'value': 'all'}] + [{'key': month, 'value': i + 1} for i, month in enumerate(months)]

    # Select all months by default
    self.msdd_months.selected = [item['key'] for item in self.msdd_months.items]

  @handle("msdd_years", "change")
  def msdd_years_change(self, **event_args):
    # Handle "All" option for years
    selected_keys = self.msdd_years.selected
    if 'All' in selected_keys:
      # Select all years if "All" is selected
      all_keys = [item['key'] for item in self.msdd_years.items]
      self.msdd_years.selected = all_keys
    elif not selected_keys:
      # Deselect all if no keys are selected
      self.msdd_years.selected = []
    print("Selected years:", self.msdd_years.selected)

  @handle("msdd_months", "change")
  def msdd_months_change(self, **event_args):
    # Handle "All" option for months
    selected_keys = self.msdd_months.selected
    if 'All' in selected_keys:
      # Select all months if "All" is selected
      all_keys = [item['key'] for item in self.msdd_months.items]
      self.msdd_months.selected = all_keys
    elif not selected_keys:
      # Deselect all if no keys are selected
      self.msdd_months.selected = []
    print("Selected months:", self.msdd_months.selected)
