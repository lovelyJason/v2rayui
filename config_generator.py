#! /usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import json

import requests
from requests.exceptions import ConnectTimeout


def getip():
    try:
        resp = requests.get("http://httpbin.org/ip", timeout=5).json()
        ip = resp.get("origin").split(", ")[0]
    except ConnectTimeout:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    return str(ip)

def open_port(port):
    cmd = [
        "iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport $1 -j ACCEPT",
        "iptables -I INPUT -m state --state NEW -m udp -p udp --dport $1 -j ACCEPT",
        "ip6tables -I INPUT -m state --state NEW -m tcp -p tcp --dport $1 -j ACCEPT",
        "ip6tables -I INPUT -m state --state NEW -m udp -p udp --dport $1 -j ACCEPT"
    ]

    for x in cmd:
        x = x.replace("$1", str(port))
        subprocess.getoutput(x)

# 读取v2ray.config服务端配置文件并进行修改再写入
def gen_server():
    with open("/usr/local/v2rayui/v2ray.config") as f:
        data = json.load(f)

    server_websocket = json.loads("""
    {
        "path": "",
        "headers": {
            "Host": ""
        }
    }
    """)

    server_mkcp = json.loads("""
    {
        "uplinkCapacity": 20,
        "downlinkCapacity": 100,
        "readBufferSize": 2,
        "mtu": 1350,
        "header": {
          "request": null,
          "type": "none",
          "response": null
        },
        "tti": 50,
        "congestion": false,
        "writeBufferSize": 2
      }
    """)

    server_tls = json.loads("""
    {
        "certificates": [
            {
                "certificateFile": "/path/to/example.domain/fullchain.cer",
                "keyFile": "/path/to/example.domain.key"
            }
        ]
    }
    """)

    server_raw = """
    {
        "log": {
            "access": "/var/log/v2ray/access.log",
            "error": "/var/log/v2ray/error.log",
            "loglevel": "info"
        },
        "inbound": {
            "port": 39885,
            "protocol": "vmess",
            "settings": {
                "clients": [
                    {
                        "id": "475161c6-837c-4318-a6bd-e7d414697de5",
                        "level": 1,
                        "alterId": 100
                    }
                ]
            },
            "streamSettings": {
                "network": "ws"
            }
        },
        "outbound": {
            "protocol": "freedom",
            "settings": {}
        },
        "outboundDetour": [
            {
                "protocol": "blackhole",
                "settings": {},
                "tag": "blocked"
            }
        ],
        "routing": {
            "strategy": "rules",
            "settings": {
                "rules": [
                    {
                        "type": "field",
                        "ip": [
                            "0.0.0.0/8",
                            "10.0.0.0/8",
                            "100.64.0.0/10",
                            "127.0.0.0/8",
                            "169.254.0.0/16",
                            "172.16.0.0/12",
                            "192.0.0.0/24",
                            "192.0.2.0/24",
                            "192.168.0.0/16",
                            "198.18.0.0/15",
                            "198.51.100.0/24",
                            "203.0.113.0/24",
                            "::1/128",
                            "fc00::/7",
                            "fe80::/10"
                        ],
                        "outboundTag": "blocked"
                    }
                ]
            }
        }
    }
    """
    server = json.loads(server_raw)
    if data['protocol'] == "vmess":
        server['inbound']['port'] = int(data['port'])
        server['inbound']['settings']['clients'][0]['id'] = data['uuid']
        server['inbound']['settings']['clients'][0]['security'] = data[
            'encrypt']

    elif data['protocol'] == "mtproto":
        """ MTProto don't needs client config, just use Telegram"""
        server['inbound']['port'] = int(data['port'])
        server['inbound']['protocol'] = "mtproto"
        server['inbound']['settings'] = dict()
        server['inbound']['settings']['users'] = list()
        server['inbound']['settings']['users'].append(
            {'secret': data['secret']})
        server['inbound']['tag'] = "tg-in"

        server['outbound']['protocol'] = "mtproto"
        server['outbound']['tag'] = "tg-out"

        server['routing']['settings']['rules'].append({
            "type": "field",
            "inboundTag": ["tg-in"],
            "outboundTag": "tg-out"
        })

    if data['trans'] == "tcp":
        server['inbound']['streamSettings'] = dict()
        server['inbound']['streamSettings']['network'] = "tcp"

    elif data['trans'].startswith("mkcp"):
        server['inbound']['streamSettings'] = dict()
        server['inbound']['streamSettings']['network'] = "kcp"
        server['inbound']['streamSettings']['kcpSettings'] = server_mkcp

        if data['trans'] == "mkcp-srtp":
            server['inbound']['streamSettings']['kcpSettings']['header'][
                'type'] = "srtp"
        elif data['trans'] == "mkcp-utp":
            server['inbound']['streamSettings']['kcpSettings']['header'][
                'type'] = "utp"
        elif data['trans'] == "mkcp-wechat":
            server['inbound']['streamSettings']['kcpSettings']['header'][
                'type'] = "wechat-video"

    elif data['trans'] == "websocket":
        server['inbound']['streamSettings'] = dict()
        server['inbound']['streamSettings']['network'] = "ws"
        server['inbound']['streamSettings']['wsSettings'] = server_websocket
        server['inbound']['streamSettings']['wsSettings']['headers'][
            'Host'] = data['domain']

    if data['tls'] == "on":
        server['inbound']['streamSettings']['security'] = "tls"
        server_tls['certificates'][0][
            'certificateFile'] = "/root/.acme.sh/{0}/fullchain.cer".format(
                data['domain'])
        server_tls['certificates'][0][
            'keyFile'] = "/root/.acme.sh/{0}/{0}.key".format(
                data['domain'], data['domain'])
        server['inbound']['streamSettings']['tlsSettings'] = server_tls

    with open("/etc/v2ray/config.json", "w") as f:
        f.write(json.dumps(server, indent=2))

