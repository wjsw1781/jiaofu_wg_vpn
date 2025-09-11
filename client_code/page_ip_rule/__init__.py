from ._anvil_designer import page_ip_ruleTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class page_ip_rule(page_ip_ruleTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        self.repeating_panel_1.items = app_tables.wg_ip_rule.search()
        

    