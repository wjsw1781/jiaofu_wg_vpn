from ._anvil_designer import RowTemplate1Template
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

def ip_to_int(ip_str):
    """
  '10.0.0.1'  ->  167772161
  """
    parts = [int(p) for p in ip_str.split(".")]
    return (parts[0]<<24) + (parts[1]<<16) + (parts[2]<<8) + parts[3]


def int_to_ip(ip_int):
    """
  167772161  ->  '10.0.0.1'
  """
    return ".".join(str((ip_int >> shift) & 0xFF) for shift in (24,16,8,0))

    
class RowTemplate1(RowTemplate1Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def button_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.item.delete()
        get_open_form().repeating_panel_1.items = app_tables.nat_table.search()

    def button_2_click(self, **event_args):
        """This method is called when the button is clicked"""
    
        # 2. 拿到起止 IP
        
        ip_from = self.item['ip_use_from']
        ip_to   = self.item['ip_use_to']
        server_public_ip = ""
        
        start = ip_to_int(ip_from)
        end   = ip_to_int(ip_to)
        
        count      = 0
        max_pairs  = 100
        current    = start
        
        while current + 3 <= end and count < max_pairs:
            server_ip_int = current + 1       # /30 中的第一个可用地址
            client_ip_int = current + 2       # /30 中的第二个可用地址
        
            server_ip = int_to_ip(server_ip_int)
            client_ip = int_to_ip(client_ip_int)
        
            # —— 生成极简 WG 配置 ——（示范，用自己的逻辑替换）————
            server_conf = f"[Interface]\nAddress = {server_ip}/30\n"
            client_conf = f"[Interface]\nAddress = {client_ip}/30\n"
        
            # —— 写入 wg_conf 表 ————————————————————————————————
            app_tables.wg_conf.add_row(
                server_ip        = server_ip,
                client_ip        = client_ip,
                server_conf      = server_conf,
                client_conf      = client_conf,
                server_public_ip = server_public_ip
            )
        
            # 下一 /30
            current += 4
            count   += 1
        
        alert(f"已成功生成 {count} 对地址。", title="完成")