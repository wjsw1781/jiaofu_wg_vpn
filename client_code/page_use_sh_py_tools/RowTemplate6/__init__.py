from ._anvil_designer import RowTemplate6Template
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class RowTemplate6(RowTemplate6Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def down_binary_file_click(self, **event_args):
        """This method is called when the Download button is clicked"""
        server_path = self.item['server_path']
        media_object = anvil.server.call('get_binary_file',server_path)
        Notification(f"开始下载文件: {media_object.name}").show()

        anvil.media.download(media_object)
        