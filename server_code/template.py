import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

import random,string,time



_ip_keys_memory = {}

def get_公私钥_memory_service(ip):
    """
    内存服务 dict 随机的服务
    返回的结构与原函数一致，但公私钥是随机生成的字符串，不涉及文件写入。
    """
    time.sleep(3)
    if ip in _ip_keys_memory:
        return _ip_keys_memory[ip]

    # 随机生成私钥 (模拟 wg genkey)
    # 这里我们生成一个长度为44的随机字符串，包含大小写字母和数字，以模拟Base64编码的格式
    priv = ''.join(random.choices(string.ascii_letters + string.digits + '+/=', k=44)) + '='

    # 随机生成公钥 (模拟 wg pubkey)
    # 这里我们生成一个长度为44的随机字符串，包含大小写字母和数字，以模拟Base64编码的格式
    pub = ''.join(random.choices(string.ascii_letters + string.digits + '+/=', k=44)) + '='

    _ip_keys_memory[ip] = {'public': pub, 'private': priv}

    return _ip_keys_memory[ip]

def get_公私钥(ip):
    import os ,json ,subprocess,pathlib
    file_name = '/root/socks_ss_gfw_ss_socks/linux_透明代理_多路组网_子网划分/all_ip_pubkey_prikey.json'
    try:
        if not os.path.isfile(file_name):
            with open(file_name, 'w') as fp:
                fp.write('{}')    
    
        with open(file_name, 'r') as fp:
            try:
                ip_keys = json.load(fp) or {}
            except json.JSONDecodeError:
                ip_keys = {}
    
        if ip in ip_keys:
            return ip_keys[ip]
    
        priv = subprocess.check_output(['wg', 'genkey']).strip().decode()
        pub  = subprocess.check_output(['wg', 'pubkey'], input=priv.encode()).strip().decode()
        ip_keys[ip] = {'public': pub, 'private': priv}
    
        with open(file_name, 'w') as fp:
            json.dump(ip_keys, fp, indent=4)

        return ip_keys[ip]
    except Exception as e :
        return get_公私钥_memory_service(ip)


def parse_stub_output(text: str):
    import re
    res ={}
    for m in re.finditer(r'(^|\n)(?P<key>[^\n:]+?)开始.*?\n', text):
        key = m.group('key').strip()
        start_pos = m.end()             # 内容起点
        # 搜 key结束
        end_pat = re.compile(rf'(^|\n){re.escape(key)}结束', re.M)
        end_m = end_pat.search(text, start_pos)
        if end_m:
            value = text[start_pos:end_m.start()].strip()
            res[key] = value
    return res

def make_shell_stub(kv) -> str:
    out = []
    for key, cmd in kv.items():
        out.append(f'echo "{key}开始"')
        out.append(cmd)
        out.append(f'echo "{key}结束"')
    return "\n".join(out)



def extract_public_ip(text: str):
    import ipaddress, re
    # IPv4 正则（0-255）
    _IP_RE = re.compile(
        r'\b(?:25[0-5]|2[0-4]\d|1?\d?\d)'
        r'(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b'
    )
    """
    1. 先定位 “公网IP开始:” 与 “公网IP结束” 之间的文本；
       若未找到这两个标签，则直接在全文搜索。
    2. 把其中出现的 IPv4 按顺序遍历，返回第一个非私网地址。
       私网段：10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    """
    # 取出标签包围的子串（可跨行）
    m = re.search(r'公网IP开始:(.*?)公网IP结束', text, re.S)
    segment = m.group(1) if m else text

    for ip in _IP_RE.findall(segment):
        ip_obj = ipaddress.ip_address(ip)
        if not ip_obj.is_private:      # 过滤私有地址
            return ip
    return ""

py_baohuo_file = './upload_binary_file/o0_0节点保活_巡检指定wg.py'

py_save_to_server_file = '/etc/wireguard/o0_0节点保活_巡检指定wg.py'

try:
    with open(py_baohuo_file,'r') as ff:
        py_baohuo_file_content = ff.read()
except :
    py_baohuo_file_content = "print('本地没有读取到这个文件')"




