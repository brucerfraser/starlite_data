from ._anvil_designer import summary_formTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...local_data import FLT_DATE_COLUMN, BLOCK_TIME_COLUMN, AIR_TIME_COLUMN, REGO_COLUMN, AC_TYPE_COLUMN, CLIENT_COLUMN, BASE_OF_OPERATION_COLUMN


class summary_form(summary_formTemplate):
  def __init__(self, flights, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Store the flights data
    self.flights = flights

    # Populate the dropdown with summary options
    self.dd_summary_type.items = [
        ("By Registration", "rego"),
        ("By Type", "type"),
        ("By Client", "client"),
        ("By Base", "base")
    ]

    # Set the default dropdown value
    self.dd_summary_type.selected_value = "rego"

    # Call the update function to populate the summary
    self.update_summary()

  @handle('dd_summary_type','change')
  def dd_summary_change(self, **event_args):
    """Called when the dropdown value changes."""
    self.update_summary()

  def update_summary(self):
    """Update the RichText component based on the selected summary type."""
    # Get the selected summary type
    summary_type = self.dd_summary_type.selected_value

    # Group flights based on the selected summary type
    if summary_type == "rego":
        group_key = REGO_COLUMN
        title = "Summary by Registration"
    elif summary_type == "type":
        group_key = AC_TYPE_COLUMN
        title = "Summary by Aircraft Type"
    elif summary_type == "client":
        group_key = CLIENT_COLUMN
        title = "Summary by Client"
    elif summary_type == "base":
        group_key = BASE_OF_OPERATION_COLUMN
        title = "Summary by Base"
    else:
        group_key = None
        title = "Summary"

    # Group the flights
    grouped_data = {}
    for flight in self.flights:
        key = flight.get(group_key, "Unknown")
        if key not in grouped_data:
            grouped_data[key] = {"air_time": 0, "block_time": 0}
        grouped_data[key]["air_time"] += flight.get(AIR_TIME_COLUMN, 0) or 0
        grouped_data[key]["block_time"] += flight.get(BLOCK_TIME_COLUMN, 0) or 0

    # Generate the summary text
    min_date = min(flight[FLT_DATE_COLUMN] for flight in self.flights)
    max_date = max(flight[FLT_DATE_COLUMN] for flight in self.flights)
    summary_title = f"<h2><b>{title}</b></h2>"
    summary_period = f"<p><i>For the period {min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}</i></p>"
    summary_items = ""
    for key, data in grouped_data.items():
        summary_items += f"""
        <p style="color: #007BFF;">
            <b>{key}</b>: Air Time: {data['air_time']:.1f} hrs, Block Time: {data['block_time']:.1f} hrs
        </p>
        """

    # Update the RichText component
    self.rt_summary.content = f"""
    {summary_title}
    {summary_period}
    {summary_items}
    """

  @handle('btn_close','click')
  def close_me(self,**event_args):
    self.raise_event('x-close-alert')
