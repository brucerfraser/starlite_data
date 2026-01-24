from ._anvil_designer import dashboardsTemplate
from anvil import *
from ..graph_data import create_graphs
from ..local_data import FLIGHTS

class dashboards(dashboardsTemplate):
    def __init__(self, package, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Create graphs
        graphs = create_graphs(package)

        # Position graphs in the column panel
        self.graphs_panel.clear()
        for graph in graphs:
            self.graphs_panel.add_component(PlotlyPanel(graph))