# 产生配置  服务端配置 客户端配置都产生
@anvil.server.callable
def get_wg_server_client_conf(client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID,wg_server_public_ip):
    prefixlen = 30
    MTU = 1330

    wg_table_client = f"{client_ip.replace('.', '_')}"
    wg_table_server = f"{server_ip.replace('.', '_')}"

    wg_if_client =wg_table_client
    wg_if_server =wg_table_server


    wg_ip_client =client_ip
    wg_ip_server =server_ip


    ListenPort = wg_listen_port
    wg_main_server_ip = server_public_ip

    from_ip = ip_from


    wg_conf_file_client = f"/etc/wireguard/{wg_table_client}.conf"
    wg_conf_file_server = f"/etc/wireguard/{wg_table_server}.conf"



    print('当前处理的wg队列配置文件',wg_conf_file_client, wg_conf_file_server , )

    server_pub_pri=get_公私钥(wg_ip_server)
    client_pub_pri=get_公私钥(wg_ip_client)

    srv_priv = server_pub_pri['private']
    srv_pub = server_pub_pri['public']

    client_priv = client_pub_pri['private']
    cli_pub = client_pub_pri['public']



    server_conf = f"""
        [Interface]
        Address = {wg_ip_server}/{prefixlen}
        ListenPort = {ListenPort}
        PrivateKey = {srv_priv}
        Table = {wg_table_server}
        MTU = {MTU}


        [Peer]
        PublicKey = {cli_pub}
        AllowedIPs = 0.0.0.0/0, ::/0
        PersistentKeepalive = 25
    """


    # 生成配置文件
    client_conf = f"""
        [Interface]
        Address ={wg_ip_client}/{prefixlen}
        PrivateKey = {client_priv}
        Table = {wg_table_client}
        MTU = {MTU}

        [Peer]
        PublicKey = {srv_pub}
        Endpoint  = {wg_server_public_ip}:{ListenPort}
        AllowedIPs = 0.0.0.0/0, ::/0
        PersistentKeepalive = 25

    """

    # 服务端直接运行起来   还有一个保活的 py 逻辑 从本地读取即可
    公网IP_shell=make_shell_stub({"公网IP_shell":'    ip -j -4 addr show dev ppp0     '})
    所有wg_节点peer_现状_shell=make_shell_stub({"所有wg_节点peer_现状_shell":"""  wg show all dump | grep none  | awk -v now=$(date +%s) '{print $0,now-$6}' | sort -k10n | column -t    """})
    
    cmd_lunch_wg_server = f"""
        # 如果已经安装 wg 则不再安装
        if ! which wg-quick; then
          apt-get update &&   sudo apt-get install -y --no-install-recommends  wireguard-dkms wireguard-tools
        fi

        PORT_IN_USE=$(wg show all dump | awk '{{print $4}}' | grep -w "{ListenPort}")

        if [ -n "$PORT_IN_USE" ]; then
            echo "WARN: WireGuard ListenPort {ListenPort} 已被其他 WG 接口占用。正在关闭 指定WG 接口而不是所有接口以避免冲突..."
            # 关闭所有 wg 进程 防止端口冲突 起不来wg 进程 清理路由表 路由规则 保持干净环境
            # 这里使用 wg show interfaces 获取所有接口名，然后逐个执行 wg-quick down  应该是找到指定的旧接口名
            wg show all dump | grep -v none | grep "{ListenPort}" | awk '{{print $1}}' | xargs -n1 wg-quick down
            
            echo "所有 WireGuard 接口已关闭。"
            # wg show interfaces | xargs -n 1 |xargs -n1 wg-quick down
            # sed -i '/10.*$/d' /etc/iproute2/rt_tables
            # sed -i '/^$/d' /etc/iproute2/rt_tables
            # ip rule list | grep -v -E "lookup (local|main|default)" | awk '{{print $1}}' | tr -d ':' | xargs -I {{}} ip rule del pref {{}}

        else
            echo "WireGuard ListenPort {ListenPort} 未被占用，可以正常启动。"
        fi


        echo "{server_conf}" > {wg_conf_file_server}

        if ! cat /etc/iproute2/rt_tables | grep "{wg_table_server}"; then
            echo "{RT_table_ID}    {wg_table_server}" >> /etc/iproute2/rt_tables
        fi

        sysctl -w net.ipv4.ip_forward=1 2>/dev/null
        wg_MAIN_INTERFACE_server=$(ip route | awk '/^default/ {{for(i=1;i<=NF;i++) if ($i=="dev") {{print $(i+1); exit}}}}')
        iptables -t nat -D POSTROUTING -o $wg_MAIN_INTERFACE_server -j MASQUERADE
        iptables -t nat -A POSTROUTING -o $wg_MAIN_INTERFACE_server -j MASQUERADE
        echo "主网卡-------> $wg_MAIN_INTERFACE_server"
        
        ip -4 route flush table {wg_table_server}
        ip -6 route flush table {wg_table_server}
        
        wg-quick down {wg_if_server}
        wg-quick up {wg_if_server}

        ip rule list   | grep {wg_ip_client} | awk '{{print $1}}' | tr -d ':' |xargs -r -I{{}} ip rule del pref {{}}
        # ip rule add to {wg_ip_client} lookup {wg_table_server}

        ip rule list   | grep {from_ip}/16 | awk '{{print $1}}' | tr -d ':' |xargs -r -I{{}} ip rule del pref {{}}
        ip rule add to {from_ip}/16 lookup {wg_table_server}



# 保活 py 逻辑 上报逻辑更新adsl最新公网 ip 的逻辑
cat << 'EOF' > {py_save_to_server_file}
{py_baohuo_file_content}
EOF

pkill -f python3 
nohup python3 {py_save_to_server_file} > /dev/null 2>&1 &

# 埋点分析统计
{公网IP_shell}
{所有wg_节点peer_现状_shell}



"""



    # 客户端生成下发脚本 一键运行
    client_script = f"""
        if ! which wg-quick; then
          apt-get update &&   sudo apt-get install -y --no-install-recommends  wireguard-dkms wireguard-tools
        fi
        echo "{client_conf}" > {wg_conf_file_client}

        if ! cat /etc/iproute2/rt_tables | grep "{wg_table_client}"; then
            echo "{RT_table_ID}    {wg_table_client}" >> /etc/iproute2/rt_tables
        fi
        sysctl -w net.ipv4.ip_forward=1 2>/dev/null

        wg-quick down {wg_if_client}  2>/dev/null
        ip -4 route flush table {wg_table_client}
        ip -6 route flush table {wg_table_client}
        wg-quick up {wg_if_client} 2>/dev/null

        ip rule list   | grep {wg_ip_server} | awk '{{print $1}}' | tr -d ':' |xargs -r -I{{}} ip rule del pref {{}}
        # ip rule add to {wg_ip_server} lookup {wg_table_client}


        WAN_IF=$(ip -o -4 route show default   | awk '{{print $5;exit}}')
        WAN_GW=$(ip -o -4 route show default   | awk '{{print $3;exit}}')

        iptables -t nat -D POSTROUTING -o $WAN_IF -j MASQUERADE
        iptables -t nat -A POSTROUTING -o $WAN_IF -j MASQUERADE
        ip route add 106.15.79.170/32 via $WAN_GW dev $WAN_IF table {wg_table_client}
        ip route add 114.55.114.193/32 via $WAN_GW dev $WAN_IF table {wg_table_client}
        ip route add 114.55.91.58/32 via $WAN_GW dev $WAN_IF table {wg_table_client}
        ip route add 118.178.172.142/32 via $WAN_GW dev $WAN_IF table {wg_table_client}
        
        ip route add 47.97.83.157/32 via $WAN_GW dev $WAN_IF table {wg_table_client}


    """

    return client_script,cmd_lunch_wg_server

    # 纯 Python 的 SSH 客户端库


