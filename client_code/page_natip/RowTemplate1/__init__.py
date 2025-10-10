from ._anvil_designer import RowTemplate1Template
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js import window 


import time

def list_of_dicts_to_csv_string_readable(data: list[dict]) -> str:
    """
    将 list[dict] 数据转换为 CSV 字符串，自动推断列名，并处理 CSV 编码。
    适用于 Anvil 纯客户端环境。
    """
    if not data:
        return "" # 处理空数据列表的情况

    # 1. 动态获取列名 (从第一个字典的键)
    column_names = list(data[0].keys())

    # 2. 生成 CSV 头部行
    header_parts = []
    for col_name in column_names:
        # 字段值中的双引号替换为两个双引号
        escaped_col_name = col_name.replace('"', '""')
        # 用双引号包裹整个字段
        header_parts.append(f'"{escaped_col_name}"')
    header_row = ",".join(header_parts)

    # 3. 生成所有数据行
    csv_data_rows = []
    for row_dict in data:
        row_parts = []
        for col_name in column_names:
            value = row_dict.get(col_name) # 安全获取值

            # 处理 None 值，转换为字符串
            if value is None:
                value_str = ""
            else:
                value_str = str(value)

            # 处理值中的双引号 (替换为两个双引号)
            escaped_value_str = value_str.replace('"', '""')

            # 如果值包含逗号、双引号或换行符，则用双引号包裹整个字段
            # 注意：此处我们假定值中不包含换行符，且已将所有双引号转义
            # 如果值中可能包含逗号，则始终包裹是更安全的做法。
            # 为了简化，我们只处理了双引号转义，并假定所有字段都用双引号包裹，
            # 这样对于大多数情况都有效，且简单。
            field = f'"{escaped_value_str}"'
            row_parts.append(field)

        csv_data_rows.append(",".join(row_parts))

    # 4. 组合头部和数据行
    return header_row + "\n" + "\n".join(csv_data_rows)

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

