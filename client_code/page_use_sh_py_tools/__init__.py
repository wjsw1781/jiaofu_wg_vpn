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

        self.repeating_panel_1.items = app_tables.tools_py_str.search()

        # Any code you write here will run before the form opens.

    def make_91_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.server.call('make_91_to_anvil')
        alert('创建成功 91 100 个客户端')

    def add_py_click(self, **event_args):
        """This method is called when the button is clicked"""
        py_content = self.py_content.text
        py_desc = self.py_desc.text
        if not(py_desc) or not(py_content):
            alert('脚本描述 脚本内容不能为空')
            return
        app_tables.tools_py_str.add_row(
            info_desc=py_desc,    
            python_code=py_content
        )
        Notification(f'添加成功 {py_desc} ').show()
        self.repeating_panel_1.items = app_tables.tools_py_str.search()


     