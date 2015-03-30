ceph_repo:
  file.managed:
    - name: /etc/yum.repos.d/ceph.repo
    - source: salt://minions/files/ceph.repo

salt_pkg:
  pkg.installed:
    - name: salt-minion
    - require:
      - file: ceph_repo

salt_conf:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://minions/files/minion
    - template: jinja
    - defaults: 
      minion_id: {{ grains['fqdn_ip4'][0] }}
    - require: 
      - pkg: salt_pkg

salt_service: 
  service.running: 
    - name: salt-minion
    - enable: True
    - require: 
      - file: salt_conf