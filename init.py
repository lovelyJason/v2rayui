#! /usr/bin/env python
# -*- coding: utf-8 -*-
# import json
import config_generator
# import uuid

# with open("/usr/local/v2rayui/v2ray.config") as f:
#     try:
#         data = json.load(f)
#     except ValueError:
#         data = {}

# data['uuid'] = str(uuid.uuid4())
# data['ip'] = config_generator.getip()
# config_generator.open_port(data['port'])

# with open("/usr/local/v2rayui/v2ray.config", "w") as f:
#     json.dump(data, f)

# 生成v2ray服务端和客户端配置
# config_generator.gen_server()
config_generator.gen_client()
