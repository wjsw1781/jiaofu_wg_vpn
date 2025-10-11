logs="""


[INFO  anvil.app-server.core] [SERVER] 
[INFO  anvil.app-server.core] [SERVER] 
[INFO  anvil.app-server.core] [SERVER] Last login: Sat Oct 11 11:58:29 2025 from 10.10.20.254
bash /etc/wireguard/10_5_0_50.sh
root@88al10:~# bash /etc/wireguard/10_5_0_50.sh
/usr/bin/wg-quick
WARN: WireGuard ListenPort 50006 已被其他 WG 接口占用。正在关闭 指定WG 接口而不是所有接口以避免冲突...
[#] ip link delete dev 10_5_0_50
所有 WireGuard 接口已关闭。
457    10_5_0_50
net.ipv4.ip_forward = 1
主网卡-------> ppp0
wg-quick: `10_5_0_50' is not a WireGuard interface
[#] ip link add 10_5_0_50 type wireguard
[#] wg setconf 10_5_0_50 /dev/fd/63
[#] ip -4 address add 10.5.0.50/30 dev 10_5_0_50
[#] ip link set mtu 1330 up dev 10_5_0_50
[#] ip -6 route add ::/0 dev 10_5_0_50 table 10_5_0_50
[#] ip -4 route add 0.0.0.0/0 dev 10_5_0_50 table 10_5_0_50
公网IP开始: [{"ifindex":69,"ifname":"ppp0","flags":["POINTOPOINT","MULTICAST","NOARP","UP","LOWER_UP"],"mtu":1492,"qdisc":"fq_codel","operstate":"UNKNOWN","group":"default","txqlen":3,"addr_info":[{"family":"inet","local":"121.227.129.110","address":"121.227.129.1","prefixlen":32,"scope":"global","label":"ppp0","valid_life_time":4294967295,"preferred_life_time":4294967295}]}]
公网IP结束
root@88al10:~# 
[INFO  anvil.app-server.core] [SERVER] 
[INFO  anvil.app-server.core] [SERVER] 
[INFO  anvil.app-server.core] [SERVER] Last login: Sat Oct 11 11:58:05 2025 from 10.10.20.254
bash /etc/wireguard/10_5_0_46.sh
root@88al9:~# bash /etc/wireguard/10_5_0_46.sh
/usr/bin/wg-quick
WARN: WireGuard ListenPort 50006 已被其他 WG 接口占用。正在关闭 指定WG 接口而不是所有接口以避免冲突...
[#] ip link delete dev 10_5_0_46
所有 WireGuard 接口已关闭。
456    10_5_0_46
net.ipv4.ip_forward = 1
主网卡-------> ppp0
wg-quick: `10_5_0_46' is not a WireGuard interface
[#] ip link add 10_5_0_46 type wireguard
[#] wg setconf 10_5_0_46 /dev/fd/63



所有wg_节点peer_现状_shell开始:   10_1_0_22     1WitXhkgODVBBPcoEu4zVmYU8ebjslLqF+lEnfVy8kA=  (none)  124.90.93.241:1032  0.0.0.0/0,::/0  1758764986  64497986  394464972  25  1398984
w_10_203_7_1  9wxDcZMb+VSmp5n+ckoUc2A4/yK2/KXnNxYTSbo9/is=  (none)  124.90.92.80:49366  0.0.0.0/0,::/0  1758458974  6356      39273188   25  1704996
10_3_0_22     e3fOovzbmwnJpUNeCW+mqm/wRXICcwuWQ6k0MLxuIkA=  (none)  (none)              0.0.0.0/0,::/0  0           0         0          25  1760163970
10_5_0_22     cqJchuZx+hWXQw/5gRXZkoZRSRnhDtzfVozsZIUzThU=  (none)  (none)              0.0.0.0/0,::/0  0           0         0          25  1760163970
10_7_0_22     h9TnyQYwy/MrG2vBCBpoa5G7pVoWm7E03eEJ+SKgCwk=  (none)  (none)              0.0.0.0/0,::/0  0           0         0          25  1760163970
所有wg_节点peer_现状_shell结束
Device "ppp01" does not exist.
公网IP_shell开始: 
公网IP_shell结束
"""


# 2) 解析整段输出
# -------------------------------------------------
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

公网IP_shell=make_shell_stub({"公网IP_shell":'$( ip -j -4 addr show dev ppp01 )'})
所有wg_节点peer_现状_shell=make_shell_stub({"所有wg_节点peer_现状_shell":"""  $(    wg show all dump | grep none  | awk -v now=$(date +%s) '{{print $0,now-$6}}' | sort -k10n | column -t    )"""})
    
