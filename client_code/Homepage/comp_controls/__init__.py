from ._anvil_designer import comp_controlsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...local_data import FLIGHTS
from datetime import datetime


class comp_controls(comp_controlsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Load years and months into the dropdowns
    self.load_years()
    self.load_months()

  def load_years(self):
    # Extract all unique years from FLIGHTS
    years = sorted({flight['FltDate'].year for flight in FLIGHTS if flight.get('FltDate')})
    # Add "All" option at the top
    self.msdd_years.items = [{'key': 'all', 'value': 'All'}] + [{'key': year, 'value': str(year)} for year in years]

  def load_months(self):
    # Define month names
    months = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ]
    # Add "All" option at the top
    self.msdd_months.items = [{'key': 'all', 'value': 'All'}] + [{'key': i + 1, 'value': month} for i, month in enumerate(months)]

  @handle("msdd_years","change")
  def msdd_years_change(self,count,total, **event_args):
    # Handle "All" option for years
    selected_keys = self.msdd_years.selected_keys
    if 'all' in selected_keys:
      # Select all years if "All" is selected
      all_keys = [item['key'] for item in self.msdd_years.items if item['key'] != 'all']
      self.msdd_years.selected_keys = all_keys
    elif not selected_keys:
      # Deselect all if no keys are selected
      self.msdd_years.selected_keys = []
    print("Selected years:", self.msdd_years.selected_keys)

  @handle("msdd_months", "change")
  def msdd_months_change(self,count,total **event_args):
    # Handle "All" option for months
    selected_keys = self.msdd_months.selected_keys
    if 'all' in selected_keys:
      # Select all months if "All" is selected
      all_keys = [item['key'] for item in self.msdd_months.items if item['key'] != 'all']
      self.msdd_months.selected_keys = all_keys
    elif not selected_keys:
      # Deselect all if no keys are selected
      self.msdd_months.selected_keys = []
    print("Selected months:", self.msdd_months.selected_keys)
