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
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
"""


# --- 自部署逻辑 ---  说明是第一次从用户态进行运行  文件名可以自定义 但是服务名字字不能变
if 当前脚本文件绝对路径名 != 目标脚本路径:
    try:
        # 先删除旧的 systemd 服务文件 (如果存在)
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


                systemctl status {systemd服务名}    

                systemctl restart {systemd服务名}    

                sudo journalctl -u {systemd服务名} -f

                watch -n 1 systemctl status {systemd服务名}

        """)

    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：部署失败：{e}")
        sys.exit(1)



# 主逻辑

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 服务已启动。开始执行主任务...")


# 第一个主逻辑  遍历所有 wiregard 的节点 最后握手时间

cmds = f"""
    wg show all dump | grep none | column -t | awk -v now=$(date +%s) '{{print $0,now-$6}}' | sort -k10n
"""
res = os.popen(cmds).read().splitlines()
for line in res:
    wg_name = line.split()[0]
    last_handshake = line.split()[-1]
    if int(last_handshake) < 180:
        continue
    
    print(f" {wg_name} 需要重启")
    os.system(f""" bash /etc/wireguard/{wg_name}.sh """)



    

# 第二个主逻辑  上传日志 埋点



