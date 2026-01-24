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
    # Load the first visual
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
    for traces, layout in graphs:
      # Use the _make_plot helper function to create the Plot component
      plot = self._make_plot(traces, layout)
      self.graphs.add_component(plot)

  def _make_plot(self, traces, layout, *, height=320, interactive=False):
    """
    Helper function to create an Anvil Plot component.

    Args:
        traces (list): List of Plotly traces (data).
        layout (dict): Plotly layout dictionary.
        height (int): Height of the plot.
        interactive (bool): Whether the plot is interactive.

    Returns:
        Plot: An Anvil Plot component.
    """
    p = Plot()
    p.height = str(height)
    p.interactive = bool(interactive)
    p.config = {
        "doubleClick": "reset",
        "displaylogo": False,
        "scrollZoom": False,
        "responsive": True
    }
    p.data = traces
    p.layout = layout
    p.redraw()
    return p
