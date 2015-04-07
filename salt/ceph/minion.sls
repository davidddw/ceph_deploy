
include:
  - .repo

salt_pkg:
  pkg.installed:
    - name: salt-minion
    - fromrepo: ceph
    - require: 
      - pkgrepo: pkg_repo

/etc/salt/minion.d:
  file.directory:
    - user: root
    - group: root
    - mode: 755
    - makedirs: True
    - recurse:
      - user
      - group
      - mode

salt_conf:
  file.managed:
    - name: /etc/salt/minion.d/master.conf
    - source: salt://ceph/files/master.conf
    - template: jinja
    - require: 
      - pkg: salt_pkg
      - file: /etc/salt/minion.d
    - require_in:
      - service: salt_service

salt_service: 
  service.running: 
    - name: salt-minion
    - enable: True
    - watch: 
      - file: salt_conf
      - file: grains_conf

grains_conf:
  file.managed:
    - name: /etc/salt/grains
    - template: jinja
    - source: salt://ceph/files/grains
    - require:
      - pkg: salt_pkg
    - require_in:
      - service: salt_service

