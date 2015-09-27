#!/bin/bash

PWD=`pwd`
CLUSTER=172.16.39.0/24
NIC=eth0
PASSWD=yunshan3302
SALT_NIC=eth0
SALT_MASTER=`hostname`
SALT_IP=`ip addr show $SALT_NIC | grep -Po 'inet \K[\d.]+'`

echo "make ceph.yml."
cat <<EOF > ${PWD}/conf/ceph.yml
---
ceph:
  global: 
    cluster_network: ${CLUSTER}
    public_network: ${CLUSTER}
    fsid: 294bc494-81ba-4c3c-ac5d-af7b3442a2a5
    total_osd: 6
  mon: 
    interface: ${NIC}
  pools: 
  - name: capacity
    pg_num: 128
    pgp_num: 128
  - name: performance
    pg_num: 128
    pgp_num: 128
  - name: vm-metadata
    pg_num: 128
    pgp_num: 128
nodes: 
  master: 
    hostname: ${HOSTNAME}
    ip: ${SALT_IP}
  ntp: 
    ntpservers: 
    - ${SALT_IP}
    localnetworks: 
    - 172.16.39.0

  centos151: 
    ssd_list: []
    roles: 
    - ceph-osd
    - ceph-mon
    devs: 
    - sdc 
    - sdd 
     
  centos152:
    ssd_list: []
    roles: 
    - ceph-osd
    - ceph-mon
    devs: 
    - sdc 
    - sdd 
 
  centos153:
    ssd_list: []
    roles: 
    - ceph-osd
    - ceph-mon
    devs: 
    - sdc 
    - sdd 
...
EOF

echo "make master.yml."
cat <<EOF > ${PWD}/conf/master.yml
---
nodes: 
  - name: centos151 
    ip: 172.16.39.151
    user: root
    passwd: ${PASSWD}
  - name: centos152
    ip: 172.16.39.152
    user: root
    passwd: ${PASSWD}
  - name: centos153
    ip: 172.16.39.153
    user: root
    passwd: ${PASSWD}
...
EOF