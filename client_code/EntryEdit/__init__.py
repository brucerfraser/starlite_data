from ._anvil_designer import EntryEditTemplate
from anvil import *
import anvil.server
from anvil.tables import app_tables


class EntryEdit(EntryEditTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    self.categories = [(cat['name'], cat) for cat in app_tables.categories.search()]
    self.category_box.items = self.categories

  def image_uploader_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    self.item['image'] = file

