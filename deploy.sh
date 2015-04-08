#!/bin/bash

set -x

prepair()
{
	rm -fr  /var/cache/salt/master/* 
	systemctl restart salt-master
	salt-key -D -y

	
	mkdir -p /etc/salt/master.d/
	cat << EOF > /etc/salt/master.d/livecloud.conf
auto_accept: False

file_roots:
  base:
      - /opt/livecloud/salt/

pillar_roots:
  base:
      - /opt/livecloud/pillar/

reactor:
  - 'salt/minion/*/start':
    - /opt/calamari/salt/reactor/start.sls
EOF

	cat <<EOF > /etc/salt/roster 
centos151:
  host: 172.16.39.151
  user: root
  passwd: yunshan3302
centos152:
  host: 172.16.39.152
  user: root
  passwd: yunshan3302
centos153:
  host: 172.16.39.153
  user: root
  passwd: yunshan3302
EOF

	cat << EOF >> /root/.ssh/config
host 172.16.39.151
    StrictHostKeyChecking no
host 172.16.39.152
    StrictHostKeyChecking no
host 172.16.39.151
    StrictHostKeyChecking no
EOF
}

prepair
salt-ssh 'centos15[1-3]' -r 'echo "172.16.39.11 centos39_11" >> /etc/hosts'
salt-ssh 'centos15[1-3]' state.sls ceph.minion
sleep 10
salt-key -a centos15[1-3] -y
sleep 10
salt 'centos15[1-3]' state.highstate -l all -v 
#salt 'centos15[1-3]' ceph.journal
#salt 'centos15[1-3]' ceph.mon
#salt 'centos15[1-3]' ceph.osd
#salt 'centos15[1-3]' ceph.pool
#salt 'centos15[1-3]' kvm.pool

