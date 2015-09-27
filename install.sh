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
    rm -rf /var/cache/yum/x86_64/7/yunshan-temp/
    yum clean expire-cache || true
}

setuprepo
echo "Installing Salt Tools ... "
yum --disablerepo=\* --enablerepo=yunshan-temp install -y \
salt-master salt-ssh lighttpd ntp sshpass python-termcolor python-netifaces 

echo "Config lighttpd ... "

sed -i 's#dir-listing.activate.*#dir-listing.activate = "enable"#' \
/etc/lighttpd/conf.d/dirlisting.conf
sed -i "s#server.document-root = .*#server.document-root = \"$pathtorepo/repo\"#" \
/etc/lighttpd/lighttpd.conf 
systemctl restart lighttpd
systemctl restart salt-master

systemctl enable lighttpd
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