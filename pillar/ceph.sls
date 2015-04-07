ceph:
  global:
    cluster_network: 172.16.1.0/24
    fsid: 294bc494-81ba-4c3c-ac5d-af7b3442a2a5
    public_network: 172.16.1.0/24
  mon:
    interface: "em1"
  pools:
    - name: capacity
      pg_num: 128
      pgp_num: 128
    
    - name: performance
      pg_num: 128
      pgp_num: 128

nodes:
  master:
    hostname: centos39_11
    ip: 172.16.39.11
  ntp:
    ntpservers: 
      - 172.16.39.11
    localnetworks:
      - 172.16.39.0
  centos81:
    roles:
      - ceph-osd
      - ceph-mon
    journal: 
      xvdb:
        partition:
        - from: 0%
          to: 4G
        - from: 4G
          to: 8G
    devs: 
      xvdc:
        journal: xvdb1
      xvde:
        journal: xvdb2

  centos82:
    roles:
      - ceph-osd
      - ceph-mon
    journal: 
      xvdb:
        partition:
        - from: 0%
          to: 4G
        - from: 4G
          to: 8G
    devs:
      xvdc:
        journal: xvdb1
      xvde:
        journal: xvdb2