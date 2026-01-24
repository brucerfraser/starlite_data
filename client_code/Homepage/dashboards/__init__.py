from ._anvil_designer import dashboardsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...graph_data import create_graphs


class dashboards(dashboardsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.load_controls()
    self.cp_controls.set_event_handler('x-listen', self.act)
    # load the first visual
    self.act(self.controller.package)

  def load_controls(self, **event_args):
    """
    Load the controller into the cp_controls container.
    """
    from ..comp_controls import comp_controls
    self.controller = comp_controls()
    self.cp_controls.add_component(self.controller)

  def act(self, package, **event_args):
    """
    Generate graphs using the package and place them in the graphs_panel.
    """
    # Clear the graphs panel
    self.graphs.clear()

    # Generate graphs using the graph_data module
    graphs = create_graphs(package)

    # Add each graph to the graphs panel
    for graph in graphs:
      self.graphs.add_component(PlotlyPanel(graph))