print(所有wg_节点peer_现状_shell)
print(公网IP_shell)

print('\n\n\n\n')
for key in parse_stub_output(logs):
    print(key, parse_stub_output(logs)[key])
    print('\n-------\n')



"""



        # 如果已经安装 wg 则不再安装
        if ! which wg-quick; then
          apt-get update &&   sudo apt-get install -y --no-install-recommends  wireguard-dkms wireguard-tools
        fi

        PORT_IN_USE=$(wg show all dump | awk '{print $4}' | grep -w "50006")

        if [ -n "$PORT_IN_USE" ]; then
            echo "WARN: WireGuard ListenPort 50006 已被其他 WG 接口占用。正在关闭 指定WG 接口而不是所有接口以避免冲突..."
            # 关闭所有 wg 进程 防止端口冲突 起不来wg 进程 清理路由表 路由规则 保持干净环境
            # 这里使用 wg show interfaces 获取所有接口名，然后逐个执行 wg-quick down  应该是找到指定的旧接口名
            wg show all dump | grep -v none | grep "50006" | awk '{print $1}' | xargs -n1 wg-quick down
            
            echo "所有 WireGuard 接口已关闭。"
            # wg show interfaces | xargs -n 1 |xargs -n1 wg-quick down
            # sed -i '/10.*$/d' /etc/iproute2/rt_tables
            # sed -i '/^$/d' /etc/iproute2/rt_tables
            # ip rule list | grep -v -E "lookup (local|main|default)" | awk '{print $1}' | tr -d ':' | xargs -I {} ip rule del pref {}

        else
            echo "WireGuard ListenPort 50006 未被占用，可以正常启动。"
        fi


        echo "
        [Interface]
        Address = 10.5.0.2/30
        ListenPort = 50006
        PrivateKey = qHLbV7CEPOCi57Cz77adDhtHWRaT1whlP49CZm6E8W0=
        Table = 10_5_0_2
        MTU = 1330


        [Peer]
        PublicKey = 2ZqIH0PLiQo9PZc+hY57XhXfA2trPrLTTvXph+LZ1gQ=
        AllowedIPs = 0.0.0.0/0, ::/0
        PersistentKeepalive = 25
    " > /etc/wireguard/10_5_0_2.conf

        if ! cat /etc/iproute2/rt_tables | grep "10_5_0_2"; then
            echo "445    10_5_0_2" >> /etc/iproute2/rt_tables
        fi

        sysctl -w net.ipv4.ip_forward=1 2>/dev/null
        wg_MAIN_INTERFACE_server=$(ip route | awk '/^default/ {for(i=1;i<=NF;i++) if ($i=="dev") {print $(i+1); exit}}')
        iptables -t nat -D POSTROUTING -o $wg_MAIN_INTERFACE_server -j MASQUERADE
        iptables -t nat -A POSTROUTING -o $wg_MAIN_INTERFACE_server -j MASQUERADE
        echo "主网卡-------> $wg_MAIN_INTERFACE_server"
        
        ip -4 route flush table 10_5_0_2
        ip -6 route flush table 10_5_0_2
        
        wg-quick down 10_5_0_2
        wg-quick up 10_5_0_2

        ip rule list   | grep 10.5.0.1 | awk '{print $1}' | tr -d ':' |xargs -r -I{} ip rule del pref {}
        # ip rule add to 10.5.0.1 lookup 10_5_0_2

        ip rule list   | grep 10.4.0.0/16 | awk '{print $1}' | tr -d ':' |xargs -r -I{} ip rule del pref {}
        ip rule add to 10.4.0.0/16 lookup 10_5_0_2



# 保活 py 逻辑 上报逻辑更新adsl最新公网 ip 的逻辑
cat << 'EOF' > /etc/wireguard/o0_0节点保活_巡检指定wg.py
import os
import subprocess
import sys
import time
import shutil




# --- 配置部分 ---
systemd服务名 = "wzq_auto_py_task"          # systemd unit 文件名称 (如 my-auto-task.service)
部署目录 = "/usr/local/bin"                 # 脚本最终存放的目录
python_解释器= "/usr/bin/python3"



当前脚本文件绝对路径名 = os.path.abspath(__file__)
当前脚本文件名 = os.path.basename(__file__)


目标脚本路径 = os.path.join(部署目录, 当前脚本文件名) # 自部署时自身会复制到这里
服务文件路径 = f"/etc/systemd/system/{systemd服务名}.service"

# --- Systemd Service 文件内容 (使用你提供的格式) ---
服务文件内容 = f"""
[Unit]
Description=up_someting_by_python_by_systemd (w4_3_up_wg_server_client_diqujingweidu)
After=network.target

