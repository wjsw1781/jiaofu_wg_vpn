from ._anvil_designer import page_natipTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class page_natip(page_natipTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        self.repeating_panel_1.items = app_tables.nat_table.search()

        # Any code you write here will run before the form opens.

    def button_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        info = self.info.text
        used_ip_froms = []
        for r in app_tables.nat_table.search():
            used_ip_froms.append(['ip_use_from'])
            used_ip_froms.append(['ip_use_to'])

        available_from = None
        available_to = None

        # Iterate through possible second octet values (0 to 254)
        for x in range(255): # Covers 10.0.0.0/24 to 10.254.0.0/24
            potential_ip_from = f"10.{x}.0.0"
            potential_ip_to = f"10.{x+1}.0.255"

            # Check if this IP range is not already in use
            if potential_ip_from not in used_ip_froms:
                available_from = potential_ip_from
                available_to = potential_ip_to
                break # Found an available range, exit loop

        app_tables.nat_table.add_row(info=info, ip_use_from=available_from, ip_use_to=available_to)
        self.refresh_data_bindings()
