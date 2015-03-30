{% import 'ceph/global_vars.jinja' as conf with context -%}
{% set psls = sls.split('.')[0] -%}

include:
  - .repo

ceph_pkg:
  pkg.installed:
    - name: ceph
    - fromrepo: ceph
    - require: 
      - pkgrepo: ceph_repo

{{ conf.conf_file }}:
  file.managed:
    - template: jinja
    - source: salt://{{ psls }}/etc/ceph/ceph.conf
    - user: root
    - group: root
    - mode: '0644'
    - require:
      - pkg: ceph_pkg
