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
        self.repeating_panel_2.items = app_tables.binary_file_up_down.search()

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

    def file_loader_1_change(self, file, **event_args):
        """This method is called when a new file is loaded into this FileLoader"""
        if file:
            try:
                # 调用服务器函数上传文件
                anvil.server.call('upload_binary_file', file)
                self.repeating_panel_2.items = app_tables.binary_file_up_down.search()

                Notification(f"文件 '{file.name}' 上传成功！").show()
                
            except Exception as e:
                Notification(f"文件上传失败: {e}", title="错误", style="danger").show()
        else:
            Notification("未选择文件进行上传。", style="warning").show()


     