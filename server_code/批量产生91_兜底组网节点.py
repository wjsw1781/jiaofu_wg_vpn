
# -*- coding: utf-8 -*-
import sys,os
import inspect
import os
current_file_path = inspect.getfile(inspect.currentframe())
current_file_path = os.path.abspath(current_file_path)
basedir = os.path.dirname(current_file_path)
    
os.chdir(basedir)
parent_dir = os.path.dirname(basedir)

sys.path.append(basedir)

sys.path.append(parent_dir)
sys.path.append(os.path.dirname(parent_dir))
sys.path.append(os.path.dirname(os.path.dirname(parent_dir)))



print('basedir-------------->',basedir)
sys.path.append(basedir)






from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import subprocess, time,os,sys,json,random,ipaddress

def get_公私钥(ip):
    import os ,json ,subprocess,pathlib
    file_name = '/root/socks_ss_gfw_ss_socks/linux_透明代理_多路组网_子网划分/all_ip_pubkey_prikey.json'
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




# 需要多少个 minipc 机器
need_how_many_client = 100

# 基础配置
from_ip = "10.91.0.0/16"
wg_main_server_ip = '47.97.83.157'
from_rt_id = 300
from_listen_port = 55001
RT_table_IDs = list(range(from_rt_id,from_rt_id+need_how_many_client))
ListenPorts = list(range(from_listen_port,from_listen_port+need_how_many_client))
wg_server_ips = []

# udp 接受的 mtu 必须要小
MTU = 1380
prefixlen = 24

# 规定 服务器端ip 客户端 ip 网段信息
wg_ip_obj = ipaddress.ip_network(from_ip).subnets(new_prefix=prefixlen)
for subnet in wg_ip_obj:                                                    # 10.101.0.0/24 … 10.101.255.0/24
    server_ip = subnet.network_address + 1  
    wg_ip =f"{server_ip}/{subnet.prefixlen}"
    wg_server_ips.append(wg_ip)
wg_server_ips= wg_server_ips[2:-2]




process_bar = tqdm(total=need_how_many_client)

data_sh_client = []
# 生成客户端的配置文件
for i in range(need_how_many_client):
    process_bar.update(1)

    # 服务器wg ip 地址  
    wg_ip_server_with_prefixlen =  str(wg_server_ips[i])
    wg_all_current_ips = list(ipaddress.ip_network(wg_ip_server_with_prefixlen,strict=False).hosts())

    wg_ip_server = str(wg_all_current_ips[0])
    wg_ip_client = str(wg_all_current_ips[-1])


    wg_table_server = f"w_{wg_ip_server.replace('.','_')}"
    wg_table_client = f"w_{wg_ip_client.replace('.','_')}"

    wg_if_client =wg_table_client
    wg_if_server =wg_table_server



    ListenPort = ListenPorts[i]
    RT_table_ID = RT_table_IDs[i]

    wg_conf_file_client = f"/etc/wireguard/{wg_table_client}.conf"
    wg_conf_file_server = f"/etc/wireguard/{wg_table_server}.conf"



    print('当前处理的wg队列配置文件', wg_conf_file_server , wg_conf_file_client)

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
    with open(wg_conf_file_server, "w") as f:
        f.write(server_conf)


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
    with open(wg_conf_file_client, "w") as f:
        f.write(client_conf)

    # 服务端直接运行起来
    cmd_lunch_wg_server = f"""
        sysctl -w net.ipv4.ip_forward=1

        if ! cat /etc/iproute2/rt_tables | grep "{wg_table_server}"; then
            echo "{RT_table_ID}    {wg_table_server}" >> /etc/iproute2/rt_tables
        fi
        sysctl -w net.ipv4.ip_forward=1 2>/dev/null

        wg-quick down {wg_conf_file_server}
        wg-quick up {wg_conf_file_server}

        ip rule list   | grep {wg_ip_client} | awk '{{print $1}}' | tr -d ':' |xargs -r -I{{}} ip rule del pref {{}}
        ip rule add to {wg_ip_client} lookup {wg_table_server}

    """



    
    # 客户端生成下发脚本 一键运行
    client_script = f"""
        sysctl -w net.ipv4.ip_forward=1

        echo "{client_conf}" > {wg_conf_file_client}

        if ! cat /etc/iproute2/rt_tables | grep "{wg_table_client}"; then
            echo "{RT_table_ID}    {wg_table_client}" >> /etc/iproute2/rt_tables
        fi
        sysctl -w net.ipv4.ip_forward=1 2>/dev/null

        wg-quick down {wg_if_client}  2>/dev/null
        ip -4 route flush table {wg_table_client}
        ip -6 route flush table {wg_table_client}
        wg-quick up {wg_if_client} 2>/dev/null

        ip rule list   | grep {from_ip} | awk '{{print $1}}' | tr -d ':' |xargs -r -I{{}} ip rule del pref {{}}
        ip rule add to {from_ip} lookup {wg_table_client}


    """
    os.system(cmd_lunch_wg_server)
    with open(f'/etc/wireguard/{wg_if_server}.conf', "w") as f:
        f.write(cmd_lunch_wg_server)


    data_sh_client.append(client_script)
# print(data_sh_client)
# json dump 到一个文件 
with open('91_client_script_up.json', 'w') as f:
    json.dump(data_sh_client, f)
