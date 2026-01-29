from ._anvil_designer import comp_controlsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...local_data import FLIGHTS,package_flights
from datetime import datetime



class comp_controls(comp_controlsTemplate):
  def __init__(self, year=None, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # we need to keep a watch on if an "All" has been clicked or not
    self.alls = {'years': False, 'months': True, 'ac_type': True, 'rego': True, 'cff_base': True, 'cff_client': True}
    self.package = {'years': [], 'months': [], 'ac_type': [], 'rego': [], 'cff_base': [], 'cff_client': []}
    self.total_years = 0

    # Ensure year argument is a string if provided
    if year:
      year = str(year)
    else:
      year = str(datetime.now().year)  # Default to the current year

    # Load dropdowns
    self.load_years(year)
    self.load_months()
    self.load_ac_type()
    self.load_rego()
    self.load_cff_base()
    self.load_cff_client()

  def load_years(self, year):
    years = sorted({flight['FltDate'].year for flight in FLIGHTS if flight.get('FltDate')})
    self.total_years = len(years)
    self.msdd_years.items = ["All"] + [str(year) for year in years]
    self.msdd_years.selected = [str(year)]
    self.package['years'] = self.msdd_years.selected

  def load_months(self):
    months = ["All",
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ]
    self.msdd_months.items = months
    self.msdd_months.selected = months
    mons = self.msdd_months.selected
    mons.remove('All')
    self.package['months'] = mons

  def load_ac_type(self):
    ac_types = sorted({flight['ACType'] for flight in FLIGHTS if flight.get('ACType')})
    self.msdd_ac_type.items = ["All"] + ac_types
    self.msdd_ac_type.selected = ac_types
    self.package['ac_type'] = ac_types

  def load_rego(self):
    regos = sorted({flight['Rego'] for flight in FLIGHTS if flight.get('Rego')})
    self.msdd_rego.items = ["All"] + regos
    self.msdd_rego.selected = regos
    self.package['rego'] = regos

  def load_cff_base(self):
    cff_bases = sorted({flight['CFF_Base_of_Operation'] for flight in FLIGHTS if flight.get('CFF_Base_of_Operation')})
    self.msdd_cff_base.items = ["All"] + cff_bases
    self.msdd_cff_base.selected = cff_bases
    self.package['cff_base'] = cff_bases

  def load_cff_client(self):
    cff_clients = sorted({flight['CFF_Client'] for flight in FLIGHTS if flight.get('CFF_Client')})
    self.msdd_cff_client.items = ["All"] + cff_clients
    self.msdd_cff_client.selected = cff_clients
    self.package['cff_client'] = cff_clients

  @handle("msdd_years", "change")
  def msdd_years_change(self, **event_args):
    self.handle_change("years", self.msdd_years, self.total_years)

  @handle("msdd_months", "change")
  def msdd_months_change(self, **event_args):
    self.handle_change("months", self.msdd_months, 12)

  @handle("msdd_ac_type", "change")
  def msdd_ac_type_change(self, **event_args):
    self.handle_change("ac_type", self.msdd_ac_type, len(self.msdd_ac_type.items) - 1)

  @handle("msdd_rego", "change")
  def msdd_rego_change(self, **event_args):
    self.handle_change("rego", self.msdd_rego, len(self.msdd_rego.items) - 1)

  @handle("msdd_cff_base", "change")
  def msdd_cff_base_change(self, **event_args):
    self.handle_change("cff_base", self.msdd_cff_base, len(self.msdd_cff_base.items) - 1)

  @handle("msdd_cff_client", "change")
  def msdd_cff_client_change(self, **event_args):
    self.handle_change("cff_client", self.msdd_cff_client, len(self.msdd_cff_client.items) - 1)

  def handle_change(self, key, dropdown, total_items):
    selected_keys = dropdown.selected
    if 'All' in selected_keys:
      if not self.alls[key]:
        self.alls[key] = True
        all_keys = dropdown.items
        dropdown.selected = all_keys
        try:
          all_keys.remove("All")
        except Exception:
          pass
        self.package[key] = all_keys
      else:
        if len(selected_keys) < total_items + 1:
          self.alls[key] = False
          try:
            selected_keys.remove('All')
          except Exception:
            pass
          dropdown.selected = selected_keys
          self.package[key] = selected_keys
    else:
      if self.alls[key]:
        self.alls[key] = False
        dropdown.selected = []
        self.package[key] = []
      else:
        self.package[key] = dropdown.selected
    self.send_pack()

  def send_pack(self, **event_args):
    self.parent.raise_event('x-listen', package=self.package)

  @handle('btn_more','click')
  def more_summary(self,**event_args):
    from ...pop_ups.summary_form import summary_form
    result = package_flights(self.package)
    sum = summary_form(flights=result['sorted_flights'])
    alert(sum,buttons=[],large=True)
