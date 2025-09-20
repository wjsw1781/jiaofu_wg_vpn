from ._anvil_designer import RowTemplate5Template
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class RowTemplate5(RowTemplate5Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def down_py_content_click(self, **event_args):
        """This method is called when the button is clicked"""

        name = self.item['info_desc']
        content = self.item['python_code']
        anvil.media.download(anvil.BlobMedia("text/py", content.encode(), f"{name}.py"))

    def del_py_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.item.delete()

        self.parent.parent.parent.parent.parent.repeating_panel_1.items = app_tables.tools_py_str.search()

    def button_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        t = TextBox()
        alert(content=t,title="备注一下这个节点被那个机器使用了 地点 业务方")
        if t.text:
            self.item['have_be_use'] = t.text


