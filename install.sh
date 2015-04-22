#!/bin/bash

pathtorepo=`pwd`

function cleanup() {
    rm -f /etc/yum.repos.d/yunshan-temp.repo || true
}

function setuprepo() {
    echo "Setting up the temporary repository..."
    echo \
"[yunshan-temp]
baseurl=file://$pathtorepo/repo
gpgcheck=0
enabled=1
name=Yunshan temporary repository
" > /etc/yum.repos.d/yunshan-temp.repo

    echo "Cleaning Yum cache..."
    rm -rf /var/cache/yum/x86_64/6/yunshan-temp/
    yum clean expire-cache || true
}

setuprepo
echo "Installing Salt Tools ... "
yum --disablerepo=\* --enablerepo=yunshan-temp install -y \
salt-master salt-ssh monkey vim ntp sshpass

echo "Config monkey ... "
sed -i "s#DocumentRoot .*#DocumentRoot $pathtorepo/repo#" /etc/monkey/sites/default
sed -i '/dirlisting.so/s:# ::g' /etc/monkey/plugins.load
systemctl restart monkey
systemctl enable monkey
systemctl enable ntpd
systemctl enable salt-master

echo \
"
restrict 172.16.0.0 mask 255.255.0.0 nomodify notrap
server  127.127.1.0     # local clock
fudge   127.127.1.0 stratum 10
" >> /etc/ntp.conf


echo Done
cleanup
exit 0
