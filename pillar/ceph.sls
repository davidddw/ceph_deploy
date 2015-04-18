ceph:
  global: {cluster_network: 172.16.39.0/24, fsid: 294bc494-81ba-4c3c-ac5d-af7b3442a2a5,
    public_network: 172.16.39.0/24}
  mon: {interface: eth1}
  pools:
  - {name: capacity, pg_num: 128, pgp_num: 128}
  - {name: performance, pg_num: 128, pgp_num: 128}
nodes:
  centos81:
    devs:
      xvdc: {journal: xvdb1}
      xvde: {journal: xvdb2}
    journal:
      xvdb:
        partition: {count: 2, per_size: 4G}
    roles: [ceph-osd, ceph-mon]
  centos82:
    devs:
      xvdc: {journal: xvdb1}
      xvde: {journal: xvdb2}
    journal:
      xvdb:
        partition: {count: 2, per_size: 4G}
    roles: [ceph-osd, ceph-mon]
  master: {hostname: centos39_11, ip: 172.16.39.11}
  ntp:
    localnetworks: [172.16.39.0]
    ntpservers: [172.16.39.11]
