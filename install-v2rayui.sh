#!/usr/bin/env bash

#Check Root
[ $(id -u) != "0" ] && { echo "${CFAILURE}Error: You must be root to run this script${CEND}"; exit 1; }

#Check OS
if [ -n "$(grep 'Aliyun Linux release' /etc/issue)" -o -e /etc/redhat-release ]; then
  OS=CentOS
  [ -n "$(grep ' 7\.' /etc/redhat-release)" ] && CentOS_RHEL_version=7
  [ -n "$(grep ' 6\.' /etc/redhat-release)" -o -n "$(grep 'Aliyun Linux release6 15' /etc/issue)" ] && CentOS_RHEL_version=6
  [ -n "$(grep ' 5\.' /etc/redhat-release)" -o -n "$(grep 'Aliyun Linux release5' /etc/issue)" ] && CentOS_RHEL_version=5
elif [ -n "$(grep 'Amazon Linux AMI release' /etc/issue)" -o -e /etc/system-release ]; then
  OS=CentOS
  CentOS_RHEL_version=6
elif [ -n "$(grep bian /etc/issue)" -o "$(lsb_release -is 2>/dev/null)" == 'Debian' ]; then
  OS=Debian
  [ ! -e "$(which lsb_release)" ] && { apt-get -y update; apt-get -y install lsb-release; clear; }
  Debian_version=$(lsb_release -sr | awk -F. '{print $1}')
elif [ -n "$(grep Deepin /etc/issue)" -o "$(lsb_release -is 2>/dev/null)" == 'Deepin' ]; then
  OS=Debian
  [ ! -e "$(which lsb_release)" ] && { apt-get -y update; apt-get -y install lsb-release; clear; }
  Debian_version=$(lsb_release -sr | awk -F. '{print $1}')
elif [ -n "$(grep Ubuntu /etc/issue)" -o "$(lsb_release -is 2>/dev/null)" == 'Ubuntu' -o -n "$(grep 'Linux Mint' /etc/issue)" ]; then
  OS=Ubuntu
  [ ! -e "$(which lsb_release)" ] && { apt-get -y update; apt-get -y install lsb-release; clear; }
  Ubuntu_version=$(lsb_release -sr | awk -F. '{print $1}')
  [ -n "$(grep 'Linux Mint 18' /etc/issue)" ] && Ubuntu_version=16
else
  echo "${CFAILURE}Does not support this OS, Please contact the author! ${CEND}"
  kill -9 $$
fi

# 安装依赖
if [ ${OS} == CentOS ];then
	pip install -r requirements.txt
	pip install supervisor

fi

cd /usr/local
git clone https://github.com/lovelyJason/v2rayui.git

# 生成配置
# cd /usr/local/v2rayui && python init.py
cp /usr/local/v2rayui/v2rayui.py /usr/local/bin/v2rayui
chmod +x /usr/local/bin/v2rayui
chmod +x /usr/local/v2rayui/start.sh      # web service启动入口

# 配置supervisorctl
# [program:test] #程序的名字，在supervisor中可以用这个名字来管理该程序。
# user=root #指定运行用户
# command=bash /root/1.sh #启动程序的命令
# autorstart=true #设置改程序是否虽supervisor的启动而启动
# directory=/home/lege #相当于在该目录下执行程序
# autorestart=true #程序停止之后是否需要重新将其启动
# startsecs=5 #重新启动时，等待的时间
# startretries=100 #重启程序的次数
# redirect_stderr=true #是否将程序错误信息重定向的到文件
# stdout_logfile=/home/lege/supervisor_log/log.txt #将程序输出重定向到该文件
# stderr_logfile=/home/lege/supervisor_log/err.txt #将程序错误信息重定向到该文件

mkdir /etc/supervisor
mkdir /etc/supervisor/conf.d
echo_supervisord_conf > /etc/supervisor/supervisord.conf
cat>>/etc/supervisor/supervisord.conf<<EOF
[include]
files = /etc/supervisor/conf.d/*.ini
EOF
touch /etc/supervisor/conf.d/v2rayui.ini
cat>>/etc/supervisor/conf.d/v2rayui.ini<<EOF
[program:v2rayui]
user=root
command=bash /usr/local/v2rayui/start.sh
stderr_logfile=/var/log/v2rayui.err.log
stdout_logfile=/var/log/v2rayui.out.log
autostart=true
autorestart=true
startsecs=5
priority=1
stopasgroup=true
killasgroup=true

environment=LANG="en_US.UTF-8",LC_ALL="en_US.UTF-8",LC_LANG="en_US.UTF-8"

[inet_http_server]
port=0.0.0.0:9001
username=user
password=123
EOF
supervisorctl reload

# 初始化v2rayui界面参数
read -p "请输入默认用户名[默认admin]： " un
read -p "请输入默认登录密码[默认admin]： " pw
read -p "请输入监听端口号[默认5000]： " uport
if [[ -z "${uport}" ]];then
	uport="5000"
else
	if [[ "$uport" =~ ^(-?|\+?)[0-9]+(\.?[0-9]+)?$ ]];then
		if [[ $uport -ge "65535" || $uport -le 1 ]];then
			echo "端口范围取值[1,65535]，应用默认端口号5000"
			unset uport
			uport="5000"
		else
			tport=`netstat -anlt | awk '{print $4}' | sed -e '1,2d' | awk -F : '{print $NF}' | sort -n | uniq | grep "$uport"`
			if [[ ! -z ${tport} ]];then
				echo "端口号已存在！应用默认端口号5000"
				unset uport
				uport="5000"
			fi
		fi
	else
		echo "请输入数字！应用默认端口号5000"
		uport="5000"
	fi
fi
if [[ -z "${un}" ]];then
	un="admin"
fi
if [[ -z "${pw}" ]];then
	pw="admin"
fi
sed -i "s/%%username%%/${un}/g" /usr/local/v2rayui/panel.config
sed -i "s/%%passwd%%/${pw}/g" /usr/local/v2rayui/panel.config
sed -i "s/%%port%%/${uport}/g" /usr/local/v2rayui/panel.config

supervisord -c /etc/supervisor/supervisord.conf
echo "supervisord -c /etc/supervisor/supervisord.conf">>/etc/rc.local     # 加入开机启动
chmod +x /etc/rc.local

echo "安装成功！
"
echo "面板端口：${uport}"
echo "默认用户名：${un}"
echo "默认密码：${pw}"
echo ''
echo "输入 v2rayui 并回车可以手动管理网页面板相关功能"

#清理垃圾文件
rm -rf /root/config.json
