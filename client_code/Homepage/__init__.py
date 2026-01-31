from ._anvil_designer import HomepageTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..EntryEdit import EntryEdit
from .. import local_data
from datetime import datetime

class Homepage(HomepageTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run when the form opens.
    result = local_data.load_up()
    # print(result)
    # Format and display data version
    self.update_data_label(result)
    
    self.btn_records_click()
    

  @handle("file_loader_1", "change")
  def upload(self,file,**event_args):
    """This method is called when a file is loaded into the FileLoader"""
    if file is not None:
      self.file_loader_1.clear()
      result = anvil.server.call('receive_file', file, source='upload')
      if result['complete']:
        msg = "File uploaded, \n{t} Total rows, \n{s} Rows saved".format(t=result['total_rows'],
                                                                        s=result['rows_processed'])
        self.update_data_label(result)
        alert(msg)
        if result['rows_processed'] > 0:
          self.reload_flights()
      

  @handle("btn_records", "click")
  def btn_records_click(self, **event_args):
    from .records import records
    self.content_panel.clear()
    self.content_panel.add_component(records())

  @handle('btn_dashboard','click')
  def btn_dashboard_click(self,**event_args):
    from .dashboards import dashboards
    self.content_panel.clear()
    self.content_panel.add_component(dashboards())

  @handle("btn_refresh", "click")
  def btn_refresh_click(self, **event_args):
    result = anvil.server.call('api_handler')
    complete = result['complete']
    total_rows = result['total_rows']
    rows_completed = result['rows_processed']

    if complete:
      msg = "API retrieved data, \n{t} Total rows, \n{s} Rows saved".format(t=total_rows,
                                                                       s=rows_completed)
      self.update_data_label(result)
      alert(msg)
      if rows_completed > 0:
        self.reload_flights()
    else:
      alert("API call unsuccessful")

  def update_data_label(self,result=None,**event_args):
    if result and result.get('latest_log_date'):
      latest_date = result['latest_log_date']
      today = datetime.now().date()

      # If date is today, show time; otherwise show date
      if latest_date.date() == today:
        date_str = latest_date.strftime('%H:%M')
      else:
        date_str = latest_date.strftime('%d %b')

      self.lbl_data_version.text = f"Data version:\nFlight records: {date_str}"

  def reload_flights(self,**event_args):
    result = local_data.load_up(api_call=False)
    self.update_data_label(result)
    self.btn_records_click()
