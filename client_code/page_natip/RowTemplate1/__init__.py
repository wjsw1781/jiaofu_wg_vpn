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
                    app_tables.wg_conf.get(wg_server_public_ip=r['wg_server_public_ip'],ip_to=ip_to)['wg_server_ok'] =  "成功"
                else:
                    app_tables.wg_conf.get(wg_server_public_ip=r['wg_server_public_ip'],ip_to=ip_to)['wg_server_ok'] =   r['stderr']
            fail_ips = [r['wg_server_public_ip'] for r in result if not r['ok']]# 失败 IP 列表            
            info = "\n".join(fail_ips)
            alert(f'全部完成：成功 {succ}，失败 {len(fail_ips)}，失败 IP: {info}', result)

        
        delay = 5
        for r in conf_rows:
            delay +=1

            window.setTimeout(lambda row=r: run_one(row), delay)
            # run_one(dict(r))
            

    def make_conf_click(self, **event_args):
        """This method is called when the button is clicked"""
    
        # 2.路由表编号  不一样  这个是客户端 这边路由表 一样会导致 ip rule 最后路由到最后一个 200
        RT_table_ID = 200
    
        ip_from = self.item['ip_use_from']
        ip_to   = self.item['ip_use_to']
        wg_listen_port =self.item['wg_listen_port']
        max_pairs  = 2000
    
        start = ip_to_int(ip_to)
        end   = start+max_pairs
        count      = 0
        current    = start
    
        all_conf = []
        all_conf_after_threads = []
    
    
        while current + 3 <= end and count < max_pairs:
            RT_table_ID +=1
            client_ip_int = current + 1       # /30 中的第一个可用地址
            server_ip_int = current + 2       # /30 中的第二个可用地址
    
            client_ip = int_to_ip(client_ip_int)
            server_ip = int_to_ip(server_ip_int)
            try:
                server_public_ip = self.server_ips[self.server_ip_index]
                self.server_ip_index += 1   
            except :
                break
            all_conf.append([client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID])
    
            # 下一 /30
            current += 4
            count   += 1
    
        def thread_run_one_conf(one_conf):
            client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID = one_conf
    
            client_conf,server_conf= anvil.server.call('get_wg_server_client_conf',client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID)
    
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
    
            all_conf_after_threads.append(server_conf)
    
            if len(all_conf_after_threads)!=len(all_conf):
                return

            alert(f"已成功生成 {len(all_conf_after_threads)} 对地址。", title="完成")
            # 最后触发下载
            txt = "\n\n".join(all_conf_after_threads)
            anvil.media.download(anvil.BlobMedia("text/plain", txt.encode(), "wg_servers.sh"))

    
    
        delay = 5
        for r in all_conf:
            window.setTimeout(lambda row=r: thread_run_one_conf(row), delay)
            delay +=1

            
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
        wg_client_ips    = [r['wg_client_ip'] for r in app_tables.wg_conf.search(ip_to=ip_to)]
        # 扩充手机路由规则    获取所有 client ip 进行扩充 一对 5 占用补充 phone 手机 ip 准备 ip范围   
        
        now_phone = [r for r in app_tables.wg_ip_rule.search(for_key_ip_use_to_wg_16=ip_to)]
        phone_per_cli  = 5                                            # 1 : 5
        cursor         = ip_to_int(now_phone[0]['ip_from_phone'])
        cursor += 1

        # 第一个地址给 wifi 网卡使用  enp88s0
        gateway_ip  = int_to_ip(cursor)
        
        info_template = now_phone[0]['info']
        for cli_ip in wg_client_ips:          # 遍历两个 WG-client IP
            for _ in range(phone_per_cli):    # 给每个 client 派 5 个手机 IP
                cursor += 1
                mobile_ip = int_to_ip(cursor)
        
                if len(app_tables.wg_ip_rule.search(ip_from_phone=mobile_ip,ip_to_wg_client=cli_ip)):
                    continue                                   # 已存在 → 跳过
        
                app_tables.wg_ip_rule.add_row(                # 不存在 → 新增
                    ip_from_phone            = mobile_ip,
                    ip_to_wg_client          = cli_ip,        
                    for_key_ip_use_to_wg_16  = ip_to,
                    info=info_template,
                )
        dhcp_start = int_to_ip(ip_to_int(gateway_ip)+1)
        dhcp_end   = mobile_ip
        
        

        # dns 操作 
        DNSMASQ_CONF = "/etc/dnsmasq.conf"
        wifi_网卡 = 'enp3s0'
        系统自带dns_file = "/etc/resolv.conf"

        系统自带dns_conf = """
            nameserver 127.0.0.1
                        
            # A. 全局禁止 NetworkManager 写 resolv.conf
            # /etc/NetworkManager/conf.d/no-resolv.conf （新建）
                                    
            # [main]
            # dns=none
                        
            
            # B. 重启 NetworkManager
            # systemctl restart NetworkManager
                        
            
        """
    

        ali_dns = '223.5.5.5' 
        google_dns = '8.8.8.8'
        china_dns = '114.114.114.114'
        ad = '94.140.14.14'
        use_dns = ali_dns
        lease_time = "12h"
        netmask = "255.255.0.0"            
        
        dnsmasq_conf = f"""
            # ===============  自动生成，请勿手工修改  =====================
            bind-interfaces
            
            port=53
            server={use_dns}
            listen-address=127.0.0.1
            
            
            # 第一个网卡管理 ===================== ===================== ===================== ===================== =====================
            listen-address={gateway_ip}
            interface={wifi_网卡}
            dhcp-range={dhcp_start},{dhcp_end},{netmask},{lease_time}
            dhcp-option=3,{gateway_ip}                          # 默认网关
            dhcp-option=6,{use_dns}                             # DNS服务器
    
        """

        first_cmd = f"""

                # 必须优先运行的代码  关闭掉一些应用  影响路由表   调整 mss 头部大小  

                iptables -t mangle -D FORWARD -o w+ -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
                iptables -t mangle -A FORWARD -o w+ -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

                iptables -t mangle -D FORWARD -o 10_+ -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
                iptables -t mangle -D FORWARD -i 10_+ -p tcp --tcp-flags SYN,RST SYN  -j TCPMSS --clamp-mss-to-pmtu
                iptables -t mangle -A FORWARD -o 10_+ -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
                iptables -t mangle -A FORWARD -i 10_+ -p tcp --tcp-flags SYN,RST SYN  -j TCPMSS --clamp-mss-to-pmtu
                
                # 安装 dnsmasq 创建配置必须要链接网络   
                # 恢复 DNS 能力
                # sudo systemctl enable --now systemd-resolved       # 重新开服务
                # sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf   # 恢复符号链接
                # sudo apt update && sudo apt install -y dnsmasq
                
                echo "{dnsmasq_conf}" > {DNSMASQ_CONF}

                
                #拉起wifi网卡
                ip addr flush dev {wifi_网卡}
                sudo ip addr add {gateway_ip}/{netmask} dev {wifi_网卡}
                ip link set {wifi_网卡} down
                ip link set {wifi_网卡} up

                
                # 禁用系统自带 使用 dnsmasq 进行路由 移除配置  关键点 上面必须都运行完成才能工作
                systemctl stop systemd-resolved
                systemctl disable systemd-resolved
                sudo systemctl stop dnsmasq
                echo "{系统自带dns_conf}" > {系统自带dns_file}
                systemctl restart dnsmasq
                # systemctl status dnsmasq


                # 开始拉起所有的 wg 客户端##################################
                # 开始拉起所有的 wg 客户端##################################
                # 开始拉起所有的 wg 客户端##################################
                # 开始拉起所有的 wg 客户端##################################

                
        """

        
        all_ip_rule = list(app_tables.wg_ip_rule.search(for_key_ip_use_to_wg_16=ip_to,ip_to_wg_client= q.not_(None)))
        all_rule = []
        for rule_row in all_ip_rule:
            ip_addr = rule_row['ip_from_phone']
            use_wg_if_client = rule_row['ip_to_wg_client'].replace('.','_')
            template = f"""
                        ip rule list   | grep {ip_addr} | awk '{{print $1}}' | tr -d ':' |xargs -r -I{{}} ip rule del pref {{}}
                        ip rule add from {ip_addr} lookup {use_wg_if_client}

            """
            all_rule.append(template)

        # wg 客户端
        wg_client_lunchs    = "\n\n".join(r['wg_client_conf'] for r in app_tables.wg_conf.search(ip_to=ip_to))

        # 路由表
        all_rule = "\n\n".join(all_rule)

        # 所有命令
        txt  = first_cmd + wg_client_lunchs + all_rule
        
        anvil.media.download(anvil.BlobMedia("text/plain", txt.encode(), "wg_clients.sh"))

    def delete_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.item.delete()
        self.parent.parent.parent.parent.parent.repeating_panel_1.items = app_tables.nat_table.search()


