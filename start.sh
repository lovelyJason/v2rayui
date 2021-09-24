#!/usr/bin/env bash

# 脚本入口
# PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
# export PATH

#Check Root
[ $(id -u) != "0" ] && { echo "${CFAILURE}Error: You must be root to run this script${CEND}"; exit 1; }

cd /usr/local/v2rayui
python3 /usr/local/v2rayui/app.py
