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
    # we need to keep a watch on if an "All" has been clicked or not
    self.alls = {'years': False, 'months': True}
    self.package = {'years':[],'months':[]}
    self.total_years = 0
    # Ensure year argument is a string if provided
    if year:
      year = str(year)
    else:
      year = str(datetime.now().year)  # Default to the current year

    # Load years and months into the dropdowns
    self.load_years(year)
    self.load_months()

  def load_years(self, year):
    # Extract all unique years from FLIGHTS
    years = sorted({flight['FltDate'].year for flight in FLIGHTS if flight.get('FltDate')})
    self.total_years = len(years)
    # Add "All" option at the top
    self.msdd_years.items = ["All"] + [str(year) for year in years]
    self.msdd_years.selected = [str(year)]
    self.package['years'] = self.msdd_years.selected

  def load_months(self):
    # Define month names
    months = ["All",
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ]
    # Add "All" option at the top
    self.msdd_months.items = months
    # Select all months by default
    self.msdd_months.selected = months
    mons = self.msdd_months.selected
    mons.remove('All')
    self.package['months'] = mons

  @handle("msdd_years", "change")
  def msdd_years_change(self, **event_args):
    # Handle "All" option for years
    selected_keys = self.msdd_years.selected
    if 'All' in selected_keys:
      # Select all years if "All" is selected and wasn't in the previous selection
      if not self.alls['years']:
        self.alls['years'] = True
        all_keys = self.msdd_years.items
        self.msdd_years.selected = all_keys
        try:
          all_keys.remove("All")
        except Exception as e:
          pass
        self.package['years'] = all_keys
      else:
        # we must deselect All if an item has been deselcted
        if len(selected_keys) < self.total_years + 1:
          self.alls['years'] = False
          # Remove 'All' from selection
          try:
            selected_keys.remove('All')
          except Exception as e:
            pass
          self.msdd_years.selected = selected_keys
          self.package['years'] = selected_keys
    else:
      # We must check if All was previously selected
      if self.alls['years']:
        self.alls['years'] = False
        self.msdd_years.selected = []
        self.package['years'] = []
      else:
        # Just a normal change
        self.package['years'] = self.msdd_years.selected
    

  @handle("msdd_months", "change")
  def msdd_months_change(self, **event_args):
    # Handle "All" option for months
    selected_keys = self.msdd_months.selected
    if 'All' in selected_keys:
      # Select all months if "All" is selected and wasn't in the previous selection
      if not self.alls['months']:
        self.alls['months'] = True
        all_keys = self.msdd_months.items
        self.msdd_months.selected = all_keys
        try:
          all_keys.remove("All")
        except Exception as e:
          pass
        self.package['months'] = all_keys
      else:
        # we must deselect All if an item has been deselcted
        if len(selected_keys) < 13:
          self.alls['months'] = False
          # Remove 'All' from selection
          try:
            selected_keys.remove('All')
          except Exception as e:
            pass
          self.msdd_months.selected = selected_keys
          self.package['months'] = selected_keys
    else:
      # We must check if All was previously selected
      if self.alls['months']:
        self.alls['months'] = False
        self.msdd_months.selected = []
        self.package['months'] = []
      else:
        # Just a normal change
        self.package['months'] = self.msdd_months.selected

  def send_pack(self,**event_args):
    self.parent.raise_event('x-listen',package=self.package)
