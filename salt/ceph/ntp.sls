{% set ntpservers = salt['pillar.get']('nodes:ntp:ntpservers') -%}

include:
  - .repo

ntp_pkg:
  pkg.installed:
    - name: ntp
    - fromrepo: ceph
    - require:
      - pkgrepo: pkg_repo

ntp_conf_setup:
  file.managed:
    - name: /etc/ntp.conf
    - source: salt://ceph/files/ntpc.conf
    - template: jinja
    - require: 
      - pkg: ntp_pkg
    - require_in:
      - service: ntp_service

ntp_update: 
  cmd.run: 
    - name: ntpdate -d {{ ntpservers[0] }}
    - timeout: 10
    - require:
      - file: ntp_conf_setup 

ntp_service: 
  service.running: 
    - name: ntpd
    - enable: True
    - watch: 
      - file: ntp_conf_setup
    - require:
      - cmd: ntp_update 

systohc: 
  cmd.run: 
    - name: hwclock --systohc
    - timeout: 10
    - require:
      - cmd: ntp_update 
    
Asia/Shanghai:
  timezone.system:
    - name: Asia/Shanghai
    - utc: True