[Service]
ExecStart={python_解释器} {目标脚本路径}
Type=simple
Environment=PYTHONUNBUFFERED=1
Restart=always
RestartSec=60
User=root

[Install]
WantedBy=multi-user.target
"""


# --- 自部署逻辑 ---  说明是第一次从用户态进行运行  文件名可以自定义 但是服务名字字不能变
if 当前脚本文件绝对路径名 != 目标脚本路径:
    try:
        # 先删除旧的 systemd 服务文件 (如果存在)
        os.system(f"""
                cd /etc/systemd/system/ && ll
                rm {目标脚本路径}
                ps aux | grep python
                pkill -f python3
                pkill -f python
                ps aux | grep python
        """)
        
        os.system(f"sudo systemctl stop {systemd服务名}.service") # 1
        os.system(f"sudo systemctl disable {systemd服务名}.service") # 2
        os.system(f"sudo systemctl daemon-reload ")
        if os.path.exists(服务文件路径):
            os.remove(服务文件路径)
        if os.path.exists(目标脚本路径):
            os.remove(目标脚本路径)

        shutil.copy2(当前脚本文件名, 目标脚本路径)
        os.chmod(目标脚本路径, 777)
        with open(服务文件路径, "w") as f:
            f.write(服务文件内容.strip())

        os.system(f"sudo systemctl restart {systemd服务名}.service") # 1
        os.system(f"sudo systemctl enable {systemd服务名}.service") # 2
        os.system(f"sudo systemctl daemon-reload ")



        print(f"""

                {python_解释器} {目标脚本路径}
                cd /etc/systemd/system/ && ll
                rm {目标脚本路径}
                ps aux | grep python
                pkill -f python3
                pkill -f python
                sudo systemctl stop wzq_auto_py_task
                sudo systemctl disable wzq_auto_py_task
                sudo systemctl daemon-reload
                ps aux | grep python


                systemctl status {systemd服务名}    

                systemctl restart {systemd服务名}    

                sudo journalctl -u {systemd服务名} -f

                
                sudo journalctl -u wzq_auto_py_task -f

                watch -n 1 systemctl status {systemd服务名}

        """)

    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：部署失败：{e}")



# 主逻辑

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 服务已启动。开始执行主任务...")


# 第一个主逻辑  遍历所有 wiregard 的节点 最后握手时间

cmds = f"""
    wg show all dump | grep none  | awk -v now=$(date +%s) '{{print $0,now-$6}}' | sort -k10n
"""
print(cmds)

res = os.popen(cmds).read().splitlines()
for line in res:
    wg_name = line.split()[0]
    last_handshake = line.split()[-1]
    if int(last_handshake) < 180:
        # print(f" {wg_name} 无需重启 最后握手时间 小于 180 秒")
        continue
    if '0.0.0.0/0' in line:
        # print(f" {wg_name} 无需重启 根本没有链接 只是服务器这边预留好的  0.0.0.0/0")
        continue
    print(f" {wg_name} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>需要重启")
    os.system(f""" bash /etc/wireguard/{wg_name}.sh >/dev/null 2>&1 """)
    
# 遍历所有 wiregard 目录下的所有 .sh 文件 如果没有执行过 则执行 就是根据网卡名字看看有没有就行了
all_wg_interfaces = os.popen(" wg show all dump ").read()
for file in os.listdir('/etc/wireguard/'):
    if not file.endswith('.sh'):
        continue
    file = file.replace('.sh', '')
    if file in all_wg_interfaces:
        continue
    print(f" {file} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>需要重启")
    os.system(f""" bash /etc/wireguard/{file}.sh >/dev/null 2>&1 """)


    









EOF

pkill -f python3 
nohup python3 /etc/wireguard/o0_0节点保活_巡检指定wg.py > /dev/null 2>&1 &

# 埋点分析统计
echo "公网IP_shell开始"
$( ip -j -4 addr show dev ppp01 )
echo "公网IP_shell结束"
echo "所有wg_节点peer_现状_shell开始"
  wg show all dump | grep none  | awk -v now=$(date +%s) '{print $0,now-$6}' | sort -k10n | column -t    
echo "所有wg_节点peer_现状_shell结束"







"""