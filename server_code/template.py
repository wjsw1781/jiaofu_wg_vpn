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
        
    
    cmd_lunch_wg_server = f"""
        # 如果已经安装 wg 则不再安装
        if ! which wg-quick; then
          apt-get update &&   sudo apt-get install -y --no-install-recommends  wireguard-dkms wireguard-tools
        fi

        PORT_IN_USE=$(wg show all dump | awk '{{print $4}}' | grep -w "{ListenPort}")

        if [ -n "$PORT_IN_USE" ]; then
            echo "WARN: WireGuard ListenPort {ListenPort} 已被其他 WG 接口占用。正在关闭所有 WG 接口以避免冲突..."
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


    """

    return client_script,cmd_lunch_wg_server

    # 纯 Python 的 SSH 客户端库




@anvil.server.callable
def ssh_exec(data_with_cmd):
    import paramiko    ,time,os
    now = time.time()
    ssh_pwd = data_with_cmd["ssh_pwd"]
    ssh_host = data_with_cmd["ssh_host"]
    ssh_port = data_with_cmd["ssh_port"]
    wg_server_ip = data_with_cmd["wg_server_ip"]
    
    cmd = data_with_cmd["wg_server_conf"]


    host = ssh_host
    port = ssh_port
    user = "root"
    password = ssh_pwd
    timeout = 15

    print(f'     ssh root@{ssh_host}  -p {ssh_port}    {ssh_pwd}   -------> ',ssh_host)


    ret = {"host": host,"ssh_port":ssh_port,"ok": False, "stdout": "", "stderr": "", "error": "","wg_server_public_ip":ssh_host}

    ssh = paramiko.SSHClient()

    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, port=port,username=user, password=password,timeout=timeout)

        wg_server_ip_sh = wg_server_ip.replace(".","_")
        


        # wg 服务端 sh 拉起文件
        local_wg_conf = f'./wg_conf/{wg_server_ip_sh}.sh'
        remote_wg_conf = f'/etc/wireguard/{wg_server_ip_sh}.sh'
        os.makedirs(os.path.dirname(local_wg_conf), exist_ok=True)
        
        with open(local_wg_conf,'w') as f:
            f.write(cmd)
        osftp = ssh.open_sftp()
        osftp.put(local_wg_conf, remote_wg_conf)
        osftp.close()

        cmd = f'bash {remote_wg_conf}'

        stdin, stdout, stderr = ssh.exec_command(cmd,timeout=10)


        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                ret["stdout"] += stdout.channel.recv(1024).decode(errors="ignore")
            if stdout.channel.recv_stderr_ready():
                ret["stderr"] += stdout.channel.recv_stderr(1024).decode(errors="ignore")
            time.sleep(1)

            if time.time() - now > 800:
                break

        ret["stdout"] += stdout.channel.recv(65535).decode(errors="ignore")
        ret["stderr"] += stdout.channel.recv_stderr(65535).decode(errors="ignore")

        ret["stderr"] = ret["stderr"]
        ret["stdout"] = ret["stdout"]
        ret["ok"]      = '/usr/bin/wg-quick' in ret["stdout"]


    except Exception as e:
        ret["error"] = str(e)
    print(ret['ok'],ret['wg_server_public_ip'],'----------------->',ret["error"])

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
    data = kw
    if not data or "wg_server_ip" not in data or "wg_server_public_ip" not in data:
        return (400, "need both     ---- wg_server_ip   wg_server_public_ip")

    row = app_tables.wg_conf.get(wg_server_ip=data["wg_server_ip"])
    if row is None:
        return (404, "wg_server_ip not exit")

    row["wg_server_public_ip"] = data["wg_server_public_ip"]
    return dict(row)




