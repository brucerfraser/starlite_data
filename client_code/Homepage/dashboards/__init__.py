from ._anvil_designer import dashboardsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class dashboards(dashboardsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.load_controls()
    self.cp_controls.set_event_handler('x-listen',self.act)

  def load_controls(self,**event_args):
    from ..comp_controls import comp_controls
    self.controller = comp_controls()
    self.cp_controls.add_component(self.controller)

  def act(self,package,**event_args):
    pass
