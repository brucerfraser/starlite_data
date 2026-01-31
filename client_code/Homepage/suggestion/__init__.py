from ._anvil_designer import suggestionTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

class suggestion(suggestionTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)


  @handle('fu_image','change')
  def change_file(self,file,**event_args):
    try:
      self.img_picture.source = file
    except:
      pass

  @handle('btn_save','click')
  def save_click(self,**event_args):
    if self.txt_suggest.text:
      txt = self.txt_suggest.text
      if self.fu_image.file:
        file = self.fu_image.file
      else:
        file = None
      dte = datetime.now().date()
      app_tables.suggestions.add_row(date=dte,file=file,suggestion=txt)
    self.parent.raise_event('x-close-suggest')

  @handle('btn_cancel','click')
  def cancel_click(self,**event_args):
    self.parent.raise_event('x-close-suggest')
