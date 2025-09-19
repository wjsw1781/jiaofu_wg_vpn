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




# 产生配置  服务端配置 客户端配置都产生
@anvil.server.callable
def get_wg_server_client_conf(client_ip,server_ip,server_public_ip,ip_from,ip_to,wg_listen_port,RT_table_ID):
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
        Endpoint  = {wg_main_server_ip}:{ListenPort}
        AllowedIPs = 0.0.0.0/0, ::/0
        PersistentKeepalive = 25

    """

    # 服务端直接运行起来
    cmd_lunch_wg_server = f"""
        # 如果已经安装 wg 则不再安装
        if ! which wg-quick; then
          apt-get update &&   sudo apt-get install -y --no-install-recommends  wireguard-dkms wireguard-tools
        fi

        PORT_IN_USE=$(wg show all dump | awk '{{print $4}}' | grep -w "{ListenPort}")

        if [ -n "$PORT_IN_USE" ]; then
            echo "WARN: WireGuard ListenPort {ListenPort} 已被其他 WG 接口占用。正在关闭所有 WG 接口以避免冲突..."
            # 关闭所有 wg 进程 防止端口冲突 起不来wg 进程 清理路由表 路由规则 保持干净环境
            # 这里使用 wg show interfaces 获取所有接口名，然后逐个执行 wg-quick down
            wg show interfaces | xargs -n 1 | xargs -n 1 wg-quick down
            
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
    wg_server_public_ip = data_with_cmd["wg_server_public_ip"]
    wg_server_ip = data_with_cmd["wg_server_ip"]
    
    cmd = data_with_cmd["wg_server_conf"]

    print(f'     ssh root@{wg_server_public_ip}         -------> ',wg_server_public_ip)

    host = wg_server_public_ip
    port =22
    user = "root"
    password = "Spider666Linux"
    timeout = 15



    ret = {"host": host, "ok": False, "stdout": "", "stderr": "", "error": "","wg_server_public_ip":wg_server_public_ip}

    ssh = paramiko.SSHClient()

    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, port=port,username=user, password=password,timeout=timeout)

        wg_server_ip_sh = wg_server_ip.replace(".","_")
        
        local_wg_conf = f'./wg_conf/{wg_server_ip_sh}.sh'
        remote_wg_conf = f'/etc/wireguard/{wg_server_ip_sh}.sh'
        os.makedirs(os.path.dirname(local_wg_conf), exist_ok=True)
        
        with open(local_wg_conf,'w') as f:
            f.write(cmd)


        osftp = ssh.open_sftp()
        osftp.put(local_wg_conf,remote_wg_conf)
        osftp.close()

        cmd = f'bash {remote_wg_conf}  && echo "wangzhiqiangok--------------->" '

        stdin, stdout, stderr = ssh.exec_command(cmd,timeout=11111)


        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                ret["stdout"] += stdout.channel.recv(1024).decode(errors="ignore")
            if stdout.channel.recv_stderr_ready():
                ret["stderr"] += stdout.channel.recv_stderr(1024).decode(errors="ignore")
            time.sleep(1)

        ret["stdout"] += stdout.channel.recv(65535).decode(errors="ignore")
        ret["stderr"] += stdout.channel.recv_stderr(65535).decode(errors="ignore")
        ret["ok"]      = '/usr/bin/wg-quick' in ret["stdout"]
    except Exception as e:
        ret["error"] = str(e)
    finally:

        try:
            ssh.close()
        except:
            pass
    print(ret['ok'],ret['wg_server_public_ip'],'----------------->',ret["error"])

    return ret



@anvil.server.callable
def make_91_to_anvil():
    import json
    file_name = '91_client_script_up.json'
    with open(file_name,'r') as f:
        data = json.load(f)
    for index, i in enumerate(data):
        py_desc = str(index)
        py_content = i
        app_tables.tools_py_str.add_row(
            info_desc=py_desc,    
            python_code=py_content
        )
