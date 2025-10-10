from ._anvil_designer import page_sshTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class page_ssh(page_sshTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        # 从指定位置传递过来 只限制这个 ip_to 下的业务数据
        if 'from_params' in properties:
            self.repeating_panel_1.items=properties['from_params']
        else:
            self.repeating_panel_1.items = app_tables.wg_conf.search()
        # Any code you write here will run before the form opens.
