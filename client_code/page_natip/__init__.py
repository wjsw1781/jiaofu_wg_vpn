from ._anvil_designer import page_natipTemplate
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
        used_ports =[]
        for r in app_tables.nat_table.search():
            used_ip_froms.append(r['ip_use_from'])
            used_ip_froms.append(r['ip_use_to'])
            used_ports.append(r['wg_listen_port'])

        available_port = 50000
        available_from = None
        available_to = None

        # Iterate through possible second octet values (0 to 254)
        for x in range(255): # Covers 10.0.0.0/24 to 10.254.0.0/24
            potential_ip_from = f"10.{x}.0.0"
            potential_ip_to = f"10.{x+1}.0.0"

            # Check if this IP range is not already in use
            if potential_ip_from not in used_ip_froms and potential_ip_to not in used_ip_froms:
                available_from = potential_ip_from
                available_to = potential_ip_to
                break # Found an available range, exit loop
                
        while available_port in used_ports:
            available_port += 1  

        # 构造手机 ip  的路由规则 先产生 500 左右 ip 手机 等到 wgclient 实际运行后 开始前端绑定或者接口修改这个表就行
        available_from_start = ip_to_int(available_from)
        phone_num = 20
        for i in range(phone_num):
            available_from_start+=1
            one_ip = int_to_ip(available_from_start)
            # app_tables.wg_ip_rule.add_row(ip_from_phone=one_ip,for_key_ip_use_to_wg_16=available_to,)
            row = app_tables.wg_ip_rule.search(ip_from_phone=one_ip)      # 查是否已存在
            if len(row):
                row = app_tables.wg_ip_rule.get(ip_from_phone=one_ip)   
                row['for_key_ip_use_to_wg_16'] = available_to          # 已有 → 更新
                row['info'] = info          # 已有 → 更新

            else:
                app_tables.wg_ip_rule.add_row(                         # 没有 → 新增
                    ip_from_phone=one_ip,
                    for_key_ip_use_to_wg_16=available_to,
                    info = info
                )
        
        app_tables.nat_table.add_row(info=info, ip_use_from=available_from, ip_use_to=available_to,wg_listen_port=available_port)
        alert(f'默认服务 {phone_num}个手机   网段位于  {available_from}    wg 服务网段位于 {available_to}')
        self.repeating_panel_1.items = app_tables.nat_table.search() 
