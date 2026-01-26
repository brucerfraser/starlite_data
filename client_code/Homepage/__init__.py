from ._anvil_designer import HomepageTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..EntryEdit import EntryEdit
from .. import local_data

class Homepage(HomepageTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run when the form opens.
    local_data.load_up()
    self.btn_records_click()
    

  @handle("file_loader_1", "change")
  def upload(self,file,**event_args):
    """This method is called when a file is loaded into the FileLoader"""
    if file is not None:
      self.file_loader_1.clear()
      rows_completed = 0
      complete = False
      total_rows = 0
      
      # Loop until all rows are processed
      while not complete:
        result = anvil.server.call('receive_file', file, rows_completed)
        complete = result['complete']
        total_rows = result['total_rows']
        rows_completed = result['rows_processed']
        
        if complete:
          msg = "File uploaded, \n{t} Total rows, \n{s} Rows saved".format(t=total_rows,
                                                                          s=rows_completed)
          alert(msg)
        else:
          print(f"Rows completed: {rows_completed}")

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
      msg = "File uploaded, \n{t} Total rows, \n{s} Rows saved".format(t=total_rows,
                                                                       s=rows_completed)
      alert(msg)
    else:
      alert("API call unsuccessful")
