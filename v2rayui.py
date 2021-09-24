#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# v2rayui服务端的操作，启动，重启，关闭等
import json
import os
import commands


def open_port(port):
    cmd = [
        "iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport $1 -j ACCEPT",
        "iptables -I INPUT -m state --state NEW -m udp -p udp --dport $1 -j ACCEPT",
        "ip6tables -I INPUT -m state --state NEW -m tcp -p tcp --dport $1 -j ACCEPT",
        "ip6tables -I INPUT -m state --state NEW -m udp -p udp --dport $1 -j ACCEPT"
    ]

    for x in cmd:
        x = x.replace("$1", str(port))
        commands.getoutput(x)


def start():
    os.system("""supervisorctl start v2rayui""")


def stop():
    os.system("""supervisorctl stop v2rayui""")


def write(data):
    with open("/usr/local/v2rayui/panel.config", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == '__main__':
    with open("/usr/local/v2rayui/panel.config") as f:
        data = json.load(f)

    print("欢迎使用 v2rayui 面板 ---- By jasonhuang\n")
    print("当前面板用户名：" + str(data['username']))
    print("当前面板密码：" + str(data['password']))
    print("当前面板监听端口：" + str(data['port']))
    print("请输入数字选择功能：\n")
    print("1. 启动面板")
    print("2. 停止面板")
    print("3. 重启面板")
    print("4. 设置面板用户名和密码")
    print("5. 设置面板SSL")
    print("6. 设置面板端口")
    choice = str(input("\n请选择："))

    if choice == "1":
        start()
        open_port(data['port'])
        print("启动成功!")

    elif choice == "2":
        stop()
        print("停止成功！")

    elif choice == "3":
        stop()
        start()
        open_port(data['port'])
        print("重启成功!")
    elif choice == "4":
        new_username = str(raw_input("请输入新的用户名："))
        new_password = str(raw_input("请输入新的密码："))
        data['username'] = new_username
        data['password'] = new_password
        write(data)
        stop()
        start()
        print("用户名密码设置成功！")
    elif choice == "5":
        print("提示：只有在面板开启 V2ray TLS 功能时，面板自身的SSL功能才会正常运行。\n")
        print("1. 打开面板 SSL 功能")
        print("2. 关闭面板 SSL 功能")
        ssl_choice = str(input("请选择："))

        if ssl_choice == "1":
            data['use_ssl'] = "on"
            write(data)
            stop()
            start()
            print("面板SSL已开启！")
        else:
            data['use_ssl'] = "off"
            write(data)
            stop()
            start()
            print("面板SSL已关闭！")
    elif choice == "6":
        new_port = input("请输入新的面板端口：")
        data['port'] = int(new_port)
        write(data)
        stop()
        start()
        open_port(data['port'])
        print("面板端口已修改！")