from loguru import logger
import sys

@anvil.server.callable
def ssh_exec(data_with_cmd):
    import paramiko    ,time,os


    row_id = data_with_cmd["row_id"]
    ssh_pwd = data_with_cmd["ssh_pwd"]
    ssh_host = data_with_cmd["ssh_host"]
    ssh_port = data_with_cmd["ssh_port"]
    wg_server_ip = data_with_cmd["wg_server_ip"]
    logger.success(f'开始执行 ssh_exec  {row_id}            ssh root@{ssh_host}  -p {ssh_port}    {ssh_pwd}  ')



    
    cmd = data_with_cmd["wg_server_conf"]


    host = ssh_host
    port = ssh_port
    user = "root"
    password = ssh_pwd
    timeout = 15


    ret = {"row_id":row_id,    "host": host,"ssh_port":ssh_port,"ok": False, "stdout": "", "stderr": "", "error": "","wg_server_public_ip":ssh_host}

    ssh = paramiko.SSHClient()

    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, port=port,username=user, password=password,timeout=timeout)

        wg_server_ip_sh = wg_server_ip.replace(".","_")
        


    
        local_wg_conf = f'./wg_conf/{wg_server_ip_sh}.sh'
        remote_wg_conf = f'/etc/wireguard/{wg_server_ip_sh}.sh'
        os.makedirs(os.path.dirname(local_wg_conf), exist_ok=True)
        stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/wireguard/", timeout=timeout)

        with open(local_wg_conf,'w') as f:
            f.write(cmd)

        osftp = ssh.open_sftp()
        osftp.put(local_wg_conf, remote_wg_conf)
        osftp.close()

        cmd = f'bash {remote_wg_conf}'


        # 执行 并获取所有结果         output_buffer = ""
        output_buffer = ""

        remote_shell = ssh.invoke_shell(width=1080, height=1080)  
        remote_shell.send(cmd + '\n')


        now_time=int(time.time())

        while True:
            # 避免过度轮询
            time.sleep(0.1)

            end_time=int(time.time())
            if end_time-now_time>10:
                break
            # 读取实时输出
            if remote_shell.recv_ready():
                # new_data = shell.recv(1024).decode('utf-8')
                new_data = remote_shell.recv(1024).decode('utf-8', errors='ignore') 
                output_buffer += new_data

                sys.stdout.write("\r")  # 回到行首
                sys.stdout.write("\033[K")  # 清除当前行
                sys.stdout.write(output_buffer)
                sys.stdout.flush()
    
        parsed = parse_stub_output(output_buffer)
        for key in parsed:

            if key == "公网IP_shell":
                try:
                    wg_server_public_ip = extract_public_ip(parsed[key])
                    if wg_server_public_ip:
                        row = app_tables.wg_conf.get_by_id(row_id)
                        # 更新公网IP  外界 adsl 拨号机器的公网 ip 无法固定
                        row['wg_server_public_ip']=wg_server_public_ip
                    # logger.debug(f" {row_id}      {key} ---> {wg_server_public_ip}")
                except Exception as e:
                    pass

            if key == "所有wg_节点peer_现状_shell":
                ok = wg_server_ip_sh in parsed[key]
                logger.debug(f" {row_id}      {key} ---> {wg_server_ip_sh} in {ok}")

        
        ret["stderr"] = output_buffer
        ret["stdout"] = output_buffer
        ret["ok"]      = ok
        


    except Exception as e:
        ret["error"] = str(e)

    return ret



