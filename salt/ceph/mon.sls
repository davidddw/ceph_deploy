{% import 'ceph/global_vars.jinja' as conf with context -%}
{% set ip = salt['network.ip_addrs'](conf.mon_interface)[0] -%}
{% set secret = '/var/lib/ceph/tmp/' + conf.cluster + '.mon.keyring' -%}
{% set monmap = '/var/lib/ceph/tmp/' + conf.cluster + 'monmap' -%}

include:
  - .ceph

ceph_mon:
  ceph_deploy.create_mon:
    - cluster: {{ conf.cluster }}
    - fsid: {{ conf.fsid }}
    - monmap: {{ monmap }} 
    - curr_host: {{ conf.host }}
    - hosts_infos:
      {% for mon in conf.hosts %} 
      - host: {{ mon['host'] }}
        ip: {{ mon['ip'] }}
      {% endfor %}   