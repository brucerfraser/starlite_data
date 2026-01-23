from ._anvil_designer import HomepageTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..EntryEdit import EntryEdit

class Homepage(HomepageTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run when the form opens.
    self.refresh_entries()
      # Set an event handler on the RepeatingPanel (our 'entries_panel')
    self.entries_panel.set_event_handler('x-delete-entry', self.delete_entry)

  def add_entry_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    # Initialise an empty dictionary to store the user inputs
    new_entry = {}
    # Open an alert displaying the 'EntryEdit' Form
    save_clicked = alert(
      content=EntryEdit(item=new_entry),
      title="Add Entry",
      large=True,
      buttons=[("Save", True), ("Cancel", False)]
    )
    # If the alert returned 'True', the save button was clicked.
    if save_clicked:
      anvil.server.call('add_entry', new_entry)
      self.refresh_entries()
    
  def refresh_entries(self):
     # Load existing entries from the Data Table, 
     # and display them in the RepeatingPanel
     # self.entries_panel.items = anvil.server.call('get_entries')
     pass

  def delete_entry(self, entry, **event_args):
    # Delete the entry
    anvil.server.call('delete_entry', entry)
    # Refresh entry to remove the deleted entry from the Homepage
    self.refresh_entries()

  @handle("file_loader_1", "change")
  def upload(self,file,**event_args):
    """This method is called when a file is loaded into the FileLoader"""
    if file is not None:
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
          print(f"Completed: total rows {total_rows}")
          alert(f"File processed successfully!\n\nTotal rows in file: {total_rows}")
        else:
          print(f"Rows completed: {rows_completed}")

