from ._anvil_designer import page_use_sh_py_toolsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class page_use_sh_py_tools(page_use_sh_py_toolsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def make_91_click(self, **event_args):
        """This method is called when the button is clicked"""
        pass