@anvil.server.callable
def make_91_to_anvil():
    import json,re
    file_name = '91_client_script_up.json'
    with open(file_name,'r') as f:
        data = json.load(f)
    for index, py_content in enumerate(data):

        pattern = r"Address =(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/\d{1,2}(?:\r?\n|$)"

        match = re.search(pattern, py_content)
        py_desc = match.group(1)
        have_in = app_tables.tools_py_str.search( info_desc=py_desc)
        if len(have_in) == 0:
            app_tables.tools_py_str.add_row(
                info_desc=py_desc,
                python_code=py_content
            )
        else:
            data_row = app_tables.tools_py_str.get(info_desc=py_desc)
            data_row['python_code']=py_content




@anvil.server.callable
def upload_binary_file(file):
    import os
    file_name = file.name
    file_content = file._content

    server_path = f'./upload_binary_file/{file_name}'
    os.makedirs(os.path.dirname(server_path), exist_ok=True)
    with open(server_path,'wb') as f:
        f.write(file_content)
    data_row = app_tables.binary_file_up_down.search(server_path=server_path)
    if len(data_row) == 0:
        app_tables.binary_file_up_down.add_row(
            server_path=server_path,
            file_name=file_name,
            tags = ""
        )
    else:
        row = app_tables.binary_file_up_down.get(server_path=server_path)
        row['file_name'] = file_name
        row['tags'] = ""
        row['python_code'] = file_content
    pass


@anvil.server.callable
def get_binary_file(server_path):
    import anvil.media
    media_object = anvil.media.from_file(server_path, "text/plain")
    return media_object



# 修改wg_server_public_ip 为 adsl 最新 ip
@anvil.server.http_endpoint("/wg_server_public_ip_update", methods=["POST","GET"], authenticate_users=False)
def wg_server_public_ip_update(**kw):
    return {}