# 写入vray.config客户端配置，方便前端直接下载配置文件
def gen_client():
    client_raw = """
    {
      "policy": null,
      "log": {
        "access": "",
        "error": "",
        "loglevel": "warning"
      },
      "inbounds": [
        {
          "tag": "proxy",
          "port": 10808,
          "listen": "0.0.0.0",
          "protocol": "socks",
          "sniffing": {
            "enabled": true,
            "destOverride": [
              "http",
              "tls"
            ]
          },
          "settings": {
            "auth": "noauth",
            "udp": true,
            "ip": null,
            "address": null,
            "clients": null
          },
          "streamSettings": null
        }
      ],
      "outbounds": [
        {
          "tag": "proxy",
          "protocol": "vmess",
          "settings": {
            "vnext": [
              {
                "address": "v2us.j.ssnss.live",
                "port": 443,
                "users": [
                  {
                    "id": "dc1ffbb4-f291-4b5c-be8f-3423a2353134",
                    "alterId": 0,
                    "email": "t@t.tt",
                    "security": "auto"
                  }
                ]
              }
            ],
            "servers": null,
            "response": null
          },
          "streamSettings": {
            "network": "ws",
            "security": "tls",
            "tlsSettings": {
              "allowInsecure": true,
              "serverName": "v2us.j.ssnss.live"
            },
            "tcpSettings": null,
            "kcpSettings": null,
            "wsSettings": {
              "connectionReuse": true,
              "path": "/index",
              "headers": {
                "Host": "v2us.j.ssnss.live"
              }
            },
            "httpSettings": null,
            "quicSettings": null
          },
          "mux": {
            "enabled": true,
            "concurrency": 8
          }
        },
        {
          "tag": "direct",
          "protocol": "freedom",
          "settings": {
            "vnext": null,
            "servers": null,
            "response": null
          },
          "streamSettings": null,
          "mux": null
        },
        {
          "tag": "block",
          "protocol": "blackhole",
          "settings": {
            "vnext": null,
            "servers": null,
            "response": {
              "type": "http"
            }
          },
          "streamSettings": null,
          "mux": null
        }
      ],
      "stats": null,
      "api": null,
      "dns": null,
      "routing": {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
          {
            "type": "field",
            "port": null,
            "inboundTag": [
              "api"
            ],
            "outboundTag": "api",
            "ip": null,
            "domain": null
          }
        ]
      }
    }
    """

    cLient_mkcp = json.loads("""
    {
        "mtu": 1350,
        "tti": 50,
        "uplinkCapacity": 20,
        "downlinkCapacity": 100,
        "congestion": false,
        "readBufferSize": 2,
        "writeBufferSize": 2,
        "header": {
            "type": "none"
        }
    }
    """)

    mux_enable = json.loads("""
    {
            "enabled": true
    }
    """)

    mux_disable = json.loads("""
    {
      "enabled": false
    }
    """)

    client = json.loads(client_raw)

    with open("/usr/local/v2rayui/v2ray.config") as f:
        data = json.load(f)

    outbound = client['outbounds'][0]
    if data['mux'] == "on":
        outbound['mux']['enabled'] = True
    elif data['mux'] == "off":
        outbound['mux']['enabled'] = False

    if data['domain'] == "none":
        outbound['settings']['vnext'][0]['address'] = data['ip']
    else:
        outbound['settings']['vnext'][0]['address'] = data['domain']

    outbound['settings']['vnext'][0]['port'] = int(data['port'])
    outbound['settings']['vnext'][0]['users'][0]['id'] = data['uuid']
    outbound['settings']['vnext'][0]['users'][0]['security'] = data['encrypt']

    if data['trans'] == "websocket":
        outbound['streamSettings']['network'] = "ws"

    elif data['trans'].startswith("mkcp"):
        if data['trans'] == "mkcp-srtp":
            cLient_mkcp['header']['type'] = "srtp"
        elif data['trans'] == "mkcp-utp":
            cLient_mkcp['header']['type'] = "utp"
        elif data['trans'] == "mkcp-wechat":
            cLient_mkcp['header']['type'] = "wechat-video"

        outbound['streamSettings']['network'] = "kcp"
        outbound['streamSettings']['kcpSettings'] = cLient_mkcp

    elif data['trans'] == "tcp":
        outbound['streamSettings']['network'] = "tcp"

    if data['tls'] == "on":
        outbound['streamSettings']['security'] = "tls"
        outbound['streamSettings']['tlsSettings']['serverName'] = data['domain']
        outbound['streamSettings']['wsSettings']['headers']['Host'] = data['domain']

    with open("/usr/local/etc/v2ray/config.json", "w") as f:
        f.write(json.dumps(client, indent=2))

    with open("/usr/local/v2rayui/static/config.json", "w") as f:
        f.write(json.dumps(client, indent=2))
