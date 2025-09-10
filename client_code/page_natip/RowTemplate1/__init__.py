from ._anvil_designer import RowTemplate1Template
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js import window 
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

def parse_csv(text):
  rows = []
  line = []
  field = []
  in_quote = False
  i = 0
  while i < len(text):
    ch = text[i]
    if ch == '"' :
      if in_quote and i + 1 < len(text) and text[i+1] == '"':
        # 遇到两个连续 "" ，在字段里加一个 "
        field.append('"')
        i += 1
      else:
        # 进入或退出引号
        in_quote = not in_quote
    elif ch == ',' and not in_quote:
      # 字段结束
      line.append(''.join(field))
      field = []
    elif ch in '\r\n' and not in_quote:
      # 行结束（\r\n、\n 或 \r）
      if ch == '\r' and i + 1 < len(text) and text[i+1] == '\n':
        i += 1      # 跳过 \n
      line.append(''.join(field))
      rows.append(line)
      line = []
      field = []
    else:
      field.append(ch)
    i += 1
  # 文件最后一行
  line.append(''.join(field))
  rows.append(line)
  return rows


def is_public_ip(s):
    parts = s.split('.')
    if len(parts) != 4:                     # 不是 IPv4 4 段
        return False
    try:
        nums = [int(p) for p in parts]
    except:
        return False                          # 有非数字
    if any(n < 0 or n > 255 for n in nums): # 范围非法
        return False

    # 过滤常见私网段
    if nums[0] == 10:
        return False
    if nums[0] == 172 and 16 <= nums[1] <= 31:
        return False
    if nums[0] == 192 and nums[1] == 168:
        return False

    return True
    
class RowTemplate1(RowTemplate1Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def ssh_run_click(self, **event_args):
        """This method is called when the button is clicked"""
        ip_to = self.item['ip_use_to']
        conf_rows = list(app_tables.wg_conf.search(ip_to=ip_to))

        result = []

        
        def run_one(row):       # 要执行的命令
            fut = anvil.server.call('ssh_exec', dict(row))
            result.append(fut)
            if len(result) !=len(conf_rows):
                return
            succ     = sum(r['ok'] for r in result)                            # 成功条数
            for r in result:     
                if r['ok']:
                    app_tables.wg_conf.get(wg_server_public_ip=r['wg_server_public_ip'])['wg_server_ok'] =  "成功"
                else:
                    app_tables.wg_conf.get(wg_server_public_ip=r['wg_server_public_ip'])['wg_server_ok'] =   r['stderr']
            fail_ips = [r['wg_server_public_ip'] for r in result if not r['ok']]# 失败 IP 列表            
            info = "\n".join(fail_ips)
            alert(f'全部完成：成功 {succ}，失败 {len(fail_ips)}，失败 IP: {info}', result)

        
        delay = 5
        for r in conf_rows:
            window.setTimeout(lambda row=r: run_one(row), delay)
            delay +=1
            # run_one(dict(r))
            

    def make_conf_click(self, **event_args):
        """This method is called when the button is clicked"""
    
        # 2. 拿到起止 IP
        
        ip_from = self.item['ip_use_from']
        ip_to   = self.item['ip_use_to']
        wg_listen_port =self.item['wg_listen_port']
        max_pairs  = 2000

        start = ip_to_int(ip_to)
        end   = start+max_pairs
        print(f'{ip_to} ----{int_to_ip(end)}')
        count      = 0
        current    = start
        
        while current + 3 <= end and count < max_pairs:
            client_ip_int = current + 1       # /30 中的第一个可用地址
            server_ip_int = current + 2       # /30 中的第二个可用地址
        
            client_ip = int_to_ip(client_ip_int)
            server_ip = int_to_ip(server_ip_int)

            try:
                server_public_ip = self.server_ips[self.server_ip_index]
                self.server_ip_index += 1   
            except :
                break
            RT_table_ID = count+200
            # —— 生成极简 WG 配置 ——（示范，用自己的逻辑替换）————
            client_conf,server_conf= anvil.server.call('get_wg_server_client_conf',client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID)

            
            # —— 写入 wg_conf 表 ————————————————————————————————
            row = app_tables.wg_conf.search(wg_server_ip=server_ip)
            
            if len(row):  
                row =app_tables.wg_conf.get(wg_server_ip=server_ip)
                row['wg_client_ip']        = client_ip
                row['wg_server_conf']      = server_conf
                row['wg_client_conf']      = client_conf
                row['wg_server_public_ip'] = server_public_ip
                row['ip_to'] = ip_to
                
            else:                                                 # 不存在 → 新增
                app_tables.wg_conf.add_row(
                    wg_server_ip        = server_ip,
                    wg_client_ip        = client_ip,
                    wg_server_conf      = server_conf,
                    wg_client_conf      = client_conf,
                    wg_server_public_ip = server_public_ip,
                    ip_to = ip_to,
                )
        
            # 下一 /30
            current += 4
            count   += 1
        
        alert(f"已成功生成 {count} 对地址。", title="完成")

    def file_loader_1_change(self, file, **event_args):

            # 读取 CSV 内容（假设是 UTF-8；否则先 file.content_type 判断再选编码）
        text = file.get_bytes().decode('utf-8', errors='ignore')

        # ② 调我们自己写的 parse_csv
        rows = parse_csv(text)
        # 取每行第一列作为 server_ip，过滤掉表头（若有）
        ips = []
        for i, line in enumerate(rows):
            cands = [c.strip('" ') for c in line if is_public_ip(c.strip('" '))]
            if cands:
                ips.append(cands[0])     
        
        if not ips:
            alert("CSV 文件中未找到合法的公网 IP！")
            return
        self.server_ips = ips       # 保存到 form 的实例变量
        self.server_ip_index = 0    # 当前已分配到第几个
        
        alert(f"已载入 {len(ips)} 个服务器公网 IP。", title="上传成功")

    def client_down_click(self, **event_args):
        ip_to  = self.item['ip_use_to']
        txt    = "\n\n".join(r['wg_client_conf'] for r in app_tables.wg_conf.search(ip_to=ip_to))
        anvil.media.download(anvil.BlobMedia("text/plain", txt.encode(), "wg_clients.sh"))