class RowTemplate1(RowTemplate1Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.server_ip_index = 0 
        self.server_ips =[]

    def ssh_run_click(self, **event_args):
        """This method is called when the button is clicked"""
        ip_to = self.item['ip_use_to']
        conf_rows = list(app_tables.wg_conf.search(ip_to=ip_to))

        result = []

        
        def run_one(row):       # 要执行的命令
            row_id = row.get_id()
            send_to_server_dict = dict(row)
            send_to_server_dict['row_id']=row_id

            fut = anvil.server.call('ssh_exec',send_to_server_dict)
            result.append(fut)
            if len(result) !=len(conf_rows):
                return
            succ     = sum(r['ok'] for r in result)                            # 成功条数
            for r in result:
                ssh_port = r['ssh_port']
                row_id = r['row_id']
                row = app_tables.wg_conf.get_by_id(row_id)
                if r['ok']:
                    row['wg_server_ok'] =  ""
                else:
                    row['wg_server_ok'] =   r['error']
                    
            fail_ips = [r['wg_server_public_ip']+"     "+r['error'] for r in result if not r['ok']]# 失败 IP 列表            
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
        if self.server_ips ==[]:
            alert("请上传该业务的节点文件 才能进行后续配置")
            return
        

        ip_from = self.item['ip_use_from']
        ip_to   = self.item['ip_use_to']
        wg_listen_port =self.item['wg_listen_port']
        rt_table_id_from =self.item['rt_table_id_from']
        minipc_wifi_iplink_name = self.item['minipc_wifi_iplink_name']
        
        RT_table_ID = int(rt_table_id_from)

        total_conf =  app_tables.wg_conf.search(ip_to = ip_to)
        total_len_conf = len(total_conf)
        for INDEX , row in enumerate(total_conf):
            row.delete()
            Notification(f'删除旧配置。。。。。。。{INDEX}/{total_len_conf}').show()

        
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
                server_public_ip = self.server_ips[self.server_ip_index][0]
                wg_server_public_ip = server_public_ip
                ssh_port = self.server_ips[self.server_ip_index][1]
                ssh_pwd = self.server_ips[self.server_ip_index][2]
                ssh_host = self.server_ips[self.server_ip_index][0]
                self.server_ip_index += 1   
            except :
                break
            all_conf.append([client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID,ssh_host,ssh_port,ssh_pwd,wg_server_public_ip])
    
            # 下一 /30
            current += 4
            count   += 1
    
        def thread_run_one_conf(one_conf):
            
            client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID,ssh_host,ssh_port,ssh_pwd,wg_server_public_ip = one_conf
    
            client_conf,server_conf= anvil.server.call('get_wg_server_client_conf',client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID,wg_server_public_ip)
    
            app_tables.wg_conf.add_row(
                wg_server_ip        = server_ip,
                wg_client_ip        = client_ip,
                wg_server_conf      = server_conf,
                wg_client_conf      = client_conf,
                wg_server_public_ip = server_public_ip,
                ip_to = ip_to,
                minipc_wifi_iplink_name =minipc_wifi_iplink_name,
                wg_listen_port = str(wg_listen_port),

                ssh_host = str(ssh_host),
                ssh_port =  str(ssh_port),
                ssh_pwd=  str(ssh_pwd),
            )
    
            all_conf_after_threads.append(server_conf)
    
            if len(all_conf_after_threads)!=len(all_conf):
                return

            # 最后触发下载
            datas_conf =   list(app_tables.wg_conf.search(ip_to=ip_to))
            datas_conf = list(map(lambda x : dict(x) ,datas_conf ))
            txt = list_of_dicts_to_csv_string_readable(datas_conf)

            csv_bytes = ("\ufeff" + txt).encode("utf-8")   # 前置 UTF-8 BOM

            alert(f"已成功生成 {len(datas_conf)} 条记录。", title="完成")

            anvil.media.download(
                anvil.BlobMedia("text/csv; charset=utf-8", csv_bytes, "wg_conf.csv")
            )

    
    
        delay = 5
        for index , r in enumerate(all_conf):
            window.setTimeout(lambda row=r: thread_run_one_conf(row), delay)
            delay +=5 
            Notification(f'业务创建导致的服务端客户端配置创建并写表----进度---- {index}   / {len(all_conf)}').show()
            time.sleep(1)
            

            
    def file_loader_1_change(self, file, **event_args):
        import re
        # 读取 CSV 内容（假设是 UTF-8；否则先 file.content_type 判断再选编码）
        text = file.get_bytes().decode('utf-8', errors='ignore')

        # ② 调我们自己写的 parse_csv
        rows = parse_csv(text)
        # 取每行第一列作为 server_ip，过滤掉表头（若有）

        def pick(col_name, extra=()):
            dd = DropDown(items=list(extra)+headers, include_placeholder=True,placeholder=f"请选择 {col_name} 列")
            alert(dd, title=f"{col_name} 列？", buttons=[("确定", True)])
            return None if dd.selected_value in extra else headers.index(dd.selected_value)
        
        headers, data = rows[0], rows[1:]                  # rows 是你 parse_csv 得到的
        ip_i  = pick("公网 IP")
        pt_i  = pick("端口", extra=("默认22",))
        pw_i  = pick("密码", extra=("默认Spider666Linux",))
        
        ips, ports, pwds = [], [], []
        for r in data:
            if ip_i and  len(r)<ip_i :
                continue
            # ip 
            if ':' in r[ip_i]:
                ip, port = r[ip_i].split(':')[0],r[ip_i].split(':')[1]
            else:
                ip = r[ip_i]
                
            # port
            if pt_i is not None:
                if ':' in r[pt_i]:
                    port =r[pt_i].split(':')[1]
                else:
                    port =r[pt_i]

            else:
                port = '22'
                
            # 密码
            if pw_i is not None:
                pwd = r[pw_i]
            else:
                pwd = 'Spider666Linux'
                
            ips.append(ip)
            ports.append(port)
            pwds.append(pwd)
            
        if not ips:
            alert("CSV 文件中未找到合法的公网 IP！")
            return
            
        triples = list(zip(ips, ports, pwds)) 
        alert(f"获取到的公网 ip---->   {triples}")
        
        self.server_ips = list(set(self.server_ips + triples ))     # 保存到 form 的实例变量
        self.server_ip_index = 0    # 当前已分配到第几个
        
        alert(f"当前文件载入 {len(ips)} 个服务器公网 IP。 累积倒入  {len( self.server_ips)}", title="上传成功")

    def client_down_click(self, **event_args):
        ip_to  = self.item['ip_use_to']
        minipc_wifi_iplink_name = self.item['minipc_wifi_iplink_name']
        per_in_of_out = self.item['per_in_of_out']
        
        wg_client_ips_all_client    = [r['wg_client_ip'] for r in app_tables.wg_conf.search(ip_to=ip_to)]
        wg_client_ips    = [r['wg_client_ip'] for r in app_tables.wg_conf.search(ip_to=ip_to,wg_server_ok="")]
        alert(f'所有 client wg server 部署成功数量 {len(wg_client_ips)}   总数量{len(wg_client_ips_all_client)}  不成功的不再进行 client 的生成')
        # 扩充手机路由规则    获取所有 client ip 进行扩充 一对 5 占用补充 phone 手机 ip 准备 ip范围   
        
        now_phone = [r for r in app_tables.wg_ip_rule.search(for_key_ip_use_to_wg_16=ip_to)]
        phone_per_cli  = int(per_in_of_out)                          # 1 : 5
        cursor         = ip_to_int(now_phone[0]['ip_from_phone'])
        cursor += 1

        gateway_ip  = int_to_ip(cursor)
        
        info_template = now_phone[0]['info']
        for index,cli_ip in enumerate(wg_client_ips):          # 遍历 WG-client IP
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
            Notification(f"进度------> 构造客户端wg_ip 负载 ip rule  {index}/{len(wg_client_ips)}").show()
        dhcp_start = int_to_ip(ip_to_int(gateway_ip)+1)
        dhcp_end   = mobile_ip
        
        

        # dns 操作 
        DNSMASQ_CONF = "/etc/dnsmasq.conf"
        wifi_网卡 = minipc_wifi_iplink_name or  'enp3s0' 
        系统自带dns_file = "/etc/resolv.conf"

        系统自带dns_conf = """
            nameserver 127.0.0.1
        """
    

        ali_dns = '223.5.5.5' 
        google_dns = '8.8.8.8'
        cf_dns = '1.1.1.1'
        china_dns = '114.114.114.114'
        ad = '94.140.14.14'
        use_dns = cf_dns
        lease_time = "12h"
        netmask = "255.255.0.0"            
        
        dnsmasq_conf = f"""
            # ===============  自动生成，请勿手工修改  =====================
            bind-interfaces
            log-queries
            log-facility=/var/log/dnsmasq.log
            port=53
            server={use_dns}
            # listen-address=127.0.0.1
            
            
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
                
                
                #拉起wifi网卡
                ip addr flush dev {wifi_网卡}
                sudo ip addr add {gateway_ip}/{netmask} dev {wifi_网卡}
                ip link set {wifi_网卡} down
                ip link set {wifi_网卡} up

                # 使用系统自带的 dns
                sudo systemctl enable systemd-resolved --now
                sudo rm /etc/NetworkManager/conf.d/no-resolv.conf
                sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf  


                # 开启 dnsmasq dhcp 的 ip 分配能力
                # apt install dnsmasq
                echo "{dnsmasq_conf}" > {DNSMASQ_CONF}
                systemctl restart dnsmasq

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

        # wg 客户端 sh conf 生成 只要 wg_server_ok=""   拼接命令的同时 吧 sh 也进行保存到/etc/wiregard/*.sh
        wg_client_lunchs = []
        for wg_conf_server_client in app_tables.wg_conf.search(ip_to=ip_to,wg_server_ok=""):
            lunch_name =  wg_conf_server_client['wg_client_ip'].replace('.','_')
            sh_file = f'/etc/wireguard/{lunch_name}.sh'
            one_wg_client_conf = wg_conf_server_client['wg_client_conf']
            wg_server_public_ip = wg_conf_server_client['wg_server_public_ip'].strip()
            if wg_server_public_ip.count('.')!=3:
                Notification(f'adsl 正确的ip 还没上报上来 不进行 配置的生成 --------  {wg_server_public_ip}').show()
                continue
            import re
            one_wg_client_conf = re.sub(
                r"(Endpoint\s*=\s*)[^:]+",                 # 匹配 Endpoint 后到冒号前
                rf"\g<1>{wg_server_public_ip}",            # 用 \g<1> 引用分组 1
                one_wg_client_conf,
                count=1
            )
                        

            save_to_sh_and_shell_raw = f"""

            
cat << 'EOF' > {sh_file}
{one_wg_client_conf}
EOF

bash {sh_file}


            """
            wg_client_lunchs.append(save_to_sh_and_shell_raw)
            
        # 拉起 wg 客户端
        wg_client_lunchs    = "\n\n".join(wg_client_lunchs)

        # 路由表配置命令
        all_rule = "\n\n".join(all_rule)

        # 所有命令
        txt  = first_cmd + wg_client_lunchs + all_rule
        
        anvil.media.download(anvil.BlobMedia("text/plain", txt.encode(), "wg_clients.sh"))

    def delete_click(self, **event_args):
        """This method is called when the button is clicked"""
        ip_use_to = self.item['ip_use_to']

        self.item.delete()
        self.parent.parent.parent.parent.parent.repeating_panel_1.items = app_tables.nat_table.search()

        need_delete = app_tables.wg_conf.search(ip_to=ip_use_to)
        need_delete_num = len(need_delete)
        
        for index, line in enumerate(need_delete):
            Notification(f'业务删除引发配置删除----进度----{index}/{need_delete_num}').show()
            line.delete()

    def open_this_wg_conf_status_click(self, **event_args):
        """This method is called when the button is clicked"""
        
        from ...page_ssh import page_ssh

        ip_use_to= self.item['ip_use_to']
        from_params = app_tables.wg_conf.search(ip_to=ip_use_to)
        page = open_form('page_ssh',from_params=from_params)
        # alert(page)
        

