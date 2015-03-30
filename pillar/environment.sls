nodes:
  master:
    hostname: centos39_11
    ip: 172.16.39.11
  ntp:
    ntpservers: 
      - 172.16.39.11
    localnetworks:
      - 172.16.39.0
  centos131:
    roles:
      - ceph-osd
      - ceph-mon
    journal: 
      sdb:
        partition:
        - from: 0%
          to: 120G
        - from: 120G
          to: 240G
        - from: 240G
          to: 360G
    devs: 
      sdc:
        id: 0
        journal: sdb1
      sdd:
        id: 1
        journal: sdb2
      sde:
        id: 2
        journal: sdb3
  centos132:
    roles:
      - ceph-osd
      - ceph-mon
    journal: 
      sdb:
        partition:
        - from: 0%
          to: 120G
        - from: 120G
          to: 240G
        - from: 240G
          to: 360G
    devs:
      sdc:
        id: 3
        journal: sdb1
      sdd:
        id: 4
        journal: sdb2
      sde:
        id: 5
        journal: sdb3