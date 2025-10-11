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
        # 根据历史数据 找出可用的端口号 可用的网段  
        info = self.info.text
        rt_table_id_from = self.rt_table_id_from.text
        minipc_wifi_iplink_name = self.minipc_wifi_iplink_name.text or ""
        per_in_of_out = self.per_in_of_out.text or "1"
        if not(per_in_of_out and minipc_wifi_iplink_name and rt_table_id_from  ):
            alert('路由表起始编号   入口节点网卡名  负载比  均需要填写')
            return

        
        
        used_ip_froms = []
        used_ports =[49999]
        
        for r in app_tables.nat_table.search():
            used_ip_froms.append(r['ip_use_from'])
            used_ip_froms.append(r['ip_use_to'])
            used_ports.append(r['wg_listen_port'])
            
        used_ip_froms_num = list(map(lambda ip : ip_to_int(ip), used_ip_froms))
        
        available_port = 50000
        available_from = None
        available_to = None

        # Iterate through possible second octet values (0 to 254)
        for x in range(255): # Covers 10.0.0.0/24 to 10.254.0.0/24
            potential_ip_from = f"10.{x}.0.0"
            potential_ip_to = f"10.{x+1}.0.0"
            
            if max(used_ip_froms_num)>ip_to_int(potential_ip_to):
                continue
                
            # Check if this IP range is not already in use
            if potential_ip_from not in used_ip_froms and potential_ip_to not in used_ip_froms:
                available_from = potential_ip_from
                available_to = potential_ip_to
                break # Found an available range, exit loop
                
        while available_port <= max(used_ports):
            available_port += 1  

            
        # 增加这个业务的元信息
        app_tables.nat_table.add_row(info=info, 
                                     ip_use_from=available_from,
                                     ip_use_to=available_to,
                                     wg_listen_port=available_port,
                                     minipc_wifi_iplink_name= minipc_wifi_iplink_name,
                                     rt_table_id_from = rt_table_id_from,
                                     per_in_of_out = per_in_of_out
                                    )


        # 构造手机------> 路由规则表 只要一个就行了 路由规则会通过路由规则自己控制 1 拖5 
        row = app_tables.wg_ip_rule.search(ip_from_phone=available_from)      # 查是否已存在
        if len(row):
            row = app_tables.wg_ip_rule.get(ip_from_phone=available_from)   
            row['for_key_ip_use_to_wg_16'] = available_to          # 已有 → 更新
            row['info'] = info          # 已有 → 更新
        else:
            app_tables.wg_ip_rule.add_row(                         # 没有 → 新增
                ip_from_phone=available_from,
                for_key_ip_use_to_wg_16=available_to,
                info = info
            )

        alert(f'网段划分完成  手机网段  {available_from}    wg 服务网段位于 {available_to}')
        self.repeating_panel_1.items = app_tables.nat_table.search() 
